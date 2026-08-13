#!/usr/bin/env python3
"""
Refresh — Campanha Odisseia como um todo: CRM (Insider), Ads (Meta/Google/PMax),
leads e chegada no Comercial.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Janela: campanha inteira (spend desde 03/07, venda desde 17/07) até ontem (dias completos).
Fontes: fct_transactions (vendas/atribuição por publisher+medium),
dtm_analytics_revenue_insider_funnel (CRM, tag ODI),
dtm_analytics_facebook/google/pmax_ads_funnel (ads),
dtm_analytics_lead_conversion (leads), dim_zenvia_approaches (menções do Comercial).
As queries canônicas estão em queries/*.sql — manter em sincronia.
"""

import json, subprocess, sys, datetime
from pathlib import Path

SPEND_INI = "2026-07-01"   # spend [ODI] começa 03/07
VENDA_INI = "2026-07-17"   # D1 da venda
FIM = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
OUT = Path(__file__).parent / "data.json"

ODI_PLANO = "(nm_gateway_plan='livro-odisseia-edicao-colecionador' OR LOWER(nm_gateway_product) LIKE '%odis%')"
ODI_ADS = "(UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')"

ORIGEM_CASE = """
  CASE
    WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) = 'facebook_ads' THEN 'Ads Meta'
    WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) IN ('pmax_ads','kw_google_ads','youtube_ads') THEN 'Ads Google'
    WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) = 'email' THEN 'CRM e-mail'
    WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) LIKE '%whatsapp%' THEN 'CRM WhatsApp'
    WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) IN ('app_push','in_app') THEN 'CRM push/in-app'
    WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) LIKE 'organic%' OR LOWER(COALESCE(nm_pptc_tracking_publisher,'')) = 'organic' THEN 'Orgânico'
    WHEN COALESCE(TRIM(nm_pptc_utm_medium),'') = '' THEN 'Sem UTM'
    ELSE 'Outros'
  END
"""


def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         "--project_id=bp-datawarehouse", f"--max_rows={max_rows}", sql],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    out = r.stdout.strip()
    return json.loads(out) if out else []


def fi(v):
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def ii(v):
    try: return int(float(v)) if v not in (None, "", "null") else 0
    except: return 0


Q_FUNIL_DIA = f"""
SELECT DATE(dt_ordered_at) AS dia,
       CASE WHEN bl_is_commercial_channel THEN 'comercial' ELSE 'digital' END AS canal,
       COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND {ODI_PLANO}
  AND DATE(dt_ordered_at) BETWEEN '{VENDA_INI}' AND '{FIM}'
GROUP BY 1,2 ORDER BY 1
"""

Q_ORIGEM_DIGITAL = f"""
SELECT {ORIGEM_CASE} AS origem, COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=FALSE
  AND {ODI_PLANO} AND DATE(dt_ordered_at) BETWEEN '{VENDA_INI}' AND '{FIM}'
GROUP BY 1 ORDER BY receita DESC
"""

Q_COM_ULTIMA_SESSAO = f"""
SELECT {ORIGEM_CASE} AS origem, COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND {ODI_PLANO} AND DATE(dt_ordered_at) BETWEEN '{VENDA_INI}' AND '{FIM}'
GROUP BY 1 ORDER BY receita DESC
"""

Q_CRM_DIA = f"""
SELECT dt_dispatch_date AS dia, nm_channel AS canal,
       SUM(qt_insider_delivered) AS entregues,
       SUM(qt_insider_read_or_open) AS aberturas,
       SUM(qt_insider_click) AS clicks,
       SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita
FROM datamart.dtm_analytics_revenue_insider_funnel
WHERE UPPER(nm_campaign_tag)='ODI' AND dt_dispatch_date BETWEEN '{SPEND_INI}' AND '{FIM}'
GROUP BY 1,2 ORDER BY 1
"""

Q_CRM_PECAS = f"""
SELECT nm_channel AS canal, nm_campaign AS peca,
       SUM(qt_insider_delivered) AS entregues, SUM(qt_insider_click) AS clicks,
       SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita
FROM datamart.dtm_analytics_revenue_insider_funnel
WHERE UPPER(nm_campaign_tag)='ODI' AND dt_dispatch_date BETWEEN '{SPEND_INI}' AND '{FIM}'
GROUP BY 1,2 HAVING receita > 0 ORDER BY receita DESC LIMIT 12
"""

Q_ADS_DIA = f"""
SELECT reference_date AS dia, ROUND(SUM(vl_amount_spent),0) AS spend,
       SUM(qt_impressions) AS impr, SUM(qt_outbound_clicks) AS clicks,
       SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita,
       SUM(qt_commercial_total_sales) AS vendas_com
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE {ODI_ADS} AND reference_date BETWEEN '{SPEND_INI}' AND '{FIM}'
GROUP BY 1 ORDER BY 1
"""

Q_ADS_CAMP = f"""
SELECT 'Meta' AS fonte, nm_campaign_name AS campanha, ROUND(SUM(vl_amount_spent),0) AS spend,
       SUM(qt_impressions) AS impr, SUM(qt_outbound_clicks) AS clicks,
       SUM(qt_direct_sales) AS vendas_dir, SUM(qt_commercial_total_sales) AS vendas_com,
       SUM(qt_total_sales) AS vendas, ROUND(SUM(vl_total_revenue),0) AS receita
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE {ODI_ADS} AND reference_date BETWEEN '{SPEND_INI}' AND '{FIM}'
GROUP BY 2
UNION ALL
SELECT 'Google', nm_campaign_name, ROUND(SUM(vl_amount_spent),0), SUM(qt_impressions), SUM(qt_outbound_clicks),
       SUM(qt_direct_sales), SUM(qt_commercial_total_sales), SUM(qt_total_sales), ROUND(SUM(vl_total_revenue),0)
FROM datamart.dtm_analytics_google_ads_funnel
WHERE {ODI_ADS} AND reference_date BETWEEN '{SPEND_INI}' AND '{FIM}'
GROUP BY 2
UNION ALL
SELECT 'PMax', nm_campaign_name, ROUND(SUM(vl_amount_spent),0), SUM(qt_impressions), SUM(qt_outbound_clicks),
       SUM(qt_direct_sales), SUM(qt_commercial_total_sales), SUM(qt_total_sales), ROUND(SUM(vl_total_revenue),0)
FROM datamart.dtm_analytics_pmax_ads_funnel
WHERE {ODI_ADS} AND reference_date BETWEEN '{SPEND_INI}' AND '{FIM}'
GROUP BY 2
ORDER BY spend DESC
"""

Q_LEADS = f"""
SELECT DATE(dt_registered_at_br) AS dia,
       COALESCE(NULLIF(TRIM(LOWER(utm_source)),''),'(vazio)') AS fonte, COUNT(*) AS leads
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'ODI\\]|ODISSEIA')
  AND DATE(dt_registered_at_br) <= '{FIM}'
GROUP BY 1,2 ORDER BY 1
"""

Q_MENCOES = f"""
SELECT DATE(dt_approach_start) AS dia,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')) AS mencoes
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '{VENDA_INI}' AND '{FIM}'
GROUP BY 1 ORDER BY 1
"""


def build() -> dict:
    dias_venda = []
    d = datetime.date.fromisoformat(VENDA_INI)
    while d.isoformat() <= FIM:
        dias_venda.append(d.isoformat()); d += datetime.timedelta(days=1)

    print("  funil por dia/canal...", flush=True)
    funil = {d: {"comercial": {"vendas": 0, "receita": 0.0},
                 "digital": {"vendas": 0, "receita": 0.0}} for d in dias_venda}
    for r in bq(Q_FUNIL_DIA):
        if r["dia"] in funil:
            funil[r["dia"]][r["canal"]] = {"vendas": ii(r["vendas"]), "receita": fi(r["receita"])}
    funil_dia = [{"dia": d, **funil[d]} for d in dias_venda]

    print("  origem das vendas (digital + comercial)...", flush=True)
    origem_digital = [{"origem": r["origem"], "vendas": ii(r["vendas"]), "receita": fi(r["receita"])}
                      for r in bq(Q_ORIGEM_DIGITAL)]
    com_ultima = [{"origem": r["origem"], "vendas": ii(r["vendas"]), "receita": fi(r["receita"])}
                  for r in bq(Q_COM_ULTIMA_SESSAO)]

    print("  CRM por dia/canal...", flush=True)
    crm_dia = [{"dia": r["dia"], "canal": r["canal"], "entregues": ii(r["entregues"]),
                "aberturas": ii(r["aberturas"]), "clicks": ii(r["clicks"]),
                "vendas": ii(r["vendas"]), "receita": fi(r["receita"])} for r in bq(Q_CRM_DIA)]
    crm_tot = {}
    for r in crm_dia:
        t = crm_tot.setdefault(r["canal"], {"entregues": 0, "aberturas": 0, "clicks": 0,
                                            "vendas": 0, "receita": 0.0, "pecas": 0})
        for k in ("entregues", "aberturas", "clicks", "vendas"):
            t[k] += r[k]
        t["receita"] += r["receita"]
    pecas_por_canal = bq(f"""
SELECT nm_channel AS canal, COUNT(DISTINCT nm_campaign) AS pecas
FROM datamart.dtm_analytics_revenue_insider_funnel
WHERE UPPER(nm_campaign_tag)='ODI' AND dt_dispatch_date BETWEEN '{SPEND_INI}' AND '{FIM}'
GROUP BY 1""")
    for r in pecas_por_canal:
        if r["canal"] in crm_tot:
            crm_tot[r["canal"]]["pecas"] = ii(r["pecas"])

    print("  CRM top peças...", flush=True)
    crm_pecas = [{"canal": r["canal"], "peca": r["peca"], "entregues": ii(r["entregues"]),
                  "clicks": ii(r["clicks"]), "vendas": ii(r["vendas"]), "receita": fi(r["receita"])}
                 for r in bq(Q_CRM_PECAS)]

    print("  ads por dia...", flush=True)
    ads_dia = [{"dia": r["dia"], "spend": fi(r["spend"]), "impr": ii(r["impr"]),
                "clicks": ii(r["clicks"]), "vendas": ii(r["vendas"]),
                "receita": fi(r["receita"]), "vendas_com": ii(r["vendas_com"])} for r in bq(Q_ADS_DIA)]

    print("  ads por campanha...", flush=True)
    ads_camp = [{"fonte": r["fonte"], "campanha": r["campanha"], "spend": fi(r["spend"]),
                 "impr": ii(r["impr"]), "clicks": ii(r["clicks"]),
                 "vendas_dir": ii(r["vendas_dir"]), "vendas_com": ii(r["vendas_com"]),
                 "vendas": ii(r["vendas"]), "receita": fi(r["receita"])} for r in bq(Q_ADS_CAMP)]

    print("  leads...", flush=True)
    leads_rows = bq(Q_LEADS)
    leads_dia = {}
    leads_fonte = {}
    for r in leads_rows:
        leads_dia[r["dia"]] = leads_dia.get(r["dia"], 0) + ii(r["leads"])
        leads_fonte[r["fonte"]] = leads_fonte.get(r["fonte"], 0) + ii(r["leads"])
    leads = {"por_dia": [{"dia": k, "leads": v} for k, v in sorted(leads_dia.items())],
             "por_fonte": dict(sorted(leads_fonte.items(), key=lambda kv: -kv[1])),
             "total": sum(leads_fonte.values())}

    print("  menções Zenvia...", flush=True)
    menc = {r["dia"]: ii(r["mencoes"]) for r in bq(Q_MENCOES)}
    mencoes_dia = [{"dia": d, "mencoes": menc.get(d, 0)} for d in dias_venda]

    # KPIs
    tot_v = sum(f["comercial"]["vendas"] + f["digital"]["vendas"] for f in funil_dia)
    tot_r = sum(f["comercial"]["receita"] + f["digital"]["receita"] for f in funil_dia)
    spend_total = sum(c["spend"] for c in ads_camp)
    kpis = {
        "vendas": tot_v, "receita": tot_r, "ticket": round(tot_r / tot_v) if tot_v else 0,
        "vendas_comercial": sum(f["comercial"]["vendas"] for f in funil_dia),
        "receita_comercial": sum(f["comercial"]["receita"] for f in funil_dia),
        "spend_ads": spend_total,
        "roas_blended": round(tot_r / spend_total, 2) if spend_total else None,
        "mencoes_total": sum(m["mencoes"] for m in mencoes_dia),
    }

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "config": {"spend_ini": SPEND_INI, "venda_ini": VENDA_INI, "fim": FIM},
        "kpis": kpis,
        "funil_dia": funil_dia,
        "origem_digital": origem_digital,
        "comercial_ultima_sessao": com_ultima,
        "crm": {"totais": crm_tot, "por_dia": crm_dia, "top_pecas": crm_pecas},
        "ads": {"por_dia": ads_dia, "campanhas": ads_camp},
        "leads": leads,
        "mencoes_dia": mencoes_dia,
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing odisseia-campanha data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: odisseia-campanha refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
