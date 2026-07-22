#!/usr/bin/env python3
"""
Refresh — Lançamento Odisseia vs Clube do Livro (Comercial + hipótese BP10).

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Janelas:
  CDL: D1 = 2026-05-05 (abertura Comercial)
  ODI: D1 = 2026-07-17 (primeira venda)
As queries canônicas estão em queries/*.sql — manter em sincronia.
"""

import json, subprocess, sys, datetime
from pathlib import Path

CDL_D1 = "2026-05-05"
ODI_D1 = "2026-07-17"
N_DIAS = 6  # dias equivalentes comparados (D1–D6); ODI cresce conforme a campanha anda
OUT = Path(__file__).parent / "data.json"

ODI_FILTER = "(nm_gateway_plan='livro-odisseia-edicao-colecionador' OR LOWER(nm_gateway_product) LIKE '%odis%')"
CDL_FILTER = "nm_gateway_plan='clube-do-livro' AND nm_gateway_product NOT LIKE '%Bundle%'"


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


Q_PLACAR = f"""
WITH vendas AS (
  SELECT 'CDL' AS campanha,
         DATE_DIFF(DATE(dt_ordered_at), DATE '{CDL_D1}', DAY)+1 AS dia_campanha,
         CASE WHEN bl_is_commercial_channel THEN 'comercial' ELSE 'digital' END AS canal,
         vl_payment_gross
  FROM masterdata.fct_transactions
  WHERE DATE(dt_ordered_at) >= '{CDL_D1}'
    AND nm_status='approved' AND bl_is_renovation = FALSE AND {CDL_FILTER}
  UNION ALL
  SELECT 'ODI',
         DATE_DIFF(DATE(dt_ordered_at), DATE '{ODI_D1}', DAY)+1,
         CASE WHEN bl_is_commercial_channel THEN 'comercial' ELSE 'digital' END,
         vl_payment_gross
  FROM masterdata.fct_transactions
  WHERE DATE(dt_ordered_at) >= '{ODI_D1}'
    AND nm_status='approved' AND bl_is_renovation = FALSE AND {ODI_FILTER}
)
SELECT campanha, dia_campanha, canal,
       COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM vendas WHERE dia_campanha BETWEEN 1 AND {N_DIAS}
GROUP BY 1,2,3 ORDER BY dia_campanha, campanha, canal
"""

Q_SELLERS = f"""
WITH v AS (
  SELECT 'CDL' AS campanha, nm_pptc_tracking_name AS tracking
  FROM masterdata.fct_transactions
  WHERE DATE(dt_ordered_at) BETWEEN '{CDL_D1}' AND DATE_ADD('{CDL_D1}', INTERVAL {N_DIAS - 1} DAY)
    AND nm_status='approved' AND bl_is_commercial_channel AND {CDL_FILTER}
  UNION ALL
  SELECT 'ODI', nm_pptc_tracking_name
  FROM masterdata.fct_transactions
  WHERE DATE(dt_ordered_at) BETWEEN '{ODI_D1}' AND DATE_ADD('{ODI_D1}', INTERVAL {N_DIAS - 1} DAY)
    AND nm_status='approved' AND bl_is_commercial_channel AND {ODI_FILTER}
)
SELECT campanha, COUNT(*) AS vendas,
       COUNT(DISTINCT REGEXP_EXTRACT(LOWER(tracking), r'(c\\d{{4}})')) AS vendedores
FROM v GROUP BY 1
"""

Q_MENCOES = f"""
WITH conv AS (
  SELECT 'CDL' AS campanha,
         DATE_DIFF(DATE(dt_approach_start), DATE '{CDL_D1}', DAY)+1 AS dia_campanha,
         REGEXP_CONTAINS(LOWER(nm_conversation), r'clube do livro') AS menciona,
         id_seller
  FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN DATE_SUB('{CDL_D1}', INTERVAL 4 DAY)
                                    AND DATE_ADD('{CDL_D1}', INTERVAL {N_DIAS - 1} DAY)
  UNION ALL
  SELECT 'ODI',
         DATE_DIFF(DATE(dt_approach_start), DATE '{ODI_D1}', DAY)+1,
         REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia'),
         id_seller
  FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN DATE_SUB('{ODI_D1}', INTERVAL 4 DAY)
                                    AND DATE_ADD('{ODI_D1}', INTERVAL {N_DIAS - 1} DAY)
)
SELECT campanha, dia_campanha,
       COUNT(*) AS abordagens_total,
       COUNTIF(menciona) AS mencoes,
       COUNT(DISTINCT IF(menciona, id_seller, NULL)) AS vendedores_mencionando
FROM conv GROUP BY 1,2 ORDER BY campanha, dia_campanha
"""

Q_MENCOES_JUL = """
SELECT DATE(dt_approach_start) AS dia,
       COUNT(*) AS abordagens_total,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')) AS odisseia,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'clube do livro')) AS cdl,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'10 anos|dez anos|anivers[aá]rio')) AS bp10
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) >= '2026-07-14'
GROUP BY 1 ORDER BY 1
"""

Q_MIX = f"""
WITH v AS (
  SELECT CASE WHEN DATE(dt_ordered_at) BETWEEN '{CDL_D1}' AND DATE_ADD('{CDL_D1}', INTERVAL 6 DAY)
              THEN 'mai' ELSE 'jul' END AS janela,
         CASE
           WHEN nm_gateway_plan='clube-do-livro' OR nm_gateway_plan LIKE 'ebooks%clube%' THEN 'Clube do Livro'
           WHEN {ODI_FILTER} THEN 'Odisseia'
           WHEN LOWER(nm_gateway_plan) LIKE '%bp-10%' OR LOWER(nm_gateway_plan) LIKE '%10-anos%'
             OR LOWER(nm_gateway_product) LIKE '%10 anos%' THEN 'Combos BP10'
           WHEN nm_gateway_plan LIKE 'mecenas%' THEN 'Mecenas'
           WHEN bl_lifetime_offer THEN 'Vitalício'
           ELSE 'Assinaturas/outros'
         END AS produto,
         vl_payment_gross
  FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
    AND (DATE(dt_ordered_at) BETWEEN '{CDL_D1}' AND DATE_ADD('{CDL_D1}', INTERVAL 6 DAY)
      OR DATE(dt_ordered_at) BETWEEN '2026-07-16' AND DATE_ADD('2026-07-16', INTERVAL 6 DAY))
)
SELECT janela, produto, COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita,
       ROUND(100*COUNT(*)/SUM(COUNT(*)) OVER (PARTITION BY janela),1) AS pct_vendas
FROM v GROUP BY 1,2 ORDER BY janela, vendas DESC
"""

Q_CAPACIDADE = f"""
SELECT CASE WHEN DATE(dt_approach_start) BETWEEN '{CDL_D1}' AND DATE_ADD('{CDL_D1}', INTERVAL 6 DAY)
            THEN 'mai' ELSE 'jul' END AS janela,
       COUNT(*) AS abordagens, COUNT(DISTINCT id_seller) AS vendedores,
       ROUND(COUNT(*)/7,0) AS abordagens_dia
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '{CDL_D1}' AND DATE_ADD('{CDL_D1}', INTERVAL 6 DAY)
   OR DATE(dt_approach_start) BETWEEN '2026-07-16' AND DATE_ADD('2026-07-16', INTERVAL 6 DAY)
GROUP BY 1
"""

Q_LEADS = f"""
SELECT 'ODI' AS camp, COUNT(*) AS leads
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'ODI\\]|ODISSEIA')
UNION ALL
SELECT 'CDL', COUNT(*)
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'CDL\\]|CLUBE.DO.LIVRO')
  AND dt_registered_at_br < '2026-05-18'
"""

Q_SPEND = """
SELECT CASE WHEN UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%'
            THEN 'ODI' ELSE 'CDL' END AS camp,
       ROUND(SUM(vl_amount_spent),0) AS spend
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE reference_date >= '2026-04-01'
  AND ((UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')
    OR (UPPER(nm_campaign_name) LIKE '%[CDL]%' AND reference_date < '2026-05-18'))
GROUP BY 1
"""

Q_CONVERSAS_ODI = """
SELECT nm_stage, nm_conversation
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) >= '2026-07-14'
  AND REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')
"""

Q_TOTAL_COMERCIAL = f"""
SELECT CASE WHEN DATE(dt_ordered_at) BETWEEN '{CDL_D1}' AND DATE_ADD('{CDL_D1}', INTERVAL {N_DIAS - 1} DAY)
            THEN 'mai' ELSE 'jul' END AS janela,
       COUNT(*) AS vendas,
       ROUND(SUM(vl_payment_gross),0) AS receita,
       ROUND(SUM(vl_payment_gross)/{N_DIAS},0) AS receita_dia,
       ROUND(AVG(vl_payment_gross),0) AS ticket_medio,
       COUNT(DISTINCT REGEXP_EXTRACT(LOWER(nm_pptc_tracking_name), r'(c\\d{{4}})')) AS vendedores_com_venda
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND (DATE(dt_ordered_at) BETWEEN '{CDL_D1}' AND DATE_ADD('{CDL_D1}', INTERVAL {N_DIAS - 1} DAY)
    OR DATE(dt_ordered_at) BETWEEN '{ODI_D1}' AND DATE_ADD('{ODI_D1}', INTERVAL {N_DIAS - 1} DAY))
GROUP BY 1
"""

Q_ANIV = """
SELECT COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND bl_lifetime_offer
  AND DATE(dt_ordered_at) BETWEEN '2026-07-16' AND DATE_ADD('2026-07-16', INTERVAL 6 DAY)
  AND LOWER(nm_gateway_offer) LIKE '%aniv26%'
"""


def build() -> dict:
    print("  placar D1–D6...", flush=True)
    placar_rows = bq(Q_PLACAR)
    dias = list(range(1, N_DIAS + 1))
    placar = {}
    for camp in ("CDL", "ODI"):
        for canal in ("comercial", "digital"):
            key = f"{camp.lower()}_{canal}"
            placar[key] = {"vendas": [0]*N_DIAS, "receita": [0.0]*N_DIAS}
    for r in placar_rows:
        key = f"{r['campanha'].lower()}_{r['canal']}"
        d = ii(r["dia_campanha"]) - 1
        if 0 <= d < N_DIAS:
            placar[key]["vendas"][d] = ii(r["vendas"])
            placar[key]["receita"][d] = fi(r["receita"])

    totais = {}
    for camp in ("cdl", "odi"):
        com = placar[f"{camp}_comercial"]; dig = placar[f"{camp}_digital"]
        totais[camp] = {
            "vendas": sum(com["vendas"]) + sum(dig["vendas"]),
            "receita": sum(com["receita"]) + sum(dig["receita"]),
            "comercial": sum(com["vendas"]),
            "digital": sum(dig["vendas"]),
        }

    print("  vendedores...", flush=True)
    for r in bq(Q_SELLERS):
        totais[r["campanha"].lower()]["vendedores"] = ii(r["vendedores"])

    print("  menções Zenvia (esforço)...", flush=True)
    menc_rows = bq(Q_MENCOES)
    # dia_campanha vai de -3 (D1-4) a N_DIAS
    dias_menc = list(range(-3, N_DIAS + 1))
    mencoes = {c: {"abordagens": [0]*len(dias_menc), "mencoes": [0]*len(dias_menc),
                   "vendedores": [0]*len(dias_menc)} for c in ("cdl", "odi")}
    for r in menc_rows:
        idx = ii(r["dia_campanha"]) + 3
        if 0 <= idx < len(dias_menc):
            m = mencoes[r["campanha"].lower()]
            m["abordagens"][idx] = ii(r["abordagens_total"])
            m["mencoes"][idx] = ii(r["mencoes"])
            m["vendedores"][idx] = ii(r["vendedores_mencionando"])

    conversao = {}
    for camp in ("cdl", "odi"):
        menc_venda = sum(mencoes[camp]["mencoes"][3:])  # só D1+
        vendas_com = totais[camp]["comercial"]
        conversao[camp] = {
            "mencoes_d1_dn": menc_venda,
            "vendas_comercial": vendas_com,
            "taxa_pct": round(100 * vendas_com / menc_venda, 1) if menc_venda else None,
        }

    print("  menções por tema (jul)...", flush=True)
    menc_jul = [{"dia": r["dia"], "abordagens": ii(r["abordagens_total"]),
                 "odisseia": ii(r["odisseia"]), "cdl": ii(r["cdl"]), "bp10": ii(r["bp10"])}
                for r in bq(Q_MENCOES_JUL)]

    print("  mix do Comercial...", flush=True)
    mix = [{"janela": r["janela"], "produto": r["produto"], "vendas": ii(r["vendas"]),
            "receita": fi(r["receita"]), "pct": fi(r["pct_vendas"])} for r in bq(Q_MIX)]

    print("  capacidade...", flush=True)
    capacidade = {r["janela"]: {"abordagens": ii(r["abordagens"]),
                                "vendedores": ii(r["vendedores"]),
                                "abordagens_dia": ii(r["abordagens_dia"])}
                  for r in bq(Q_CAPACIDADE)}

    print("  contexto das conversas ODI...", flush=True)
    import re as _re
    convs = bq(Q_CONVERSAS_ODI, max_rows=500)
    ctx = {"total": len(convs), "vendedor_primeiro": 0, "cliente_primeiro": 0,
           "script_concierge": 0, "cita_cdl": 0, "stages": {}}
    for r in convs:
        c = r["nm_conversation"] or ""
        low = c.lower()
        pos = low.find("odiss")
        marcadores = [(m.start(), m.group(1)) for m in _re.finditer(r"\b(seller|manager|prospect):", c[:pos])]
        if marcadores:
            quem = marcadores[-1][1]
            ctx["vendedor_primeiro" if quem in ("seller", "manager") else "cliente_primeiro"] += 1
        if "membro fundador da cole" in low or "concierge liter" in low:
            ctx["script_concierge"] += 1
        if "clube do livro" in low:
            ctx["cita_cdl"] += 1
        stage = r["nm_stage"] or "(sem etapa)"
        ctx["stages"][stage] = ctx["stages"].get(stage, 0) + 1
    ctx["stages"] = dict(sorted(ctx["stages"].items(), key=lambda kv: -kv[1]))

    print("  receita total do Comercial...", flush=True)
    total_comercial = {r["janela"]: {"vendas": ii(r["vendas"]), "receita": fi(r["receita"]),
                                     "receita_dia": fi(r["receita_dia"]),
                                     "ticket": fi(r["ticket_medio"]),
                                     "vendedores_com_venda": ii(r["vendedores_com_venda"])}
                       for r in bq(Q_TOTAL_COMERCIAL)}

    print("  estrutura (leads + spend)...", flush=True)
    leads = {r["camp"]: ii(r["leads"]) for r in bq(Q_LEADS)}
    spend = {r["camp"]: fi(r["spend"]) for r in bq(Q_SPEND)}
    aniv = bq(Q_ANIV)[0]

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "config": {"cdl_d1": CDL_D1, "odi_d1": ODI_D1, "n_dias": N_DIAS},
        "placar": placar,
        "totais": totais,
        "mencoes": {"dias": dias_menc, **mencoes},
        "conversao": conversao,
        "mencoes_jul": menc_jul,
        "mix": mix,
        "contexto_conversas": ctx,
        "total_comercial": total_comercial,
        "capacidade": capacidade,
        "estrutura": {
            "leads_cdl": leads.get("CDL", 0), "leads_odi": leads.get("ODI", 0),
            "spend_cdl": spend.get("CDL", 0), "spend_odi": spend.get("ODI", 0),
            "aniv26_vendas": ii(aniv["vendas"]), "aniv26_receita": fi(aniv["receita"]),
        },
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing odisseia-lancamento data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: odisseia-lancamento refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
