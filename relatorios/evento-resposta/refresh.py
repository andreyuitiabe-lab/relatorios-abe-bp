#!/usr/bin/env python3
"""
Relatório: CPL, custo/resposta e conversão — campanhas otimizadas por evento
de resposta (Lead Survey) vs demais campanhas de LEAD do Meta Ads.

Cobre os lançamentos com experimento de evento de resposta (EVG, BP10).

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

OUT = Path(__file__).parent / "data.json"

# Lançamentos que rodam a campanha "Lead Survey" (otimização por evento de resposta)
LANCAMENTOS = ["EVG", "BP10"]
# Janela da curva de aprendizado = vida das campanhas survey (começaram 19/jun/2026)
DT_SURVEY_START = "2026-06-19"
# Janela da comparação de conversão por lançamento
LOOKBACK_DAYS = 120
# Atribuição last-click: utm_content -> id_advertising.
# Captura tanto "AD## ... __<id>" quanto o id puro "<id>" (padrão do BP10).
ID_RE = r"([0-9]+)$"


# ─── BQ helper ───────────────────────────────────────────────────────────────
def bq(sql: str, max_rows: int = 5000) -> list:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         "--project_id=bp-datawarehouse", f"--max_rows={max_rows}", sql],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    out = r.stdout.strip()
    return json.loads(out) if out else []

def fi(v) -> float:
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def ii(v) -> int:
    try: return int(v) if v not in (None, "", "null") else 0
    except: return 0


# ─── queries ─────────────────────────────────────────────────────────────────
def q_serie(lanc: str) -> str:
    """Série diária de CPL, custo/resposta e CTR: survey vs base, dentro do lançamento."""
    return f"""
    WITH ad_grupo AS (
      SELECT id_advertising,
        CASE WHEN ANY_VALUE(nm_campaign_name) LIKE '%Survey%' THEN 'survey' ELSE 'base' END AS grupo
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
      WHERE nm_campaign_name LIKE '%[{lanc}]%[LEAD]%' AND reference_date >= '2026-06-01'
      GROUP BY id_advertising
    ),
    spend_daily AS (
      SELECT f.reference_date AS dia, g.grupo,
        SUM(f.vl_amount_spent) AS spent,
        SUM(f.qt_outbound_clicks) AS clicks,
        SUM(f.qt_impressions) AS impr
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel` f
      JOIN ad_grupo g USING (id_advertising)
      WHERE f.reference_date >= '{DT_SURVEY_START}'
      GROUP BY 1, 2
    ),
    leads_daily AS (
      SELECT DATE(lc.dt_registered_at_br) AS dia, g.grupo,
        COUNT(*) AS leads,
        COUNTIF(ARRAY_LENGTH(lc.arr_survey_responses) > 0) AS resp
      FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion` lc
      JOIN ad_grupo g ON g.id_advertising = REGEXP_EXTRACT(lc.utm_content, r'{ID_RE}')
      WHERE DATE(lc.dt_registered_at_br) >= '{DT_SURVEY_START}' AND lc.utm_medium = 'facebook_ads'
      GROUP BY 1, 2
    )
    SELECT CAST(dia AS STRING) AS dia, grupo,
      ROUND(spent / NULLIF(leads, 0), 2) AS cpl,
      ROUND(spent / NULLIF(resp, 0), 2) AS custo_resp,
      ROUND(clicks / NULLIF(impr, 0) * 100, 2) AS ctr
    FROM spend_daily FULL JOIN leads_daily USING (dia, grupo)
    ORDER BY dia, grupo
    """

# Reconciliação: cadastros e respostas do lançamento inteiro por nm_tag
# (todas as campanhas e todas as fontes) — é a métrica que o dashboard oficial mostra.
def q_recon() -> str:
    tags = ", ".join(f"'{l}'" for l in LANCAMENTOS)
    return f"""
    SELECT UPPER(nm_tag) AS lancamento,
      COUNT(*) AS tag_cad,
      COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) AS tag_resp,
      ROUND(COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) / COUNT(*) * 100, 1) AS tag_taxa
    FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
    WHERE dt_registered_at_br >= '{DT_SURVEY_START}' AND UPPER(nm_tag) IN ({tags})
    GROUP BY 1
    """

def q_resumo(lanc: str, excluir=None) -> str:
    """Resumo agregado dos dois grupos na vida das campanhas survey.

    excluir: lista de datas 'YYYY-MM-DD' a remover do agregado (dias anômalos de
    CTR colapsado). Aplicada tanto ao gasto (reference_date) quanto aos leads
    (dt_registered_at_br) para manter as duas pontas alinhadas na mesma janela.
    """
    ex = ", ".join(f"'{d}'" for d in (excluir or []))
    filtro_gasto = f"AND reference_date NOT IN ({ex})" if ex else ""
    filtro_lead = f"AND DATE(dt_registered_at_br) NOT IN ({ex})" if ex else ""
    return f"""
    WITH meta AS (
      SELECT id_advertising, ANY_VALUE(nm_campaign_name) AS nm_campaign_name, SUM(vl_amount_spent) AS spent
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
      WHERE reference_date >= '{DT_SURVEY_START}' {filtro_gasto} AND nm_campaign_name LIKE '%[{lanc}]%[LEAD]%'
      GROUP BY id_advertising
    ),
    leads AS (
      SELECT REGEXP_EXTRACT(utm_content, r'{ID_RE}') AS id_advertising,
        COUNT(*) AS qt_leads,
        COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) AS qt_resp,
        COUNTIF(EXISTS(SELECT 1 FROM UNNEST(arr_st_approved_transactions) t
                       WHERE t.days_to_purchase BETWEEN 0 AND 30)) AS qt_comprou
      FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
      WHERE dt_registered_at_br >= '{DT_SURVEY_START}' {filtro_lead} AND utm_medium = 'facebook_ads'
      GROUP BY 1
    )
    SELECT
      CASE WHEN m.nm_campaign_name LIKE '%Survey%' THEN 'survey' ELSE 'base' END AS grupo,
      ROUND(SUM(m.spent), 0) AS invest, SUM(l.qt_leads) AS leads,
      ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_leads), 0), 2) AS cpl,
      ROUND(SUM(l.qt_resp) / NULLIF(SUM(l.qt_leads), 0) * 100, 1) AS taxa_resp,
      ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_resp), 0), 2) AS custo_resp,
      ROUND(SUM(l.qt_comprou) / NULLIF(SUM(l.qt_leads), 0) * 100, 2) AS conv_pct
    FROM meta m LEFT JOIN leads l USING (id_advertising)
    GROUP BY 1 ORDER BY 1
    """

# Conversão lead->venda e CAC por lançamento (todas as campanhas de LEAD).
Q_CONV = f"""
WITH meta AS (
  SELECT id_advertising,
    REGEXP_EXTRACT(ANY_VALUE(nm_campaign_name), r'\\[([A-Z0-9]+)\\] \\[LEAD\\]') AS lancamento,
    SUM(vl_amount_spent) AS spent
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {LOOKBACK_DAYS} DAY)
    AND nm_campaign_name LIKE '%[LEAD]%'
  GROUP BY id_advertising
),
leads AS (
  SELECT REGEXP_EXTRACT(utm_content, r'{ID_RE}') AS id_advertising,
    COUNT(*) AS qt_leads,
    COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) AS qt_resp,
    COUNTIF(EXISTS(SELECT 1 FROM UNNEST(arr_st_approved_transactions) t
                   WHERE t.days_to_purchase BETWEEN 0 AND 30)) AS qt_comprou
  FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
  WHERE dt_registered_at_br >= DATE_SUB(CURRENT_DATE(), INTERVAL {LOOKBACK_DAYS} DAY)
    AND utm_medium = 'facebook_ads'
  GROUP BY 1
)
SELECT m.lancamento,
  ROUND(SUM(m.spent), 0) AS invest, SUM(l.qt_leads) AS leads,
  ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_leads), 0), 2) AS cpl,
  ROUND(SUM(l.qt_resp) / NULLIF(SUM(l.qt_leads), 0) * 100, 1) AS taxa_resp,
  ROUND(SUM(l.qt_comprou) / NULLIF(SUM(l.qt_leads), 0) * 100, 2) AS conv_pct,
  ROUND(SUM(m.spent) / NULLIF(SUM(l.qt_comprou), 0), 0) AS cac
FROM meta m LEFT JOIN leads l USING (id_advertising)
WHERE m.lancamento IS NOT NULL
GROUP BY 1 HAVING leads > 500 ORDER BY invest DESC
"""


# ─── build ───────────────────────────────────────────────────────────────────
def build() -> dict:
    launches = {}
    all_dias = set()
    serie_raw = {}
    for lanc in LANCAMENTOS:
        print(f"  {lanc}: série diária...", flush=True)
        serie_raw[lanc] = bq(q_serie(lanc))
        all_dias |= {r["dia"] for r in serie_raw[lanc]}

    dias = sorted(all_dias)

    def serie_grupo(rows, grupo, campo):
        m = {r["dia"]: r for r in rows if r["grupo"] == grupo}
        return [fi(m[d][campo]) if d in m and m[d].get(campo) not in (None, "") else None for d in dias]

    print("  reconciliação por nm_tag...", flush=True)
    recon = {r["lancamento"]: r for r in bq(q_recon())}

    for lanc in LANCAMENTOS:
        rows = serie_raw[lanc]
        ctr_survey = serie_grupo(rows, "survey", "ctr")
        # dias anômalos = CTR do survey desabou (< 0,5%) — falha técnica de clique/destino.
        # Excluídos do resumo agregado (inflam CPL/custo-resposta), mas mantidos na série.
        anomalias_full = [dias[i] for i, c in enumerate(ctr_survey) if c is not None and c < 0.5]
        anomalias = [d[5:] for d in anomalias_full]
        print(f"  {lanc}: resumo{(' (excl. ' + ', '.join(anomalias) + ')') if anomalias else ''}...", flush=True)
        grupos = {r["grupo"]: r for r in bq(q_resumo(lanc, excluir=anomalias_full))}
        def g(k, campo, cast=fi):
            return cast(grupos.get(k, {}).get(campo)) if k in grupos else 0
        rc = recon.get(lanc, {})
        launches[lanc] = {
            "serie": {
                "cpl_survey":   serie_grupo(rows, "survey", "cpl"),
                "cpl_base":     serie_grupo(rows, "base", "cpl"),
                "cresp_survey": serie_grupo(rows, "survey", "custo_resp"),
                "cresp_base":   serie_grupo(rows, "base", "custo_resp"),
                "ctr_survey":   ctr_survey,
            },
            "anomalias": anomalias,
            "resumo": {
                "survey": {"cpl": g("survey","cpl"), "taxa_resp": g("survey","taxa_resp"),
                           "custo_resp": g("survey","custo_resp"), "conv": g("survey","conv_pct"),
                           "invest": g("survey","invest"), "leads": g("survey","leads",ii)},
                "base":   {"cpl": g("base","cpl"), "taxa_resp": g("base","taxa_resp"),
                           "custo_resp": g("base","custo_resp"), "conv": g("base","conv_pct"),
                           "invest": g("base","invest"), "leads": g("base","leads",ii)},
            },
            "recon": {"tag_cad": ii(rc.get("tag_cad")), "tag_resp": ii(rc.get("tag_resp")),
                      "tag_taxa": fi(rc.get("tag_taxa"))},
        }

    print("  conversão por lançamento...", flush=True)
    conv = bq(Q_CONV)

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "survey_start": DT_SURVEY_START,
        "lookback_days": LOOKBACK_DAYS,
        "lancamentos": LANCAMENTOS,
        "labels": [d[5:] for d in dias],   # MM-DD
        "launches": launches,
        "conv": [
            {"lancamento": r["lancamento"], "invest": fi(r["invest"]), "leads": ii(r["leads"]),
             "cpl": fi(r["cpl"]), "taxa_resp": fi(r["taxa_resp"]),
             "conv": fi(r["conv_pct"]), "cac": fi(r["cac"])}
            for r in conv
        ],
    }


def main():
    print("Gerando data.json...", flush=True)
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"✓ {OUT} ({len(data['conv'])} lançamentos, {len(data['labels'])} dias, survey em {LANCAMENTOS})")

    if "--push" in sys.argv:
        d = OUT.parent
        for cmd in (["git", "add", "-A"],
                    ["git", "commit", "-m", "relatório evento-resposta: atualiza data.json"],
                    ["git", "push"]):
            subprocess.run(cmd, cwd=d, check=False)


if __name__ == "__main__":
    main()
