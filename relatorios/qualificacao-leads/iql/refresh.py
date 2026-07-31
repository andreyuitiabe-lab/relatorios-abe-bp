#!/usr/bin/env python3
"""
Relatório: IQL — Índice de Qualidade de Lead (monitoramento do modelo + resultados).

Puxa dos modelos dbt do IQL (fct_lead_iql / fct_iql_weights — pré-merge em
bp-staging.dbt_abe; pós-merge trocar DATASET para bp-datawarehouse.datamart) e do
spend Meta, agrega server-side e escreve data.json. Nenhum número hardcoded no
index.html, exceto o bloco BACKTEST (resultado da recalibração local).

⚠️ Pré-merge o fct_lead_iql NÃO atualiza sozinho — rodar antes, no repo bp-dbt-dw:
  dbt run --select models/marts/marketing/iql --target local --defer --state manifest --favor-state
Pós-merge o job diário (tag 11h00_utc) assume e este aviso morre.

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
TAGS = ["EVG", "BP10", "ELB26"]
TAGS_PESQUISA = "('" + "','".join(TAGS) + "')"
# filtro de campanhas Meta (nm_campaign_name carrega a sigla entre colchetes)
FILTRO_META = " OR ".join(f"CONTAINS_SUBSTR(nm_campaign_name,'[{t}]')" for t in TAGS)

# Fonte: modelos dbt do IQL. Pré-merge (MR !2426) vivem em bp-staging.dbt_abe;
# no cutover pós-merge, trocar apenas esta constante.
DATASET = "bp-staging.dbt_abe"
FCT = f"`{DATASET}.fct_lead_iql`"
PESOS = f"`{DATASET}.fct_iql_weights`"

# Faixas do scorecard v1 (5 bandas). "Qualificado" (IQL/CPLq) = A+ ∪ A — preserva a
# semântica da v0.2 (A ≈ ≥2× conversão base); para os múltiplos de valor D28
# (medidos em 3 faixas), A+∪A → nm_a, B → nm_b, C∪D → nm_c.
BANDAS_Q = "('A+','A')"
ORD_FAIXA = "CASE nm_iql_band WHEN 'A+' THEN 0 WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 ELSE 4 END"

# CPLq alvo por campanha (normativo — definido pelo negócio; a mediana é descritiva).
CPLQ_ALVO = {}  # ex.: {"BP10": 10.0}

# Fator de maturação da receita last-click: RPL(D+240) ÷ RPL(D+X), mediana de 10
# campanhas de 2025 (fonte: scratchpad/maturacao.csv; GDC excluída por degenerada).
FATOR_MATURACAO = {30: 1.90, 60: 1.43, 90: 1.25, 240: 1.0}

# Meta de retorno padrão sobre receita BRUTA last-click.
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


# Múltiplos de valor por grupo (D28, medidos em 3 faixas — ver nota em BANDAS_Q).
MULT_VALOR = {"nao_nm": 11.0, "nm_a": 3.3, "nm_b": 1.05, "nm_c": 0.83}

# Forecast por composição de clusters (D31) — parâmetros de cohorts maduras 2025.
CLUSTER_VALOR = {
    "membro_vitalicio": {"rpl": 515.71, "m30": 0.171, "m60": 0.264, "m180": 0.627},
    "membro_ativo":     {"rpl": 129.62, "m30": 0.128, "m60": 0.210, "m180": 0.550},
    "ex_membro":        {"rpl": 44.64,  "m30": 0.427, "m60": 0.550, "m180": 0.748},
    "nm_a":             {"mult": 3.3,   "m30": 0.442, "m60": 0.536, "m180": 0.770},
    "nm_b":             {"mult": 1.05,  "m30": 0.491, "m60": 0.637, "m180": 0.803},
    "nm_c":             {"mult": 0.83,  "m30": 0.449, "m60": 0.595, "m180": 0.773},
}

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


def bq(sql, max_rows=5000, tentativas=2):
    for i in range(tentativas):
        r = subprocess.run(
            ["bq", "query", "--use_legacy_sql=false", "--format=json", f"--max_rows={max_rows}", sql],
            capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(r.stdout or "[]")
        print(f"  bq falhou (tentativa {i+1}/{tentativas}): {r.stderr.strip()[-300:]}", flush=True)
    raise RuntimeError("bq query falhou após retries")


def main():
    print("cards...", flush=True)
    cards = bq(f"""
      SELECT ANY_VALUE(cd_scorecard_version) versao, COUNT(*) leads,
        COUNT(DISTINCT nm_tag) tags,
        COUNTIF(nm_iql_band IN {BANDAS_Q}) faixa_a,
        COUNTIF(nm_iql_band IN {BANDAS_Q} AND nm_status_level='nao_membro') nm_a
      FROM {FCT}""")[0]

    print("resumo por campanha...", flush=True)
    campanhas = bq(f"""
      SELECT nm_tag, COUNT(*) leads,
        COUNTIF(nm_iql_band IN {BANDAS_Q}) faixa_a,
        COUNTIF(nm_iql_band IN {BANDAS_Q} AND nm_status_level='nao_membro') nm_a,
        ROUND(COUNTIF(nm_iql_band IN {BANDAS_Q})/COUNT(*)*100, 1) iql_pct,
        COUNTIF(nm_status_level='nao_membro') nao_membros,
        COUNTIF(nm_survey_response_level = 'sim') respondentes,
        COUNTIF(qt_sales>0) convertidos,
        ROUND(COUNTIF(qt_sales>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_attributed_revenue)/COUNT(*), 2) rpl,
        ROUND(SUM(IF(nm_status_level='nao_membro', vl_attributed_revenue, 0))
          / NULLIF(COUNTIF(nm_status_level='nao_membro'), 0), 2) rpl_nm_observado,
        ROUND(AVG(IF(nm_status_level='nao_membro',
          DATE_DIFF(CURRENT_DATE('America/Sao_Paulo'), DATE(dt_registered_at_br), DAY), NULL)), 1)
          idade_media_dias,
        MIN(DATE(dt_registered_at_br)) inicio, MAX(DATE(dt_registered_at_br)) fim
      FROM {FCT}
      WHERE nm_tag IN {TAGS_PESQUISA}
      GROUP BY 1 ORDER BY fim DESC""")
    for c in campanhas:  # fator de maturação da cohort NM (interpolação da curva histórica)
        c["fator_maturacao"] = round(fator_maturacao(float(c["idade_media_dias"] or 0)), 2)

    print("compra na página de obrigado (≤30min do cadastro)...", flush=True)
    # Corte de 30min medido na distribuição cadastro→compra (bimodal: o cluster imediato
    # concentra-se em ≤30min; 30min–2h é vale). Mesmo dedup email×tag do dtm/fct.
    obrigado = bq(f"""
      WITH leads AS (
        SELECT nm_tag, dt_registered_at_br, arr_st_approved_transactions
        FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
        WHERE nm_tag IN {TAGS_PESQUISA}
        QUALIFY ROW_NUMBER() OVER (PARTITION BY nm_email, nm_tag ORDER BY dt_registered_at_br) = 1
      )
      SELECT nm_tag,
        COUNTIF(EXISTS(SELECT 1 FROM UNNEST(arr_st_approved_transactions) t
          WHERE t.vl_payment_gross IS NOT NULL
            AND DATETIME_DIFF(t.dt_ordered_at, dt_registered_at_br, MINUTE) BETWEEN 0 AND 30))
          compradores_obrigado
      FROM leads GROUP BY 1""")
    obr = {r["nm_tag"]: int(r["compradores_obrigado"]) for r in obrigado}
    for c in campanhas:
        n = obr.get(c["nm_tag"], 0)
        c["obrigado_n"] = n
        c["obrigado_pct_leads"] = round(n / int(c["leads"]) * 100, 2) if int(c["leads"]) else 0
        c["obrigado_pct_vendas"] = round(n / int(c["convertidos"]) * 100, 1) if int(c["convertidos"]) else 0

    print("faixas NM (5 bandas)...", flush=True)
    faixas = bq(f"""
      SELECT nm_tag, nm_iql_band AS faixa, COUNT(*) leads,
        COUNTIF(qt_sales>0) conv,
        ROUND(COUNTIF(qt_sales>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_attributed_revenue)/COUNT(*), 2) rpl
      FROM {FCT}
      WHERE nm_tag IN {TAGS_PESQUISA} AND nm_status_level='nao_membro'
      GROUP BY 1,2 ORDER BY 1, {ORD_FAIXA}""")

    print("bandas de score (monotonia)...", flush=True)
    bandas = bq(f"""
      SELECT nm_tag, FORMAT('%02d', RANGE_BUCKET(qt_iql_points, [-40,-32,-24,-15,-7,0,6,15])) banda,
        MIN(qt_iql_points) score_min, MAX(qt_iql_points) score_max,
        COUNT(*) leads, COUNTIF(qt_sales>0) conv,
        ROUND(COUNTIF(qt_sales>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_attributed_revenue)/COUNT(*), 2) rpl
      FROM {FCT}
      WHERE nm_tag IN {TAGS_PESQUISA} AND nm_status_level='nao_membro'
      GROUP BY 1,2 ORDER BY 1,2""")

    print("série diária por faixa...", flush=True)
    serie = bq(f"""
      WITH base AS (
        SELECT DATE(dt_registered_at_br) dia, nm_tag, nm_iql_band AS faixa, COUNT(*) leads
        FROM {FCT}
        WHERE nm_tag IN {TAGS_PESQUISA} AND dt_registered_at_br IS NOT NULL
        GROUP BY 1,2,3
      )
      SELECT dia, nm_tag, faixa, leads FROM base
      WHERE dia >= (SELECT DATE_SUB(MAX(dia), INTERVAL 60 DAY) FROM base)
      ORDER BY dia, nm_tag, faixa""")

    print("ICPs (personas NM, cascata mutuamente exclusiva)...", flush=True)
    # Reencontrado: fora da base desde a D42; o modelo v1 descontinuou o membro_oculto
    # (D41 — medido: dropar não contamina o NM), então não há mais filtro a aplicar.
    icps = bq(f"""
      WITH base AS (
        SELECT nm_tag,
          CASE
            WHEN nm_awareness_time_level IN ('6m_a_3a','mais_3a') THEN 'simpatizante_maduro'
            WHEN nm_paid_content_level = 'paga_algum' THEN 'pagante_de_conteudo'
            WHEN nm_awareness_time_level = 'primeiro_contato'
              OR nm_affinity_level = 'nunca_ouviu' THEN 'curioso_frio'
            -- fantasma: não respondeu nada e sem histórico de recadastro — silêncio total (D43)
            WHEN nm_survey_response_level = 'nao'
              AND COALESCE(nm_registration_history_level,'') != 'recadastro_quente' THEN 'fantasma'
            ELSE 'neutro'
          END persona,
          qt_sales, vl_attributed_revenue
        FROM {FCT}
        WHERE nm_tag IN {TAGS_PESQUISA} AND nm_status_level='nao_membro'
      ),
      tot AS (SELECT nm_tag, COUNT(*) n_tot, COUNTIF(qt_sales>0) c_tot FROM base GROUP BY 1)
      SELECT b.nm_tag, b.persona, COUNT(*) leads,
        ROUND(COUNT(*)/ANY_VALUE(t.n_tot)*100, 1) pct_dos_nm,
        COUNTIF(b.qt_sales>0) convertidos,
        ROUND(COUNTIF(b.qt_sales>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SAFE_DIVIDE(COUNTIF(b.qt_sales>0)/COUNT(*),
              ANY_VALUE(t.c_tot)/ANY_VALUE(t.n_tot)), 2) lift_vs_base,
        ROUND(SUM(b.vl_attributed_revenue)/COUNT(*), 2) rpl
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
          COUNTIF(nm_iql_band IN {BANDAS_Q}) qualificados,
          COUNTIF(nm_iql_band IN {BANDAS_Q} AND nm_status_level='nao_membro') nm_a,
          COUNTIF(nm_iql_band = 'B' AND nm_status_level='nao_membro') nm_b,
          COUNTIF(nm_iql_band IN ('C','D') AND nm_status_level='nao_membro') nm_c,
          COUNTIF(nm_status_level != 'nao_membro') n_nao_nm,
          COUNTIF(qt_sales>0) convertidos,
          SUM(vl_attributed_revenue) receita
        FROM {FCT}
        WHERE nm_tag IN {TAGS_PESQUISA} AND utm_content IS NOT NULL
        GROUP BY 1,2 HAVING leads >= 50 AND id_ad IS NOT NULL
      ),
      spend AS (
        SELECT CAST(id_advertising AS STRING) id_ad,
          ANY_VALUE(nm_ad_name) nm_ad, ANY_VALUE(nm_ad_set_name) nm_adset,
          ANY_VALUE(nm_campaign_name) nm_campanha, SUM(vl_amount_spent) investimento
        FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
        WHERE {FILTRO_META}
        GROUP BY 1
      )
      SELECT l.nm_tag, l.id_ad, COALESCE(s.nm_ad, l.id_ad) anuncio,
        s.nm_adset adset, s.nm_campanha campanha, l.leads,
        l.qualificados, ROUND(l.qualificados/l.leads*100,1) iql_pct,
        l.nm_a, l.nm_b, l.nm_c, l.n_nao_nm,
        l.convertidos, ROUND(l.convertidos/l.leads*100, 2) conv_pct,
        ROUND(l.receita/l.leads, 2) rpl,
        ROUND(s.investimento, 2) investimento,
        ROUND(s.investimento/l.leads, 2) cpl,
        ROUND(s.investimento/NULLIF(l.qualificados,0), 2) cplq
      FROM leads l JOIN spend s USING (id_ad)
      WHERE s.investimento > 0
      ORDER BY cplq""", max_rows=200)

    print("resultado por campanha Meta (otimizações testadas)...", flush=True)
    # Agrupa os anúncios rastreados por campanha do Meta — cada campanha carrega a
    # otimização/estratégia testada no nome. Sem piso de 50 leads por anúncio: o piso
    # vale no agregado da campanha.
    meta_campanhas = bq(f"""
      WITH leads AS (
        SELECT REGEXP_EXTRACT(utm_content, r'(\\d{{10,}})$') id_ad, nm_tag,
          COUNT(*) leads,
          COUNTIF(nm_iql_band IN {BANDAS_Q}) qualificados,
          COUNTIF(nm_iql_band IN {BANDAS_Q} AND nm_status_level='nao_membro') nm_a,
          COUNTIF(nm_iql_band = 'B' AND nm_status_level='nao_membro') nm_b,
          COUNTIF(nm_iql_band IN ('C','D') AND nm_status_level='nao_membro') nm_c,
          COUNTIF(nm_status_level != 'nao_membro') n_nao_nm,
          COUNTIF(qt_sales>0) convertidos,
          SUM(vl_attributed_revenue) receita
        FROM {FCT}
        WHERE nm_tag IN {TAGS_PESQUISA} AND utm_content IS NOT NULL
        GROUP BY 1,2 HAVING id_ad IS NOT NULL
      ),
      spend AS (
        SELECT CAST(id_advertising AS STRING) id_ad,
          ANY_VALUE(nm_campaign_name) campanha, SUM(vl_amount_spent) investimento
        FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
        WHERE {FILTRO_META}
        GROUP BY 1
      )
      SELECT l.nm_tag, s.campanha, COUNT(DISTINCT l.id_ad) anuncios,
        SUM(l.leads) leads, SUM(l.qualificados) qualificados,
        ROUND(SUM(l.qualificados)/SUM(l.leads)*100, 1) iql_pct,
        SUM(l.nm_a) nm_a, SUM(l.nm_b) nm_b, SUM(l.nm_c) nm_c, SUM(l.n_nao_nm) n_nao_nm,
        SUM(l.convertidos) convertidos,
        ROUND(SUM(l.convertidos)/SUM(l.leads)*100, 2) conv_pct,
        ROUND(SUM(l.receita)/SUM(l.leads), 2) rpl,
        ROUND(SUM(s.investimento), 2) investimento,
        ROUND(SUM(s.investimento)/SUM(l.leads), 2) cpl,
        ROUND(SUM(s.investimento)/NULLIF(SUM(l.qualificados),0), 2) cplq
      FROM leads l JOIN spend s USING (id_ad)
      WHERE s.investimento > 0
      GROUP BY 1,2 HAVING leads >= 50
      ORDER BY 1, cplq""")

    print("receita realizada por semana de vida (forecast D31)...", flush=True)
    # Receita do dtm RESTRITA à população escorada (mesmo dedup) — ver D31.
    receita_semanal = bq(f"""
      WITH leads AS (
        SELECT nm_tag, nm_email, arr_st_approved_transactions
        FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
        WHERE nm_tag IN {TAGS_PESQUISA}
        QUALIFY ROW_NUMBER() OVER (PARTITION BY nm_email, nm_tag ORDER BY dt_registered_at_br) = 1
      ),
      escorados AS (
        SELECT DISTINCT nm_tag, nm_email FROM {FCT}
        WHERE nm_tag IN {TAGS_PESQUISA}
      )
      SELECT nm_tag, DIV(GREATEST(t.days_to_purchase, 0), 7) semana,
        ROUND(SUM(t.vl_payment_gross), 2) receita
      FROM leads JOIN escorados USING (nm_tag, nm_email),
        UNNEST(arr_st_approved_transactions) t
      WHERE t.vl_payment_gross IS NOT NULL  -- há elementos do array todos-nulos (sem receita)
      GROUP BY 1, 2 ORDER BY 1, 2""")

    # ── impacto: o que move o score ─────────────────────────────────────────
    # Aliases do UNPIVOT = valores de nm_attribute em fct_iql_weights (join abaixo).
    # Pontos ficam apenas na memória deste processo (governança D20).
    UNPIVOT = """UNPIVOT(nivel FOR atributo IN (
          nm_status_level AS 'status_cadastro', nm_survey_response_level AS 'respondeu_pesquisa',
          nm_affinity_level AS 'afinidade_bp', nm_paid_content_level AS 'paga_conteudo',
          nm_awareness_time_level AS 'tempo_conhece', nm_ddd_region_level AS 'regiao_ddd',
          nm_registration_history_level AS 'historico_cadastro',
          nm_income_level AS 'renda_declarada', nm_age_level AS 'idade',
          nm_occupation_level AS 'ocupacao'))"""
    PTS = f"""pts AS (
        SELECT nm_attribute, nm_level, qt_points FROM {PESOS}
        WHERE cd_version = (SELECT ANY_VALUE(cd_scorecard_version) FROM {FCT}))"""
    NIVEIS = """nm_status_level, nm_survey_response_level, nm_affinity_level,
          nm_paid_content_level, nm_awareness_time_level, nm_ddd_region_level,
          nm_registration_history_level, nm_income_level, nm_age_level, nm_occupation_level"""

    print("impacto — mix da campanha por atributo (pontos não saem do processo)...", flush=True)
    mix_camp = bq(f"""
      WITH {PTS},
      u AS (
        SELECT nm_tag, atributo, nivel FROM (
          SELECT nm_tag, {NIVEIS}
          FROM {FCT} WHERE nm_tag IN {TAGS_PESQUISA}
        ) {UNPIVOT}
      )
      SELECT u.nm_tag, u.atributo, u.nivel, COUNT(*) n, IFNULL(ANY_VALUE(p.qt_points), 0) val
      FROM u LEFT JOIN pts p ON p.nm_attribute = u.atributo AND p.nm_level = u.nivel
      GROUP BY 1,2,3""", max_rows=3000)

    print("impacto — mix por anúncio...", flush=True)
    mix_ad = bq(f"""
      WITH {PTS},
      base AS (
        SELECT nm_tag, REGEXP_EXTRACT(utm_content, r'(\\d{{10,}})$') id_ad, {NIVEIS}
        FROM {FCT}
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
        IFNULL(ANY_VALUE(p.qt_points), 0) val
      FROM u LEFT JOIN pts p ON p.nm_attribute = u.atributo AND p.nm_level = u.nivel
      GROUP BY 1,2,3,4""", max_rows=25000)

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
      WITH t AS (SELECT nm_tag, COUNT(*) n_tot FROM {FCT}
                 WHERE nm_tag IN {TAGS_PESQUISA} GROUP BY 1)
      SELECT l.nm_tag, l.nm_status_level status, COUNT(*) leads,
        ROUND(COUNT(*)/ANY_VALUE(t.n_tot)*100, 1) pct_base,
        COUNTIF(qt_sales>0) convertidos,
        ROUND(COUNTIF(qt_sales>0)/COUNT(*)*100, 3) conv_pct,
        ROUND(SUM(vl_attributed_revenue)/COUNT(*), 2) rpl,
        ROUND(COUNTIF(nm_survey_response_level='sim')/COUNT(*)*100, 1) pct_respondeu,
        ROUND(COUNTIF(nm_paid_content_level='paga_algum')/COUNT(*)*100, 1) pct_paga,
        ROUND(COUNTIF(nm_registration_history_level='recadastro_quente')/COUNT(*)*100, 1) pct_recad_quente,
        ROUND(COUNTIF(nm_registration_history_level='frio')/COUNT(*)*100, 1) pct_recad_frio,
        ROUND(COUNTIF(nm_awareness_time_level='primeiro_contato')/COUNT(*)*100, 1) pct_tc_primeiro,
        ROUND(COUNTIF(nm_awareness_time_level='ate_6m')/COUNT(*)*100, 1) pct_tc_ate_6m,
        ROUND(COUNTIF(nm_awareness_time_level='6m_a_3a')/COUNT(*)*100, 1) pct_tc_6m_3a,
        ROUND(COUNTIF(nm_awareness_time_level='mais_3a')/COUNT(*)*100, 1) pct_tc_mais_3a,
        ROUND(COUNTIF(nm_ddd_region_level='alto')/COUNT(*)*100, 1) pct_reg_alto,
        ROUND(COUNTIF(nm_ddd_region_level='medio_alto')/COUNT(*)*100, 1) pct_reg_medio_alto,
        ROUND(COUNTIF(nm_ddd_region_level='medio')/COUNT(*)*100, 1) pct_reg_medio,
        ROUND(COUNTIF(nm_ddd_region_level='baixo')/COUNT(*)*100, 1) pct_reg_baixo
      FROM {FCT} l JOIN t USING (nm_tag)
      WHERE l.nm_tag IN {TAGS_PESQUISA}
      GROUP BY 1,2 ORDER BY 1, leads DESC""")

    print("perfil por anúncio (mix de status e personas)...", flush=True)
    perfil_anuncios = bq(f"""
      WITH base AS (
        SELECT nm_tag, REGEXP_EXTRACT(utm_content, r'(\\d{{10,}})$') id_ad, nm_status_level,
          CASE
            WHEN nm_status_level != 'nao_membro' THEN NULL
            WHEN nm_awareness_time_level IN ('6m_a_3a','mais_3a') THEN 'simpatizante_maduro'
            WHEN nm_paid_content_level = 'paga_algum' THEN 'pagante_de_conteudo'
            WHEN nm_awareness_time_level = 'primeiro_contato'
              OR nm_affinity_level = 'nunca_ouviu' THEN 'curioso_frio'
            WHEN nm_survey_response_level = 'nao'
              AND COALESCE(nm_registration_history_level,'') != 'recadastro_quente' THEN 'fantasma'
            ELSE 'neutro'
          END persona
        FROM {FCT}
        WHERE nm_tag IN {TAGS_PESQUISA} AND utm_content IS NOT NULL
      )
      SELECT nm_tag, id_ad, COUNT(*) leads,
        COUNTIF(nm_status_level='nao_membro') nm_leads,
        ROUND(COUNTIF(nm_status_level='nao_membro')/COUNT(*)*100, 1) pct_nao_membro,
        ROUND(COUNTIF(nm_status_level='membro_ativo')/COUNT(*)*100, 1) pct_membro_ativo,
        ROUND(COUNTIF(nm_status_level='ex_membro')/COUNT(*)*100, 1) pct_ex_membro,
        ROUND(COUNTIF(nm_status_level='membro_vitalicio')/COUNT(*)*100, 1) pct_vitalicio,
        ROUND(COUNTIF(persona='simpatizante_maduro')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_simpatizante,
        ROUND(COUNTIF(persona='pagante_de_conteudo')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_pagante,
        ROUND(COUNTIF(persona='curioso_frio')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_frio,
        ROUND(COUNTIF(persona='fantasma')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_fantasma,
        ROUND(COUNTIF(persona='neutro')/NULLIF(COUNTIF(persona IS NOT NULL),0)*100, 1) pct_p_neutro
      FROM base
      WHERE id_ad IS NOT NULL
      GROUP BY 1,2 HAVING leads >= 50
      ORDER BY 1, leads DESC""", max_rows=500)

    data = {
        "atualizado": datetime.date.today().isoformat(),
        "cplq_alvo": CPLQ_ALVO,
        "meta_roas": META_ROAS,
        "mult_valor": MULT_VALOR,
        "cluster_valor": CLUSTER_VALOR,
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
        "meta_campanhas": meta_campanhas,
        "receita_semanal": receita_semanal,
    }
    blob = json.dumps(data, ensure_ascii=False, indent=1)
    # assert de governança: nenhuma CHAVE de pontos/pesos (nem proxies) no arquivo público
    for proibido in ('"qt_pontos"', '"qt_points"', '"pontos"', '"pts"', '"val"', '"woe"',
                     '"iv_contrib"', '"media_pts"', '"desvio"'):
        assert (proibido + ":") not in blob, f"governança: chave {proibido} vazaria para o data.json"
    OUT.write_text(blob)
    print(f"ok → {OUT}")


if __name__ == "__main__":
    main()
