#!/usr/bin/env python3
"""
Refresh: Perfil de Compra — Clube do Livro
Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

OUT = Path(__file__).parent / "data.json"

def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json", f"--max_rows={max_rows}", sql],
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
    try: return int(float(v)) if v not in (None, "", "null") else 0
    except: return 0

# ── CTEs base (reutilizadas em todas as queries) ──────────────────────────────

CDL_BASE = """
  cdl_compradores AS (
    SELECT
      t.id_gateway_customer,
      t.id_transaction,
      t.dt_ordered_at AS dt_compra_cdl,
      dpi.id_person
    FROM `bp-datawarehouse.masterdata.fct_transactions` t
    JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    WHERE t.nm_gateway_plan = 'clube-do-livro'
      AND t.nm_status = 'approved'
      AND t.nm_gateway_product IN (
        'Comercial - Clube do Livro',
        'Comercial - Clube do Livro + Black',
        'Comercial - Clube do Livro + Black 18x',
        'Comercial - Clube do Livro 18x',
        'Comercial - Clube do Livro [18x]',
        'Comercial - Clube do Livro - Bronze 18x',
        'Brasil Paralelo - Clube do Livro',
        'Clube do Livro - CS'
      )
      AND c.nm_email IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (PARTITION BY dpi.id_person ORDER BY t.dt_ordered_at ASC) = 1
  ),
  subscription_history AS (
    SELECT
      dpi.id_person,
      s.dt_started_at,
      s.dt_expires_in,
      s.nm_subscription_recurrence
    FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
    JOIN `bp-datawarehouse.masterdata.dim_contact` c ON c.id_gateway_customer = s.id_gateway_customer
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    WHERE s.nm_type = 'paid'
      AND dpi.id_person IN (SELECT id_person FROM cdl_compradores)
  ),
  vitalicio_fct AS (
    SELECT DISTINCT cdl.id_person
    FROM `bp-datawarehouse.masterdata.fct_transactions` t
    JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    JOIN cdl_compradores cdl USING (id_person)
    WHERE t.bl_lifetime_offer = TRUE
      AND t.nm_status = 'approved'
      AND DATE(t.dt_ordered_at) < DATE(cdl.dt_compra_cdl)
  )
"""

# ── queries ───────────────────────────────────────────────────────────────────

Q_TOTAIS = f"""
WITH {CDL_BASE}
SELECT
  COUNT(DISTINCT p.id_person)            AS compradores,
  ROUND(SUM(t.vl_payment_gross), 0)      AS receita_total,
  ROUND(AVG(t.vl_payment_gross), 0)      AS ticket_medio,
  MIN(DATE(p.dt_compra_cdl))             AS periodo_inicio,
  MAX(DATE(p.dt_compra_cdl))             AS periodo_fim
FROM cdl_compradores p
JOIN `bp-datawarehouse.masterdata.fct_transactions` t USING (id_transaction)
"""

Q_STATUS = f"""
WITH {CDL_BASE},
member_classification AS (
  SELECT
    p.id_person,
    CASE
      WHEN COUNTIF(s.nm_subscription_recurrence = 'vitalício' AND s.dt_started_at < p.dt_compra_cdl) > 0
        OR MAX(IF(vf.id_person IS NOT NULL, 1, 0)) = 1
        THEN 'Vitalício'
      WHEN COUNTIF(p.dt_compra_cdl > s.dt_started_at AND p.dt_compra_cdl <= s.dt_expires_in) > 0
        THEN 'Membro Ativo'
      WHEN COUNTIF(s.dt_started_at < p.dt_compra_cdl) > 0
        THEN 'Ex-Membro'
      ELSE 'Nunca foi Membro'
    END AS status
  FROM cdl_compradores p
  LEFT JOIN subscription_history s USING (id_person)
  LEFT JOIN vitalicio_fct vf USING (id_person)
  GROUP BY p.id_person
)
SELECT
  status,
  COUNT(*) AS qt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM member_classification
GROUP BY 1
ORDER BY qt DESC
"""

Q_ANTIGUIDADE = f"""
WITH {CDL_BASE},
primeira_compra AS (
  SELECT
    cdl.id_person,
    MIN(t.dt_ordered_at) AS dt_primeira_bp
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = dc.nm_email
    AND dpi.nm_identifier_type = 'email'
  JOIN cdl_compradores cdl USING (id_person)
  WHERE t.nm_status = 'approved'
  GROUP BY 1
)
SELECT
  CASE
    WHEN DATE_DIFF(DATE(c.dt_compra_cdl), DATE(p.dt_primeira_bp), DAY) <= 7   THEN 'CDL como 1ª compra'
    WHEN DATE_DIFF(DATE(c.dt_compra_cdl), DATE(p.dt_primeira_bp), DAY) <= 180  THEN '< 6 meses'
    WHEN DATE_DIFF(DATE(c.dt_compra_cdl), DATE(p.dt_primeira_bp), DAY) <= 365  THEN '6–12 meses'
    WHEN DATE_DIFF(DATE(c.dt_compra_cdl), DATE(p.dt_primeira_bp), DAY) <= 730  THEN '1–2 anos'
    WHEN DATE_DIFF(DATE(c.dt_compra_cdl), DATE(p.dt_primeira_bp), DAY) <= 1460 THEN '2–4 anos'
    ELSE 'Mais de 4 anos'
  END AS faixa,
  COUNT(*) AS qt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
  ROUND(AVG(DATE_DIFF(DATE(c.dt_compra_cdl), DATE(p.dt_primeira_bp), DAY))) AS media_dias
FROM cdl_compradores c
JOIN primeira_compra p USING (id_person)
GROUP BY 1
ORDER BY media_dias
"""

Q_PRODUTOS_ANTES = f"""
WITH {CDL_BASE},
historico AS (
  SELECT
    cdl.id_person,
    t.nm_plan_label,
    t.nm_gateway_plan
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = dc.nm_email
    AND dpi.nm_identifier_type = 'email'
  JOIN cdl_compradores cdl USING (id_person)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.nm_gateway_plan NOT IN ('clube-do-livro', 'outros')
    AND t.nm_plan_label IS NOT NULL
    AND DATE(t.dt_ordered_at) < DATE(cdl.dt_compra_cdl)
),
total_cdl AS (SELECT COUNT(DISTINCT id_person) AS n FROM cdl_compradores)
SELECT
  nm_plan_label,
  COUNT(DISTINCT id_person) AS compradores,
  ROUND(COUNT(DISTINCT id_person) * 100.0 / MAX(total_cdl.n), 1) AS pct_base
FROM historico, total_cdl
GROUP BY 1
HAVING compradores >= 50
ORDER BY compradores DESC
LIMIT 20
"""

Q_CANAL = f"""
WITH {CDL_BASE}
SELECT
  CASE WHEN t.bl_is_commercial_channel THEN 'Comercial' ELSE 'Digital' END AS canal,
  COUNT(DISTINCT p.id_person)  AS qt,
  ROUND(COUNT(DISTINCT p.id_person) * 100.0 / SUM(COUNT(DISTINCT p.id_person)) OVER(), 1) AS pct,
  ROUND(AVG(t.vl_payment_gross), 0)    AS ticket_medio,
  ROUND(SUM(t.vl_payment_gross), 0)    AS receita
FROM cdl_compradores p
JOIN `bp-datawarehouse.masterdata.fct_transactions` t USING (id_transaction)
GROUP BY 1
ORDER BY qt DESC
"""

Q_CONSUMO = f"""
WITH {CDL_BASE},
historico AS (
  SELECT
    cdl.id_person,
    SUM(CASE WHEN t.bl_is_renovation = FALSE THEN t.vl_payment_gross ELSE 0 END) AS vl_total,
    COUNT(DISTINCT t.nm_gateway_plan) AS qt_planos
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = dc.nm_email
    AND dpi.nm_identifier_type = 'email'
  JOIN cdl_compradores cdl USING (id_person)
  WHERE t.nm_status = 'approved'
    AND t.nm_gateway_plan != 'clube-do-livro'
    AND DATE(t.dt_ordered_at) < DATE(cdl.dt_compra_cdl)
  GROUP BY 1
)
SELECT
  ROUND(AVG(vl_total), 0)                                         AS gasto_medio,
  ROUND(APPROX_QUANTILES(vl_total, 100)[OFFSET(50)], 0)          AS mediana_gasto,
  ROUND(AVG(qt_planos), 1)                                        AS media_planos,
  COUNT(*)                                                        AS com_historico
FROM historico
"""

# ── build ─────────────────────────────────────────────────────────────────────

def build() -> dict:
    print("  totais...", flush=True)
    tot = bq(Q_TOTAIS)[0]

    print("  status de membro...", flush=True)
    status_rows = bq(Q_STATUS)

    print("  antiguidade...", flush=True)
    ant_rows = bq(Q_ANTIGUIDADE)

    print("  produtos anteriores...", flush=True)
    prod_rows = bq(Q_PRODUTOS_ANTES)

    print("  canal...", flush=True)
    canal_rows = bq(Q_CANAL)

    print("  consumo histórico...", flush=True)
    cons = bq(Q_CONSUMO)[0]

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "totais": {
            "compradores":    ii(tot["compradores"]),
            "receita_total":  ii(tot["receita_total"]),
            "ticket_medio":   ii(tot["ticket_medio"]),
            "periodo_inicio": str(tot["periodo_inicio"]),
            "periodo_fim":    str(tot["periodo_fim"]),
        },
        "status": [
            {"label": r["status"], "qt": ii(r["qt"]), "pct": fi(r["pct"])}
            for r in status_rows
        ],
        "antiguidade": [
            {"label": r["faixa"], "qt": ii(r["qt"]), "pct": fi(r["pct"]), "media_dias": ii(r["media_dias"])}
            for r in ant_rows
        ],
        "produtos_antes": [
            {"plano": r["nm_plan_label"], "compradores": ii(r["compradores"]), "pct": fi(r["pct_base"])}
            for r in prod_rows
        ],
        "canal": [
            {"canal": r["canal"], "qt": ii(r["qt"]), "pct": fi(r["pct"]),
             "ticket_medio": ii(r["ticket_medio"]), "receita": ii(r["receita"])}
            for r in canal_rows
        ],
        "consumo": {
            "gasto_medio":   ii(cons["gasto_medio"]),
            "mediana_gasto": ii(cons["mediana_gasto"]),
            "media_planos":  fi(cons["media_planos"]),
            "com_historico": ii(cons["com_historico"]),
        },
    }

# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing Clube do Livro report...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            repo = Path(__file__).parent.parent.parent
            subprocess.run(["git", "add", str(OUT)], check=True, cwd=repo)
            subprocess.run(["git", "commit", "-m", f"data: clube-do-livro refresh {datetime.date.today()}"], check=True, cwd=repo)
            subprocess.run(["git", "push", "origin", "main"], check=True, cwd=repo)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
