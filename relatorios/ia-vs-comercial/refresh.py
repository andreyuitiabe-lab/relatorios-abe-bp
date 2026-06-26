#!/usr/bin/env python3
"""
IA vs Comercial — Hotleads junho 2026

Fonte: bp-datawarehouse.datamart.dtm_seller_conversion_rate

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

OUT          = Path(__file__).parent / "data.json"
PERIODO      = "2026-06-01"
PERIODO_FIM  = "2026-06-30"
PERIODO_LABEL = "Junho 2026"

TIPOS_PRINCIPAIS = "('OPORTUNIDADE DE VENDA','ABANDONO DE CARRINHO','COMPRA NEGADA')"

# Mapeamento canônico: nm_source_gateway_plan → produto normalizado
PRODUTO_CANONICAL = """
  CASE
    WHEN nm_source_gateway_plan LIKE 'supporter%'               THEN 'apoiador'
    WHEN nm_source_gateway_plan LIKE 'apoiador%'                THEN 'apoiador'
    WHEN nm_source_gateway_plan LIKE 'bp-economico%'            THEN 'apoiador'
    WHEN nm_source_gateway_plan LIKE 'extensao-assinatura-supporter%' THEN 'apoiador'
    WHEN nm_source_gateway_plan LIKE 'combo-religioso%'         THEN 'apoiador'
    WHEN nm_source_gateway_plan LIKE 'guia-analises%'           THEN 'apoiador'
    WHEN nm_source_gateway_plan LIKE 'good%'                    THEN 'bp-essencial'
    WHEN nm_source_gateway_plan LIKE 'bp-essencial%'            THEN 'bp-essencial'
    WHEN nm_source_gateway_plan LIKE 'extensao-assinatura-good%' THEN 'bp-essencial'
    WHEN nm_source_gateway_plan LIKE 'combo-essencial-religioso%' THEN 'bp-essencial'
    WHEN nm_source_gateway_plan LIKE 'better%'                  THEN 'bp-intermediario'
    WHEN nm_source_gateway_plan LIKE 'best%'                    THEN 'bp-premium'
    WHEN nm_source_gateway_plan LIKE 'extensao-assinatura-premium%' THEN 'bp-premium'
    WHEN nm_source_gateway_plan LIKE 'black%'                   THEN 'black'
    WHEN nm_source_gateway_plan LIKE 'clube-do-livro%'          THEN 'clube-do-livro'
    WHEN nm_source_gateway_plan LIKE 'ebook%'                   THEN 'clube-do-livro'
    WHEN nm_source_gateway_plan LIKE 'analises-clube-livro%'    THEN 'clube-do-livro'
    WHEN nm_source_gateway_plan LIKE 'teller%'                  THEN 'teller'
    WHEN nm_source_gateway_plan LIKE 'mecenas%'                 THEN 'mecenas'
    ELSE COALESCE(nm_source_gateway_plan, 'desconhecido')
  END
"""

# ─── BQ helper ───────────────────────────────────────────────────────────────
def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         f"--max_rows={max_rows}", sql],
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

Q_RESUMO = f"""
SELECT
  CASE nm_stage WHEN '10. AWSALES LISTA' THEN 'IA' ELSE 'Comercial' END AS canal,
  COUNT(*) AS qt_leads,
  SUM(CASE WHEN id_transaction IS NOT NULL THEN 1 ELSE 0 END) AS qt_convertidos,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS pct_conversao,
  ROUND(AVG(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE NULL END), 2) AS ticket_medio,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE 0 END), 2) AS receita_total,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE 0 END) / COUNT(*), 2) AS receita_por_lead
FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate`
WHERE SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] IN {TIPOS_PRINCIPAIS}
  AND DATE(dt_created_at) BETWEEN '{PERIODO}' AND '{PERIODO_FIM}'
  AND (
    nm_stage = '10. AWSALES LISTA'
    OR (nm_stage != '10. AWSALES LISTA' AND dt_first_message IS NOT NULL)
  )
GROUP BY 1
ORDER BY 1
"""

Q_POR_TIPO = f"""
SELECT
  CASE nm_stage WHEN '10. AWSALES LISTA' THEN 'IA' ELSE 'Comercial' END AS canal,
  SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] AS tipo_hotlead,
  SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(1)] AS origem,
  COUNT(*) AS qt_leads,
  SUM(CASE WHEN id_transaction IS NOT NULL THEN 1 ELSE 0 END) AS qt_convertidos,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS pct_conversao,
  ROUND(AVG(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE NULL END), 2) AS ticket_medio,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE 0 END) / COUNT(*), 2) AS receita_por_lead
FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate`
WHERE SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] IN {TIPOS_PRINCIPAIS}
  AND DATE(dt_created_at) BETWEEN '{PERIODO}' AND '{PERIODO_FIM}'
  AND (
    nm_stage = '10. AWSALES LISTA'
    OR (nm_stage != '10. AWSALES LISTA' AND dt_first_message IS NOT NULL)
  )
GROUP BY 1,2,3
ORDER BY canal, tipo_hotlead, origem
"""

Q_DETALHADO = f"""
SELECT
  CASE nm_stage WHEN '10. AWSALES LISTA' THEN 'IA' ELSE 'Comercial' END AS canal,
  SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] AS tipo_hotlead,
  SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(1)] AS origem,
  {PRODUTO_CANONICAL} AS produto_origem,
  COUNT(*) AS qt_leads,
  SUM(CASE WHEN id_transaction IS NOT NULL THEN 1 ELSE 0 END) AS qt_convertidos,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS pct_conversao,
  ROUND(AVG(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE NULL END), 2) AS ticket_medio,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE 0 END), 2) AS receita_total,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE 0 END) / COUNT(*), 2) AS receita_por_lead
FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate`
WHERE nm_hotlead_type IS NOT NULL
  AND DATE(dt_created_at) BETWEEN '{PERIODO}' AND '{PERIODO_FIM}'
  AND (
    nm_stage = '10. AWSALES LISTA'
    OR (nm_stage != '10. AWSALES LISTA' AND dt_first_message IS NOT NULL)
  )
GROUP BY 1,2,3,4
HAVING qt_leads >= 20
ORDER BY canal, tipo_hotlead, origem, qt_leads DESC
"""

# Upsell: transações aprovadas nos 7 dias após a venda inicial, atribuídas por canal
# COM → mesmo vendedor na transação pós-venda
# IA  → qualquer venda do canal Comercial para o mesmo cliente
Q_UPSELL = f"""
WITH deals AS (
  SELECT
    CASE WHEN nm_stage = '10. AWSALES LISTA' THEN 'IA' ELSE 'Comercial' END AS canal,
    SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(1)] AS origem,
    SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] AS tipo_hotlead,
    {PRODUTO_CANONICAL} AS produto,
    id_pipedrive_deal,
    id_gateway_customer,
    id_transaction      AS id_venda_inicial,
    nm_salesman_email   AS vendedor,
    dt_ordered_at       AS dt_venda
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate`
  WHERE SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] IN {TIPOS_PRINCIPAIS}
    AND nm_hotlead_type IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '{PERIODO}' AND '{PERIODO_FIM}'
    AND id_transaction IS NOT NULL
    AND id_gateway_customer IS NOT NULL
    AND (
      nm_stage = '10. AWSALES LISTA'
      OR (nm_stage != '10. AWSALES LISTA' AND dt_first_message IS NOT NULL)
    )
)
SELECT
  d.canal,
  d.origem,
  d.tipo_hotlead,
  d.produto,
  COUNT(DISTINCT d.id_pipedrive_deal)                                                         AS deals_won,
  COUNT(DISTINCT CASE WHEN ft.id_transaction IS NOT NULL THEN d.id_pipedrive_deal END)        AS deals_com_upsell,
  COUNT(ft.id_transaction)                                                                     AS qt_upsell,
  ROUND(COALESCE(SUM(ft.vl_payment_gross), 0), 2)                                             AS receita_upsell
FROM deals d
LEFT JOIN `bp-datawarehouse.masterdata.fct_transactions` ft
  ON  ft.id_gateway_customer = d.id_gateway_customer
  AND ft.nm_status            = 'approved'
  AND ft.dt_ordered_at        > d.dt_venda
  AND ft.dt_ordered_at        <= DATETIME_ADD(d.dt_venda, INTERVAL 7 DAY)
  AND ft.id_transaction       != d.id_venda_inicial
  AND (
    (d.canal = 'Comercial' AND ft.nm_salesman_email = d.vendedor)
    OR
    (d.canal = 'IA'        AND ft.bl_is_commercial_channel = TRUE)
  )
GROUP BY 1, 2, 3, 4
ORDER BY canal, origem, tipo_hotlead, deals_won DESC
"""

# Matriz: IA (todos os leads) vs Comercial (só abordados = dt_first_message IS NOT NULL)
Q_MATRIZ = f"""
SELECT
  CASE nm_stage WHEN '10. AWSALES LISTA' THEN 'IA' ELSE 'Comercial' END AS canal,
  SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(1)] AS origem,
  SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] AS tipo_hotlead,
  {PRODUTO_CANONICAL} AS produto_origem,
  COUNT(*) AS qt_leads,
  SUM(CASE WHEN id_transaction IS NOT NULL THEN 1 ELSE 0 END) AS qt_vendas,
  ROUND(SUM(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE 0 END), 2) AS receita_total,
  ROUND(AVG(CASE WHEN id_transaction IS NOT NULL THEN vl_payment_gross ELSE NULL END), 2) AS ticket_medio
FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate`
WHERE SPLIT(nm_hotlead_type, ' - ')[SAFE_OFFSET(0)] IN {TIPOS_PRINCIPAIS}
  AND nm_hotlead_type IS NOT NULL
  AND DATE(dt_created_at) BETWEEN '{PERIODO}' AND '{PERIODO_FIM}'
  AND (
    nm_stage = '10. AWSALES LISTA'
    OR (nm_stage != '10. AWSALES LISTA' AND dt_first_message IS NOT NULL)
  )
GROUP BY 1,2,3,4
ORDER BY canal, origem, tipo_hotlead, qt_leads DESC
"""

# ─── build ───────────────────────────────────────────────────────────────────

TIPO_ORDEM = [
    ("ABANDONO DE CARRINHO",  "NOVA COMPRA"),
    ("COMPRA NEGADA",         "NOVA COMPRA"),
    ("OPORTUNIDADE DE VENDA", "NOVA COMPRA"),
    ("ABANDONO DE CARRINHO",  "RENOVAÇÃO"),
    ("COMPRA NEGADA",         "RENOVAÇÃO"),
    ("OPORTUNIDADE DE VENDA", "RENOVAÇÃO"),
]

def build() -> dict:
    print("  resumo por canal...", flush=True)
    resumo_rows = bq(Q_RESUMO)
    resumo = {}
    for r in resumo_rows:
        resumo[r["canal"]] = {
            "leads":       ii(r["qt_leads"]),
            "convertidos": ii(r["qt_convertidos"]),
            "pct":         fi(r["pct_conversao"]),
            "ticket":      fi(r["ticket_medio"]),
            "receita":     fi(r["receita_total"]),
            "rpl":         fi(r["receita_por_lead"]),
        }

    print("  por tipo+origem...", flush=True)
    tipo_rows = bq(Q_POR_TIPO)
    tipo_idx = {}
    for r in tipo_rows:
        key = (r["canal"], r["tipo_hotlead"], r["origem"] or "")
        tipo_idx[key] = {
            "leads":  ii(r["qt_leads"]),
            "pct":    fi(r["pct_conversao"]),
            "ticket": fi(r["ticket_medio"]),
            "rpl":    fi(r["receita_por_lead"]),
        }

    por_tipo = []
    for tipo, origem in TIPO_ORDEM:
        ia  = tipo_idx.get(("IA",        tipo, origem), {"leads": 0, "pct": 0, "ticket": 0, "rpl": 0})
        com = tipo_idx.get(("Comercial",  tipo, origem), {"leads": 0, "pct": 0, "ticket": 0, "rpl": 0})
        if ia["leads"] == 0 and com["leads"] == 0:
            continue
        por_tipo.append({
            "label":     f"{tipo.title()} | {(origem or '—').title()}",
            "tipo":      tipo,
            "origem":    origem,
            "ia":        ia,
            "comercial": com,
        })

    print("  detalhamento por produto...", flush=True)
    det_rows = bq(Q_DETALHADO)
    por_produto = [
        {
            "canal":       r["canal"],
            "tipo":        r["tipo_hotlead"],
            "origem":      r["origem"] or "",
            "produto":     r["produto_origem"],
            "leads":       ii(r["qt_leads"]),
            "convertidos": ii(r["qt_convertidos"]),
            "pct":         fi(r["pct_conversao"]),
            "ticket":      fi(r["ticket_medio"]),
            "receita":     fi(r["receita_total"]),
            "rpl":         fi(r["receita_por_lead"]),
        }
        for r in det_rows
    ]

    print("  matriz IA (todos) vs Comercial (abordados)...", flush=True)
    mat_rows = bq(Q_MATRIZ, max_rows=10000)

    # Pivotar por (origem, tipo, produto) separando IA e Comercial
    from collections import defaultdict
    mat_idx = defaultdict(dict)
    for r in mat_rows:
        key = (r["origem"] or "", r["tipo_hotlead"], r["produto_origem"])
        leads   = ii(r["qt_leads"])
        vendas  = ii(r["qt_vendas"])
        receita = fi(r["receita_total"])
        ticket  = fi(r["ticket_medio"])
        pct_conv = round(vendas / leads * 100, 2) if leads else 0
        rpl      = round(receita / leads, 2) if leads else 0
        mat_idx[key][r["canal"]] = {
            "leads":    leads,
            "vendas":   vendas,
            "receita":  receita,
            "ticket":   ticket,
            "pct_conv": pct_conv,
            "rpl":      rpl,
        }

    EMPTY = {"leads":0,"vendas":0,"receita":0,"ticket":0,"pct_conv":0,"rpl":0}
    EMPTY_UPSELL = {"deals_won":0,"deals_com_upsell":0,"pct_upsell":0,"receita_upsell":0,"upsell_por_deal":0}

    print("  upsell pós-venda (7 dias)...", flush=True)
    upsell_rows = bq(Q_UPSELL, max_rows=10000)
    upsell_idx = {}
    for r in upsell_rows:
        deals_won       = ii(r["deals_won"])
        deals_com_up    = ii(r["deals_com_upsell"])
        receita_upsell  = fi(r["receita_upsell"])
        key = (r["canal"], r["origem"] or "", r["tipo_hotlead"], r["produto"])
        upsell_idx[key] = {
            "deals_won":       deals_won,
            "deals_com_upsell": deals_com_up,
            "pct_upsell":      round(deals_com_up / deals_won * 100, 1) if deals_won else 0,
            "receita_upsell":  receita_upsell,
            "upsell_por_deal": round(receita_upsell / deals_won, 2) if deals_won else 0,
        }

    por_matriz = []
    for (origem, tipo, produto), canais in sorted(mat_idx.items()):
        ia  = canais.get("IA",        None)
        com = canais.get("Comercial",  None)
        # só incluir se ao menos 1 canal tem 20+ leads
        ia_leads  = ia["leads"]  if ia  else 0
        com_leads = com["leads"] if com else 0
        if ia_leads < 20 and com_leads < 20:
            continue
        por_matriz.append({
            "origem":      origem,
            "tipo":        tipo,
            "produto":     produto,
            "ia":          ia  or EMPTY,
            "comercial":   com or EMPTY,
            "upsell_ia":   upsell_idx.get(("IA",        origem, tipo, produto), EMPTY_UPSELL),
            "upsell_com":  upsell_idx.get(("Comercial", origem, tipo, produto), EMPTY_UPSELL),
        })

    return {
        "updated_at":  datetime.datetime.now().isoformat(timespec="seconds"),
        "periodo":     PERIODO_LABEL,
        "resumo":      resumo,
        "por_tipo":    por_tipo,
        "por_produto": por_produto,
        "por_matriz":  por_matriz,
    }

# ─── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    push = "--push" in sys.argv
    print(f"Refreshing IA vs Comercial report ({PERIODO_LABEL})...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            repo = Path(__file__).parent.parent.parent
            subprocess.run(["git", "-C", str(repo), "add", str(OUT)], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m",
                            f"data: ia-vs-comercial refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "-C", str(repo), "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
