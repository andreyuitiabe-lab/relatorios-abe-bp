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
import subprocess
from pathlib import Path

OUT = Path(__file__).parent / "data.json"
TAGS_PESQUISA = "('EVG','BP10')"

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
        MIN(DATE(dt_registered_at_br)) inicio, MAX(DATE(dt_registered_at_br)) fim
      FROM `bp-staging.dbt_abe.tb_lead_iql`
      WHERE nm_tag IN {TAGS_PESQUISA}
      GROUP BY 1 ORDER BY fim DESC""")

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
      SELECT l.nm_tag, COALESCE(s.nm_ad, l.id_ad) anuncio, l.leads,
        l.qualificados, ROUND(l.qualificados/l.leads*100,1) iql_pct, l.nm_a,
        l.convertidos, ROUND(l.convertidos/l.leads*100, 2) conv_pct,
        ROUND(l.receita/l.leads, 2) rpl,
        ROUND(s.investimento, 2) investimento,
        ROUND(s.investimento/l.leads, 2) cpl,
        ROUND(s.investimento/NULLIF(l.qualificados,0), 2) cplq
      FROM leads l JOIN spend s USING (id_ad)
      WHERE s.investimento > 0
      ORDER BY cplq""", max_rows=200)

    data = {
        "atualizado": datetime.date.today().isoformat(),
        "cards": cards,
        "backtest": BACKTEST,
        "campanhas": campanhas,
        "faixas": faixas,
        "bandas": bandas,
        "serie": serie,
        "iv": iv,
        "perguntas": perguntas,
        "anuncios": anuncios,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"ok → {OUT}")


if __name__ == "__main__":
    main()
