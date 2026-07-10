#!/usr/bin/env python3
"""
Relatório: IQL — Índice de Qualidade de Lead (monitoramento do modelo + resultados).

Puxa de bp-staging.dbt_abe (tb_lead_iql, tb_iql_iv_perguntas) e do spend Meta,
agrega server-side e escreve data.json. Nenhum número hardcoded no index.html,
exceto o bloco BACKTEST (resultado da recalibração local — atualizar a cada versão).

⚠️ Não expor pesos do scorecard aqui (repo público) — apenas faixas, IV e agregados.

Uso: python3 refresh.py
"""
import datetime
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).parent / "data.json"
TAGS_PESQUISA = "('EVG','BP10')"

# CPLq alvo por campanha (normativo — definido pelo negócio; a mediana é descritiva).
# Vazio até o negócio definir; quando definido, vira o default da reta de alvo no
# quadrante (o usuário pode sobrescrever localmente via input, persiste no browser).
CPLQ_ALVO = {}  # ex.: {"BP10": 10.0}

# Fator de maturação da receita last-click: RPL(D+240) ÷ RPL(D+X), mediana de 10
# campanhas de 2025 (fonte: scratchpad/maturacao.csv; GDC excluída por degenerada).
# Validado contra o CSV: medianas 1,90 / 1,43 / 1,25; faixa p25–p75 em D+30: 1,66–2,36.
# Interpolação linear entre os pontos; idade <30d usa o fator de 30d (conservador).
FATOR_MATURACAO = {30: 1.90, 60: 1.43, 90: 1.25, 240: 1.0}

# Meta de retorno padrão sobre receita BRUTA last-click (folga para margem e
# incrementalidade). Editável na UI por campanha (localStorage), como o CPLq alvo.
META_ROAS = 1.5


def fator_maturacao(idade_dias):
    pts = sorted(FATOR_MATURACAO.items())
    if idade_dias <= pts[0][0]:
        return pts[0][1]
    if idade_dias >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= idade_dias <= x1:
            return y0 + (y1 - y0) * (idade_dias - x0) / (x1 - x0)


# Resultado da recalibração v0.2 (iql_recalibra.py, 2026-07-07) — treino EVG, teste BP10
BACKTEST = {
    "descricao": "Treinado no EVG, testado no BP10 (campanha nunca vista — out-of-time e out-of-campaign)",
    "linhas": [
        {"modelo": "v0.1 (pontos univariados)", "auc_nm": 0.618, "top_decil_captura": 20.4, "lift": 2.04},
        {"modelo": "v0.2 (WOE + regressão)", "auc_nm": 0.750, "top_decil_captura": 32.4, "lift": 3.24},
        {"modelo": "v0.2 sem relacao_bp (formulário futuro)", "auc_nm": 0.746, "top_decil_captura": 31.0, "lift": 3.10},
    ],
    "ressalva": ("Parte do ganho no BP10 vem da pergunta tempo_conhece, que nessa campanha tem IV "
                 "anormalmente alto (0,93 — flag de investigação). Os pesos vieram do EVG (sem vazamento "
                 "de treino), mas o nº pode estar otimista para campanha típica."),
}


def bq(sql, max_rows=5000):
    r = subprocess.run(
        ["bq", "query", "--use_legacy_sql=false", "--format=json", f"--max_rows={max_rows}", sql],
        capture_output=True, text=True, check=True)
    return json.loads(r.stdout or "[]")


def main():
    print("cards...", flush=True)
    cards = bq(f"""
      SELECT ANY_VALUE(versao_scorecard) versao, COUNT(*) leads,
        COUNT(DISTINCT nm_tag) tags,
        COUNTIF(nm_faixa_iql='A') faixa_a,
        COUNTIF(nm_faixa_iql='A' AND nivel_status='nao_membro') nm_a
      FROM `bp-staging.dbt_abe.tb_lead_iql`""")[0]

    print("resumo por campanha...", flush=True)
    campanhas = bq(f"""
      SELECT nm_tag, COUNT(*) leads,
        COUNTIF(nm_faixa_iql='A') faixa_a,
        COUNTIF(nm_faixa_iql='A' AND nivel_status='nao_membro') nm_a,
        ROUND(COUNTIF(nm_faixa_iql='A')/COUNT(*)*100, 1) iql_pct,
        COUNTIF(nivel_status='nao_membro') nao_membros,
        COUNTIF(nivel_respondeu = 'sim') respondentes,
        COUNTIF(qt_vendas>0) convertidos,
        ROUND(COUNTIF(qt_vendas>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_receita_atribuida)/COUNT(*), 2) rpl,
        ROUND(AVG(IF(nivel_status='nao_membro',
          DATE_DIFF(CURRENT_DATE('America/Sao_Paulo'), DATE(dt_registered_at_br), DAY), NULL)), 1)
          idade_media_dias,
        MIN(DATE(dt_registered_at_br)) inicio, MAX(DATE(dt_registered_at_br)) fim
      FROM `bp-staging.dbt_abe.tb_lead_iql`
      WHERE nm_tag IN {TAGS_PESQUISA}
      GROUP BY 1 ORDER BY fim DESC""")
    for c in campanhas:  # fator de maturação da cohort NM (interpolação da curva histórica)
        c["fator_maturacao"] = round(fator_maturacao(float(c["idade_media_dias"] or 0)), 2)

    print("faixas NM (campanhas com pesquisa)...", flush=True)
    faixas = bq(f"""
      SELECT nm_tag, nm_faixa_iql AS faixa, COUNT(*) leads,
        COUNTIF(qt_vendas>0) conv,
        ROUND(COUNTIF(qt_vendas>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_receita_atribuida)/COUNT(*), 2) rpl
      FROM `bp-staging.dbt_abe.tb_lead_iql`
      WHERE nm_tag IN {TAGS_PESQUISA} AND nivel_status='nao_membro'
      GROUP BY 1,2 ORDER BY 1,2""")

    print("bandas de score (monotonia)...", flush=True)
    bandas = bq(f"""
      SELECT nm_tag, FORMAT('%02d', RANGE_BUCKET(qt_pontos_iql, [-40,-25,-15,-5,4,15])) banda,
        MIN(qt_pontos_iql) score_min, MAX(qt_pontos_iql) score_max,
        COUNT(*) leads, COUNTIF(qt_vendas>0) conv,
        ROUND(COUNTIF(qt_vendas>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_receita_atribuida)/COUNT(*), 2) rpl
      FROM `bp-staging.dbt_abe.tb_lead_iql`
      WHERE nm_tag IN {TAGS_PESQUISA} AND nivel_status='nao_membro'
      GROUP BY 1,2 ORDER BY 1,2""")

    print("série diária por faixa...", flush=True)
    serie = bq(f"""
      WITH base AS (
        SELECT DATE(dt_registered_at_br) dia, nm_tag, nm_faixa_iql AS faixa, COUNT(*) leads
        FROM `bp-staging.dbt_abe.tb_lead_iql`
        WHERE nm_tag IN {TAGS_PESQUISA} AND dt_registered_at_br IS NOT NULL
        GROUP BY 1,2,3
      )
      SELECT dia, nm_tag, faixa, leads FROM base
      WHERE dia >= (SELECT DATE_SUB(MAX(dia), INTERVAL 60 DAY) FROM base)
      ORDER BY dia, nm_tag, faixa""")

    print("ICPs (personas NM, cascata mutuamente exclusiva)...", flush=True)
    icps = bq(f"""
      WITH base AS (
        SELECT nm_tag,
          CASE
            WHEN nivel_status_pessoa = 'membro_oculto' THEN 'reencontrado'
            WHEN nivel_tempo_conhece IN ('6m_a_3a','mais_3a') THEN 'simpatizante_maduro'
            WHEN nivel_paga = 'paga_algum' THEN 'pagante_de_conteudo'
            WHEN nivel_tempo_conhece = 'primeiro_contato'
              OR nivel_afinidade = 'nunca_ouviu' THEN 'curioso_frio'
            ELSE 'neutro'
          END persona,
          qt_vendas, vl_receita_atribuida
        FROM `bp-staging.dbt_abe.tb_lead_iql`
        WHERE nm_tag IN {TAGS_PESQUISA} AND nivel_status='nao_membro'
      ),
      tot AS (SELECT nm_tag, COUNT(*) n_tot, COUNTIF(qt_vendas>0) c_tot FROM base GROUP BY 1)
      SELECT b.nm_tag, b.persona, COUNT(*) leads,
        ROUND(COUNT(*)/ANY_VALUE(t.n_tot)*100, 1) pct_dos_nm,
        COUNTIF(b.qt_vendas>0) convertidos,
        ROUND(COUNTIF(b.qt_vendas>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SAFE_DIVIDE(COUNTIF(b.qt_vendas>0)/COUNT(*),
              ANY_VALUE(t.c_tot)/ANY_VALUE(t.n_tot)), 2) lift_vs_base,
        ROUND(SUM(b.vl_receita_atribuida)/COUNT(*), 2) rpl
      FROM base b JOIN tot t USING (nm_tag)
      GROUP BY 1,2 ORDER BY 1,2""")

    print("respostas por pergunta (sem woe/iv_contrib — repo público)...", flush=True)
    perguntas = bq(f"""
      SELECT nm_tag, nm_pergunta, nm_resposta, n, convertidos, conv_pct,
        rpl, lift_vs_base_tag
      FROM `bp-staging.dbt_abe.tb_iql_woe_respostas`
      WHERE nm_tag IN {TAGS_PESQUISA}
      ORDER BY nm_tag, nm_pergunta, n DESC""")

    print("leaderboard IV...", flush=True)
    iv = bq(f"""
      SELECT nm_tag, nm_pergunta, cobertura_pct, iv_total, iv_respondentes, ds_recomendacao
      FROM `bp-staging.dbt_abe.tb_iql_iv_perguntas`
      WHERE nm_tag IN {TAGS_PESQUISA}
      ORDER BY nm_tag, iv_total DESC""")

    print("anúncios (IQL + CPLq)...", flush=True)
    anuncios = bq(f"""
      WITH leads AS (
        -- id do anúncio: EVG usa 'nome__<id>', BP10 usa o id puro → dígitos longos no fim
        SELECT REGEXP_EXTRACT(utm_content, r'(\\d{{10,}})$') id_ad, nm_tag,
          COUNT(*) leads,
          COUNTIF(nm_faixa_iql='A') qualificados,
          COUNTIF(nm_faixa_iql='A' AND nivel_status='nao_membro') nm_a,
          COUNTIF(qt_vendas>0) convertidos,
          SUM(vl_receita_atribuida) receita
        FROM `bp-staging.dbt_abe.tb_lead_iql`
        WHERE nm_tag IN {TAGS_PESQUISA} AND utm_content IS NOT NULL
        GROUP BY 1,2 HAVING leads >= 50 AND id_ad IS NOT NULL
      ),
      spend AS (
        SELECT CAST(id_advertising AS STRING) id_ad,
          ANY_VALUE(nm_ad_name) nm_ad, SUM(vl_amount_spent) investimento
        FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
        WHERE CONTAINS_SUBSTR(nm_campaign_name,'[EVG]') OR CONTAINS_SUBSTR(nm_campaign_name,'[BP10]')
        GROUP BY 1
      )
      SELECT l.nm_tag, l.id_ad, COALESCE(s.nm_ad, l.id_ad) anuncio, l.leads,
        l.qualificados, ROUND(l.qualificados/l.leads*100,1) iql_pct, l.nm_a,
        l.convertidos, ROUND(l.convertidos/l.leads*100, 2) conv_pct,
        ROUND(l.receita/l.leads, 2) rpl,
        ROUND(s.investimento, 2) investimento,
        ROUND(s.investimento/l.leads, 2) cpl,
        ROUND(s.investimento/NULLIF(l.qualificados,0), 2) cplq
      FROM leads l JOIN spend s USING (id_ad)
      WHERE s.investimento > 0
      ORDER BY cplq""", max_rows=200)

    # ── impacto: o que move o score ─────────────────────────────────────────
    # O SQL devolve contagens por nível JUNTO com os pontos; os pontos ficam
    # apenas na memória deste processo. No data.json entram só share_pct
    # relativo (normalizado, sem escala) e fatos de mix (% de público).
    UNPIVOT = """UNPIVOT(nivel FOR atributo IN (
          nivel_status AS 'status_cadastro', nivel_status_pessoa AS 'status_pessoa',
          nivel_respondeu AS 'respondeu_pesquisa', nivel_afinidade AS 'afinidade_bp',
          nivel_paga AS 'paga_conteudo', nivel_tempo_conhece AS 'tempo_conhece',
          nivel_regiao_ddd AS 'regiao_ddd', nivel_historico AS 'historico_cadastro'))"""
    PTS = """pts AS (
        SELECT nm_atributo, nm_nivel, qt_pontos FROM `bp-staging.dbt_abe.tb_iql_pontos`
        WHERE versao = (SELECT ANY_VALUE(versao_scorecard) FROM `bp-staging.dbt_abe.tb_lead_iql`))"""
    NIVEIS = """nivel_status, nivel_status_pessoa, nivel_respondeu, nivel_afinidade,
          nivel_paga, nivel_tempo_conhece, nivel_regiao_ddd, nivel_historico"""

    print("impacto — mix da campanha por atributo (pontos não saem do processo)...", flush=True)
    mix_camp = bq(f"""
      WITH {PTS},
      u AS (
        SELECT nm_tag, atributo, nivel FROM (
          SELECT nm_tag, {NIVEIS}
          FROM `bp-staging.dbt_abe.tb_lead_iql` WHERE nm_tag IN {TAGS_PESQUISA}
        ) {UNPIVOT}
      )
      SELECT u.nm_tag, u.atributo, u.nivel, COUNT(*) n, IFNULL(ANY_VALUE(p.qt_pontos), 0) val
      FROM u LEFT JOIN pts p ON p.nm_atributo = u.atributo AND p.nm_nivel = u.nivel
      GROUP BY 1,2,3""", max_rows=2000)

    print("impacto — mix por anúncio...", flush=True)
    mix_ad = bq(f"""
      WITH {PTS},
      base AS (
        SELECT nm_tag, REGEXP_EXTRACT(utm_content, r'(\\d{{10,}})$') id_ad, {NIVEIS}
        FROM `bp-staging.dbt_abe.tb_lead_iql`
        WHERE nm_tag IN {TAGS_PESQUISA} AND utm_content IS NOT NULL
      ),
      ok_ads AS (
        SELECT nm_tag, id_ad FROM base WHERE id_ad IS NOT NULL
        GROUP BY 1,2 HAVING COUNT(*) >= 50
      ),
      u AS (
        SELECT nm_tag, id_ad, atributo, nivel
        FROM (SELECT b.* FROM base b JOIN ok_ads USING (nm_tag, id_ad)) {UNPIVOT}
      )
      SELECT u.nm_tag, u.id_ad, u.atributo, u.nivel, COUNT(*) n,
        IFNULL(ANY_VALUE(p.qt_pontos), 0) val
      FROM u LEFT JOIN pts p ON p.nm_atributo = u.atributo AND p.nm_nivel = u.nivel
      GROUP BY 1,2,3,4""", max_rows=20000)

    # transformação de governança: valores crus → share_pct relativo + fato de mix
    camp = defaultdict(lambda: defaultdict(lambda: {"tot": 0, "s": 0.0, "s2": 0.0, "mix": {}}))
    for r in mix_camp:
        a = camp[r["nm_tag"]][r["atributo"]]
        n, p = int(r["n"]), float(r["val"])
        a["tot"] += n; a["s"] += n * p; a["s2"] += n * p * p
        a["mix"][r["nivel"]] = a["mix"].get(r["nivel"], 0) + n

    imp_atributos, camp_mean, camp_mix = [], {}, {}
    for tag, attrs in camp.items():
        desv = {}
        for attr, a in attrs.items():
            mean = a["s"] / a["tot"]
            desv[attr] = math.sqrt(max(a["s2"] / a["tot"] - mean * mean, 0))
            camp_mean[(tag, attr)] = mean
            for nivel, n in a["mix"].items():
                camp_mix[(tag, attr, nivel)] = n / a["tot"]
        den = sum(desv.values()) or 1.0
        for attr, sd in sorted(desv.items(), key=lambda kv: -kv[1]):
            imp_atributos.append({"nm_tag": tag, "atributo": attr,
                                  "share_pct": round(sd / den * 100, 1)})

    ads_acc = defaultdict(lambda: defaultdict(lambda: {"tot": 0, "s": 0.0, "mix": {}}))
    for r in mix_ad:
        a = ads_acc[(r["nm_tag"], r["id_ad"])][r["atributo"]]
        n, p = int(r["n"]), float(r["val"])
        a["tot"] += n; a["s"] += n * p
        a["mix"][r["nivel"]] = a["mix"].get(r["nivel"], 0) + n

    imp_anuncios = []
    for (tag, id_ad), attrs in ads_acc.items():
        deltas = {attr: a["s"] / a["tot"] - camp_mean[(tag, attr)] for attr, a in attrs.items()}
        total_desvio = sum(abs(v) for v in deltas.values())  # em pontos — NÃO publicar
        den = total_desvio or 1.0
        # anúncio "típico": desvio total minúsculo → shares de % explodem sem significado
        bl_tipico = total_desvio < 2.0
        for attr, a in attrs.items():
            # fato de mix público: nível cuja fatia mais destoa da campanha (p.p.)
            nivel, n_niv = max(
                a["mix"].items(),
                key=lambda kv: abs(kv[1] / a["tot"] - camp_mix.get((tag, attr, kv[0]), 0)))
            imp_anuncios.append({
                "nm_tag": tag, "id_ad": id_ad, "atributo": attr,
                "bl_tipico": bl_tipico,
                "share_pct": round(deltas[attr] / den * 100, 1),
                "nivel": nivel,
                "pct_ad": round(n_niv / a["tot"] * 100, 1),
                "pct_camp": round(camp_mix.get((tag, attr, nivel), 0) * 100, 1),
            })
    impacto = {"atributos": imp_atributos, "anuncios": imp_anuncios}

    print("perfil por status (traços públicos de mix)...", flush=True)
    perfil_status = bq(f"""
      WITH t AS (SELECT nm_tag, COUNT(*) n_tot FROM `bp-staging.dbt_abe.tb_lead_iql`
                 WHERE nm_tag IN {TAGS_PESQUISA} GROUP BY 1)
      SELECT l.nm_tag, l.nivel_status status, COUNT(*) leads,
        ROUND(COUNT(*)/ANY_VALUE(t.n_tot)*100, 1) pct_base,
        COUNTIF(qt_vendas>0) convertidos,
        ROUND(COUNTIF(qt_vendas>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_receita_atribuida)/COUNT(*), 2) rpl,
        ROUND(COUNTIF(nivel_respondeu='sim')/COUNT(*)*100, 1) pct_respondeu,
        ROUND(COUNTIF(nivel_paga='paga_algum')/COUNT(*)*100, 1) pct_paga,
        ROUND(COUNTIF(nivel_historico='recadastro_quente')/COUNT(*)*100, 1) pct_recad_quente,
        ROUND(COUNTIF(nivel_historico='frio')/COUNT(*)*100, 1) pct_recad_frio,
        ROUND(COUNTIF(nivel_tempo_conhece='primeiro_contato')/COUNT(*)*100, 1) pct_tc_primeiro,
        ROUND(COUNTIF(nivel_tempo_conhece='ate_6m')/COUNT(*)*100, 1) pct_tc_ate_6m,
        ROUND(COUNTIF(nivel_tempo_conhece='6m_a_3a')/COUNT(*)*100, 1) pct_tc_6m_3a,
        ROUND(COUNTIF(nivel_tempo_conhece='mais_3a')/COUNT(*)*100, 1) pct_tc_mais_3a,
        ROUND(COUNTIF(nivel_regiao_ddd='alto')/COUNT(*)*100, 1) pct_reg_alto,
        ROUND(COUNTIF(nivel_regiao_ddd='medio_alto')/COUNT(*)*100, 1) pct_reg_medio_alto,
        ROUND(COUNTIF(nivel_regiao_ddd='medio')/COUNT(*)*100, 1) pct_reg_medio,
        ROUND(COUNTIF(nivel_regiao_ddd='baixo')/COUNT(*)*100, 1) pct_reg_baixo
      FROM `bp-staging.dbt_abe.tb_lead_iql` l JOIN t USING (nm_tag)
      WHERE l.nm_tag IN {TAGS_PESQUISA}
      GROUP BY 1,2 ORDER BY 1, leads DESC""")

    print("perfil por anúncio (mix de status e personas)...", flush=True)
    perfil_anuncios = bq(f"""
      WITH base AS (
        SELECT nm_tag, REGEXP_EXTRACT(utm_content, r'(\\d{{10,}})$') id_ad, nivel_status,
          CASE
            WHEN nivel_status != 'nao_membro' THEN NULL
            WHEN nivel_status_pessoa = 'membro_oculto' THEN 'reencontrado'
            WHEN nivel_tempo_conhece IN ('6m_a_3a','mais_3a') THEN 'simpatizante_maduro'
            WHEN nivel_paga = 'paga_algum' THEN 'pagante_de_conteudo'
            WHEN nivel_tempo_conhece = 'primeiro_contato'
              OR nivel_afinidade = 'nunca_ouviu' THEN 'curioso_frio'
            ELSE 'neutro'
          END persona
        FROM `bp-staging.dbt_abe.tb_lead_iql`
        WHERE nm_tag IN {TAGS_PESQUISA} AND utm_content IS NOT NULL
      )
      SELECT nm_tag, id_ad, COUNT(*) leads,
        COUNTIF(nivel_status='nao_membro') nm_leads,
        ROUND(COUNTIF(nivel_status='nao_membro')/COUNT(*)*100, 1) pct_nao_membro,
        ROUND(COUNTIF(nivel_status='membro_ativo')/COUNT(*)*100, 1) pct_membro_ativo,
        ROUND(COUNTIF(nivel_status='ex_membro')/COUNT(*)*100, 1) pct_ex_membro,
        ROUND(COUNTIF(nivel_status='membro_vitalicio')/COUNT(*)*100, 1) pct_vitalicio,
        ROUND(COUNTIF(persona='reencontrado')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_reencontrado,
        ROUND(COUNTIF(persona='simpatizante_maduro')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_simpatizante,
        ROUND(COUNTIF(persona='pagante_de_conteudo')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_pagante,
        ROUND(COUNTIF(persona='curioso_frio')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_frio,
        ROUND(COUNTIF(persona='neutro')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_neutro
      FROM base
      WHERE id_ad IS NOT NULL
      GROUP BY 1,2 HAVING leads >= 50
      ORDER BY 1, leads DESC""", max_rows=500)

    data = {
        "atualizado": datetime.date.today().isoformat(),
        "cplq_alvo": CPLQ_ALVO,
        "meta_roas": META_ROAS,
        "cards": cards,
        "backtest": BACKTEST,
        "campanhas": campanhas,
        "faixas": faixas,
        "bandas": bandas,
        "serie": serie,
        "iv": iv,
        "icps": icps,
        "perguntas": perguntas,
        "impacto": impacto,
        "perfil_status": perfil_status,
        "perfil_anuncios": perfil_anuncios,
        "anuncios": anuncios,
    }
    blob = json.dumps(data, ensure_ascii=False, indent=1)
    # assert de governança: nenhuma CHAVE de pontos/pesos (nem proxies) no arquivo público
    for proibido in ('"qt_pontos"', '"pontos"', '"pts"', '"val"', '"woe"',
                     '"iv_contrib"', '"media_pts"', '"desvio"'):
        assert (proibido + ":") not in blob, f"governança: chave {proibido} vazaria para o data.json"
    OUT.write_text(blob)
    print(f"ok → {OUT}")


if __name__ == "__main__":
    main()
