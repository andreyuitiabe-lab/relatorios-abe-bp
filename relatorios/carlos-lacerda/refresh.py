#!/usr/bin/env python3
"""
Carlos Lacerda (LAC) x Eneas (ENE) — primeiros dias de veiculacao.

Uso:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Fontes: BigQuery (Meta Ads, Insider, transacoes, leads) + GA4 (visitas de LP).
BQ roda pelo cliente Python com ADC (mesma credencial do bqq — o bq CLI expira).
GA4 reaproveita o token OAuth do MCP local em ~/meu_projeto/BigQuery/mcp-ga4.
"""

import json, subprocess, sys, datetime
from pathlib import Path

from google.cloud import bigquery

OUT = Path(__file__).parent / "data.json"
PROJECT = "bp-datawarehouse"

# D1 = primeiro dia com entrega registrada. D4 da LAC = dia corrente do pedido.
JANELAS = {
    "ENE": {"d1": "2026-07-28", "d3": "2026-07-30", "d4": "2026-07-31", "nome": "Enéas"},
    "LAC": {"d1": "2026-09-19", "d3": "2026-09-21", "d4": "2026-09-22", "nome": "Carlos Lacerda"},
}
GA4_PROPERTY = "378996649"
LP = {  # pagePath -> (sigla, tipo)
    "/seja-membro/filmes/eneas":         ("ENE", "venda"),
    "/cadastro-eneas/a":                 ("ENE", "cadastro"),
    "/cadastro-eneas/b":                 ("ENE", "cadastro"),
    "/seja-membro/filmes/carlos-lacerda": ("LAC", "venda"),
}

QUERIES = Path(__file__).parent / "queries"


def bq(sql: str) -> list[dict]:
    rows = bigquery.Client(project=PROJECT).query(sql).result()
    return [dict(r) for r in rows]


def q(nome: str) -> list[dict]:
    return bq((QUERIES / nome).read_text())


def jsonable(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()[:10]
    if v is None:
        return None
    if isinstance(v, (int, float, str, bool)):
        return v
    return float(v)


def clean(rows: list[dict]) -> list[dict]:
    return [{k: jsonable(v) for k, v in r.items()} for r in rows]


GA4_VENV = Path.home() / "meu_projeto/BigQuery/mcp-ga4/.venv/bin/python"


def ga4_lp() -> list[dict]:
    """Visitas de LP por dia. Roda ga4_lp.py na venv do MCP GA4 (onde vive o token)."""
    r = subprocess.run(
        [str(GA4_VENV), str(Path(__file__).parent / "ga4_lp.py"),
         json.dumps(JANELAS), json.dumps(LP), GA4_PROPERTY],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"GA4 falhou: {r.stderr.strip()[-500:]}")
    return json.loads(r.stdout)


Q_CRM = """
-- Disparos de CRM por canal/dia. A dtm agregada so enxerga a peca com nm_campaign_tag;
-- na ENE o CRM dos primeiros dias foi jornada 1:1, marcada so em nm_journey_name.
SELECT
  IF(REGEXP_CONTAINS(LOWER(COALESCE(nm_campaign,'') || '|' || COALESCE(nm_journey_name,'') || '|' ||
                           COALESCE(nm_journey_campaign_name,'')), r'\\[lac\\]'), 'LAC', 'ENE') AS sigla,
  DATE(dt_event_created_at) AS dt,
  CASE
    WHEN nm_event LIKE 'email%'    THEN 'email'
    WHEN nm_event LIKE 'whatsapp%' THEN 'whatsapp'
    ELSE 'app_push'
  END AS canal,
  COUNTIF(nm_event IN ('email_delivered', 'whatsapp_delivered', 'push_delivered')) AS qt_entregues,
  COUNTIF(nm_event IN ('email_click', 'whatsapp_click')) AS qt_cliques,
  -- abertura humana: email_open cru inclui abertura de maquina (Apple MPP)
  COUNTIF(nm_event = 'email_open' AND bl_human_open = 1) AS qt_aberturas
FROM `bp-datawarehouse.staging.stg_insider__events`
-- cada sigla so na SUA janela: a ENE segue ativa em set/2026 e vazaria para o lado da LAC
WHERE ((dt_bp_imported_at BETWEEN '2026-07-27' AND '2026-08-02'
        AND DATE(dt_event_created_at) BETWEEN '2026-07-28' AND '2026-07-31'
        AND REGEXP_CONTAINS(LOWER(COALESCE(nm_campaign,'') || '|' || COALESCE(nm_journey_name,'') || '|' ||
                                  COALESCE(nm_journey_campaign_name,'')), r'\\[ene\\]|eneas'))
    OR (dt_bp_imported_at BETWEEN '2026-09-18' AND '2026-09-23'
        AND DATE(dt_event_created_at) BETWEEN '2026-09-19' AND '2026-09-22'
        AND REGEXP_CONTAINS(LOWER(COALESCE(nm_campaign,'') || '|' || COALESCE(nm_journey_name,'') || '|' ||
                                  COALESCE(nm_journey_campaign_name,'')), r'\\[lac\\]')))
  AND nm_event IN ('email_delivered', 'whatsapp_delivered', 'push_delivered',
                   'email_click', 'whatsapp_click', 'email_open')
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
"""

Q_LEADS = """
SELECT nm_tag AS sigla, DATE(dt_registered_at_br) AS dt,
  COUNT(DISTINCT nm_email) AS qt_leads,
  -- leads vindos do Meta: denominador correto do CPL de midia (o total inclui organico,
  -- portal, CRM, PMax e Google, que nao estao no numerador de spend)
  COUNT(DISTINCT IF(LOWER(utm_source) LIKE '%face%', nm_email, NULL)) AS qt_leads_meta
FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
WHERE nm_tag IN ('ENE', 'LAC')
  AND (DATE(dt_registered_at_br) BETWEEN '2026-07-28' AND '2026-07-31'
    OR DATE(dt_registered_at_br) BETWEEN '2026-09-19' AND '2026-09-22')
GROUP BY 1, 2
ORDER BY 1, 2
"""


def build() -> dict:
    print("  meta ads...", flush=True)
    meta = clean(q("01_meta_primeiros_dias.sql"))
    print("  anuncios distintos...", flush=True)
    ads = clean(q("05_resumo_d1_d3.sql"))
    print("  criativo e roas...", flush=True)
    criativo = clean(q("06_criativo_e_roas.sql"))
    print("  cpm pareado (within-campaign)...", flush=True)
    cpm_pareado = clean(q("07_cpm_pareado.sql"))
    print("  midia nos 3 canais...", flush=True)
    midia = clean(q("08_midia_todos_canais.sql"))
    print("  crm por data de disparo...", flush=True)
    crm_disparo = clean(q("09_crm_por_disparo.sql"))
    print("  cpm da conta...", flush=True)
    cpm_conta = clean(q("04_cpm_benchmark_conta.sql"))
    print("  crm...", flush=True)
    crm = clean(bq(Q_CRM))
    print("  vendas...", flush=True)
    vendas = clean(q("03_vendas_rastro.sql"))
    print("  leads...", flush=True)
    leads = clean(bq(Q_LEADS))
    print("  ga4 (lp)...", flush=True)
    lp = ga4_lp()

    for r in crm + leads:
        j = JANELAS[r["sigla"]]
        r["dia"] = (datetime.date.fromisoformat(r["dt"])
                    - datetime.date.fromisoformat(j["d1"])).days + 1

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "janelas": JANELAS,
        "meta": meta,
        "ads_distintos": ads,
        "criativo": criativo,
        "cpm_pareado": cpm_pareado,
        "midia": midia,
        "crm_disparo": crm_disparo,
        "cpm_conta": cpm_conta,
        "crm": crm,
        "vendas": vendas,
        "leads": leads,
        "lp": lp,
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing LAC x ENE report data...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m",
                            f"data: LAC x ENE refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
