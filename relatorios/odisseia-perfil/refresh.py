#!/usr/bin/env python3
"""
Refresh: Perfil de Compra — Odisseia (Edição Colecionador)
Espelho do relatório `clube-do-livro`, mesma metodologia (status no momento da
compra, antiguidade, produtos anteriores, canal, consumo histórico) + dois
cortes próprios: tipo de produto (livro x só digital) e recompra CDL -> Odisseia.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

OUT = Path(__file__).parent / "data.json"

def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    """Roda via cliente Python + ADC (mesmo transporte do `bqq`)."""
    from google.cloud import bigquery
    rows = bigquery.Client(project="bp-datawarehouse").query(sql).result(max_results=max_rows)
    return [{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(r).items()} for r in rows]

def fi(v) -> float:
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def ii(v) -> int:
    try: return int(float(v)) if v not in (None, "", "null") else 0
    except: return 0

# ── CTEs base ─────────────────────────────────────────────────────────────────
# Universo e categorias validados em 21/08/2026 (wiki bq-planos.md §Odisseia):
# bundles do Comercial são gravados como DUAS transações no mesmo dia (perna do
# outro produto + perna do livro) -> bl_core marca só a perna Odisseia, senão a
# receita do Black/CDL é creditada ao livro.
#
# ⚠️ Produtos físicos (clube-do-livro, livro-odisseia*, odisseia-curso-avulso)
# geram registro `paid` em dim_subscriptions. Sem excluí-los do histórico de
# assinatura, todo comprador do CDL seria classificado como "Membro Ativo".
PLANOS_PRODUTO = "('clube-do-livro','livro-odisseia-edicao-colecionador','livro-odisseia','odisseia-curso-avulso')"

ODI_BASE = f"""
  odi_tx AS (
    SELECT
      t.id_gateway_customer,
      t.id_transaction,
      t.dt_ordered_at,
      t.vl_payment_gross,
      t.bl_is_commercial_channel,
      dpi.id_person,
      CASE
        WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'black vitalício \\+ odisseia|odisseia - ouro')
          THEN 'Odisseia + Black Vitalício'
        WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'odisseia.*travessia')
          THEN 'Odisseia + Travessia'
        WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'clube do livro \\+ odisseia')
          THEN 'Odisseia + Clube do Livro'
        WHEN t.nm_gateway_plan = 'odisseia-curso-avulso'
          THEN 'Odisseia - Curso Avulso'
        WHEN REGEXP_CONTAINS(LOWER(t.nm_gateway_product), r'odisseia - digital')
          OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'odisseia - bronze')
          THEN 'Odisseia - Digital'
        WHEN t.nm_gateway_plan IN ('livro-odisseia-edicao-colecionador','livro-odisseia')
          THEN 'Odisseia - Livro Físico'
      END AS nm_categoria
    FROM `bp-datawarehouse.masterdata.fct_transactions` t
    JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    WHERE t.nm_status = 'approved'
      AND t.bl_is_renovation = FALSE
      AND c.nm_email IS NOT NULL
      AND (t.nm_gateway_plan IN ('livro-odisseia-edicao-colecionador','livro-odisseia','odisseia-curso-avulso')
           OR REGEXP_CONTAINS(LOWER(t.nm_gateway_product), r'odis')
           OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'odis'))
  ),
  odi_tx_cat AS (
    SELECT
      *,
      CASE WHEN nm_categoria IN ('Odisseia + Black Vitalício','Odisseia + Clube do Livro')
           THEN 0 ELSE 1 END AS bl_core,
      CASE WHEN nm_categoria IN ('Odisseia - Livro Físico','Odisseia + Travessia',
                                 'Odisseia + Black Vitalício','Odisseia + Clube do Livro')
           THEN 1 ELSE 0 END AS bl_livro_fisico
    FROM odi_tx
    WHERE nm_categoria IS NOT NULL
  ),
  odi_compradores AS (
    SELECT
      id_person,
      MIN(dt_ordered_at)                                        AS dt_compra_odi,
      SUM(IF(bl_core = 1, vl_payment_gross, 0))                 AS vl_pago_odisseia,
      MAX(bl_livro_fisico)                                      AS bl_livro_fisico,
      MAX(CAST(bl_is_commercial_channel AS INT64))              AS bl_comercial
    FROM odi_tx_cat
    GROUP BY id_person
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
      AND s.nm_gateway_plan NOT IN {PLANOS_PRODUTO}
      AND dpi.id_person IN (SELECT id_person FROM odi_compradores)
  ),
  vitalicio_fct AS (
    SELECT DISTINCT o.id_person
    FROM `bp-datawarehouse.masterdata.fct_transactions` t
    JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    JOIN odi_compradores o USING (id_person)
    WHERE t.bl_lifetime_offer = TRUE
      AND t.nm_status = 'approved'
      AND t.nm_gateway_plan NOT IN {PLANOS_PRODUTO}
      AND DATE(t.dt_ordered_at) < DATE(o.dt_compra_odi)
  ),
  member_classification AS (
    SELECT
      o.id_person,
      CASE
        WHEN COUNTIF(s.nm_subscription_recurrence = 'vitalício' AND s.dt_started_at < o.dt_compra_odi) > 0
          OR MAX(IF(vf.id_person IS NOT NULL, 1, 0)) = 1 THEN 'Vitalício'
        WHEN COUNTIF(o.dt_compra_odi > s.dt_started_at AND o.dt_compra_odi <= s.dt_expires_in) > 0 THEN 'Membro Ativo'
        WHEN COUNTIF(s.dt_started_at < o.dt_compra_odi) > 0 THEN 'Ex-Membro'
        ELSE 'Nunca foi Membro'
      END AS status
    FROM odi_compradores o
    LEFT JOIN subscription_history s USING (id_person)
    LEFT JOIN vitalicio_fct vf USING (id_person)
    GROUP BY o.id_person
  )
"""

# ── queries ───────────────────────────────────────────────────────────────────

Q_TOTAIS = f"""
WITH {ODI_BASE}
SELECT
  COUNT(*)                                        AS compradores,
  ROUND(SUM(vl_pago_odisseia), 0)                 AS receita_total,
  ROUND(SUM(vl_pago_odisseia) / COUNT(*), 0)      AS ticket_medio,
  MIN(DATE(dt_compra_odi))                        AS periodo_inicio,
  MAX(DATE(dt_compra_odi))                        AS periodo_fim
FROM odi_compradores
"""

Q_STATUS = f"""
WITH {ODI_BASE}
SELECT status, COUNT(*) AS qt,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct
FROM member_classification
GROUP BY 1 ORDER BY qt DESC
"""

Q_ANTIGUIDADE = f"""
WITH {ODI_BASE},
primeira_compra AS (
  SELECT o.id_person, MIN(t.dt_ordered_at) AS dt_primeira_bp
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = dc.nm_email AND dpi.nm_identifier_type = 'email'
  JOIN odi_compradores o USING (id_person)
  WHERE t.nm_status = 'approved'
  GROUP BY 1
)
SELECT
  CASE
    WHEN mc.status = 'Nunca foi Membro' AND DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 0
      THEN 'Odisseia como 1ª compra'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 180  THEN '< 6 meses'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 365  THEN '6–12 meses'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 730  THEN '1–2 anos'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 1460 THEN '2–4 anos'
    ELSE 'Mais de 4 anos'
  END AS faixa,
  COUNT(*) AS qt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
  ROUND(AVG(DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY))) AS media_dias
FROM odi_compradores o
JOIN primeira_compra p USING (id_person)
JOIN member_classification mc USING (id_person)
GROUP BY 1 ORDER BY media_dias
"""

Q_PRODUTOS_ANTES = f"""
WITH {ODI_BASE},
historico AS (
  SELECT o.id_person, t.nm_plan_label
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = dc.nm_email AND dpi.nm_identifier_type = 'email'
  JOIN odi_compradores o USING (id_person)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.nm_gateway_plan NOT IN ('livro-odisseia-edicao-colecionador','livro-odisseia','odisseia-curso-avulso','outros')
    AND t.nm_plan_label IS NOT NULL
    AND DATE(t.dt_ordered_at) < DATE(o.dt_compra_odi)
),
total_odi AS (SELECT COUNT(*) AS n FROM odi_compradores)
SELECT nm_plan_label,
       COUNT(DISTINCT id_person) AS compradores,
       ROUND(COUNT(DISTINCT id_person) * 100.0 / MAX(total_odi.n), 1) AS pct_base
FROM historico, total_odi
GROUP BY 1
HAVING compradores >= 20
ORDER BY compradores DESC
LIMIT 20
"""

Q_CANAL = f"""
WITH {ODI_BASE}
SELECT
  CASE WHEN bl_comercial = 1 THEN 'Comercial' ELSE 'Digital' END AS canal,
  COUNT(*) AS qt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
  ROUND(AVG(vl_pago_odisseia), 0) AS ticket_medio,
  ROUND(SUM(vl_pago_odisseia), 0) AS receita
FROM odi_compradores
GROUP BY 1 ORDER BY qt DESC
"""

Q_CONSUMO = f"""
WITH {ODI_BASE},
historico AS (
  SELECT o.id_person,
         SUM(t.vl_payment_gross)           AS vl_total,
         COUNT(DISTINCT t.nm_gateway_plan) AS qt_planos
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = dc.nm_email AND dpi.nm_identifier_type = 'email'
  JOIN odi_compradores o USING (id_person)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.nm_gateway_plan NOT IN ('livro-odisseia-edicao-colecionador','livro-odisseia','odisseia-curso-avulso')
    AND DATE(t.dt_ordered_at) < DATE(o.dt_compra_odi)
  GROUP BY 1
)
SELECT ROUND(AVG(vl_total), 0)                                AS gasto_medio,
       ROUND(APPROX_QUANTILES(vl_total, 100)[OFFSET(50)], 0)  AS mediana_gasto,
       ROUND(AVG(qt_planos), 1)                               AS media_planos,
       COUNT(*)                                               AS com_historico
FROM historico
"""

# Corte próprio 1: livro físico x só digital (curso avulso / ebook)
Q_TIPO = f"""
WITH {ODI_BASE}
SELECT
  CASE WHEN bl_livro_fisico = 1 THEN 'Livro físico' ELSE 'Só digital (curso/ebook)' END AS tipo,
  COUNT(*) AS qt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
  ROUND(AVG(vl_pago_odisseia), 0) AS ticket_medio,
  ROUND(SUM(vl_pago_odisseia), 0) AS receita
FROM odi_compradores
GROUP BY 1 ORDER BY qt DESC
"""

# Corte próprio 2: recompra CDL -> Odisseia (o preditor que decide o próximo box)
Q_RECOMPRA_CDL = f"""
WITH {ODI_BASE},
cdl_compradores AS (
  SELECT DISTINCT dpi.id_person, MIN(t.dt_ordered_at) AS dt_compra_cdl
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = c.nm_email AND dpi.nm_identifier_type = 'email'
  WHERE t.nm_gateway_plan = 'clube-do-livro'
    AND t.nm_status = 'approved'
    AND t.nm_gateway_product IN (
      'Comercial - Clube do Livro','Comercial - Clube do Livro + Black',
      'Comercial - Clube do Livro + Black 18x','Comercial - Clube do Livro 18x',
      'Comercial - Clube do Livro [18x]','Comercial - Clube do Livro - Bronze 18x',
      'Brasil Paralelo - Clube do Livro','Clube do Livro - CS')
  GROUP BY 1
)
SELECT
  CASE WHEN c.id_person IS NOT NULL AND DATE(c.dt_compra_cdl) <= DATE(o.dt_compra_odi)
       THEN 'Comprou o CDL antes' ELSE 'Não comprou o CDL' END AS grupo,
  COUNT(*) AS qt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
  ROUND(AVG(o.vl_pago_odisseia), 0) AS ticket_medio
FROM odi_compradores o
LEFT JOIN cdl_compradores c USING (id_person)
GROUP BY 1 ORDER BY qt DESC
"""

# Interseção CDL × Odisseia — Venn por id_person (só CDL / só Odisseia / os dois)
Q_INTERSECAO = f"""
WITH {ODI_BASE},
cdl_compradores AS (
  SELECT dpi.id_person,
         MIN(t.dt_ordered_at)      AS dt_compra_cdl,
         SUM(t.vl_payment_gross)   AS vl_cdl
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = c.nm_email AND dpi.nm_identifier_type = 'email'
  WHERE t.nm_gateway_plan = 'clube-do-livro'
    AND t.nm_status = 'approved'
    AND t.nm_gateway_product IN (
      'Comercial - Clube do Livro','Comercial - Clube do Livro + Black',
      'Comercial - Clube do Livro + Black 18x','Comercial - Clube do Livro 18x',
      'Comercial - Clube do Livro [18x]','Comercial - Clube do Livro - Bronze 18x',
      'Brasil Paralelo - Clube do Livro','Clube do Livro - CS')
  GROUP BY 1
),
venn AS (
  SELECT
    COALESCE(c.id_person, o.id_person) AS id_person,
    CASE
      WHEN c.id_person IS NOT NULL AND o.id_person IS NOT NULL THEN 'Comprou os dois'
      WHEN c.id_person IS NOT NULL                             THEN 'Só Clube do Livro'
      ELSE                                                          'Só Odisseia'
    END AS grupo,
    COALESCE(c.vl_cdl, 0) + COALESCE(o.vl_pago_odisseia, 0) AS vl_livros
  FROM cdl_compradores c
  FULL OUTER JOIN odi_compradores o USING (id_person)
)
SELECT grupo,
       COUNT(*) AS qt,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
       ROUND(SUM(vl_livros), 0) AS receita,
       ROUND(AVG(vl_livros), 0) AS ticket_medio
FROM venn
GROUP BY 1
ORDER BY qt DESC
"""

# Base do CDL para calcular a taxa de recompra (denominador)
Q_BASE_CDL = """
SELECT COUNT(DISTINCT dpi.id_person) AS base_cdl
FROM `bp-datawarehouse.masterdata.fct_transactions` t
JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
  ON dpi.nm_identifier = c.nm_email AND dpi.nm_identifier_type = 'email'
WHERE t.nm_gateway_plan = 'clube-do-livro'
  AND t.nm_status = 'approved'
  AND t.nm_gateway_product IN (
    'Comercial - Clube do Livro','Comercial - Clube do Livro + Black',
    'Comercial - Clube do Livro + Black 18x','Comercial - Clube do Livro 18x',
    'Comercial - Clube do Livro [18x]','Comercial - Clube do Livro - Bronze 18x',
    'Brasil Paralelo - Clube do Livro','Clube do Livro - CS')
"""

# ── build ─────────────────────────────────────────────────────────────────────

def build() -> dict:
    print("  totais...", flush=True);            tot = bq(Q_TOTAIS)[0]
    print("  status de membro...", flush=True);  status_rows = bq(Q_STATUS)
    print("  antiguidade...", flush=True);       ant_rows = bq(Q_ANTIGUIDADE)
    print("  produtos anteriores...", flush=True); prod_rows = bq(Q_PRODUTOS_ANTES)
    print("  canal...", flush=True);             canal_rows = bq(Q_CANAL)
    print("  consumo histórico...", flush=True); cons = bq(Q_CONSUMO)[0]
    print("  tipo de produto...", flush=True);   tipo_rows = bq(Q_TIPO)
    print("  recompra CDL...", flush=True);      rec_rows = bq(Q_RECOMPRA_CDL)
    print("  interseção CDL x Odisseia...", flush=True); venn_rows = bq(Q_INTERSECAO)
    base_cdl = ii(bq(Q_BASE_CDL)[0]["base_cdl"])

    veio_do_cdl = next((ii(r["qt"]) for r in rec_rows if r["grupo"] == "Comprou o CDL antes"), 0)

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "totais": {
            "compradores":    ii(tot["compradores"]),
            "receita_total":  ii(tot["receita_total"]),
            "ticket_medio":   ii(tot["ticket_medio"]),
            "periodo_inicio": str(tot["periodo_inicio"]),
            "periodo_fim":    str(tot["periodo_fim"]),
        },
        "status": [{"label": r["status"], "qt": ii(r["qt"]), "pct": fi(r["pct"])} for r in status_rows],
        "antiguidade": [{"label": r["faixa"], "qt": ii(r["qt"]), "pct": fi(r["pct"]),
                         "media_dias": ii(r["media_dias"])} for r in ant_rows],
        "produtos_antes": [{"plano": r["nm_plan_label"], "compradores": ii(r["compradores"]),
                            "pct": fi(r["pct_base"])} for r in prod_rows],
        "canal": [{"canal": r["canal"], "qt": ii(r["qt"]), "pct": fi(r["pct"]),
                   "ticket_medio": ii(r["ticket_medio"]), "receita": ii(r["receita"])} for r in canal_rows],
        "consumo": {
            "gasto_medio":   ii(cons["gasto_medio"]),
            "mediana_gasto": ii(cons["mediana_gasto"]),
            "media_planos":  fi(cons["media_planos"]),
            "com_historico": ii(cons["com_historico"]),
        },
        "tipo": [{"label": r["tipo"], "qt": ii(r["qt"]), "pct": fi(r["pct"]),
                  "ticket_medio": ii(r["ticket_medio"]), "receita": ii(r["receita"])} for r in tipo_rows],
        "interseccao": {
            "grupos": [{"label": r["grupo"], "qt": ii(r["qt"]), "pct": fi(r["pct"]),
                        "receita": ii(r["receita"]), "ticket_medio": ii(r["ticket_medio"])} for r in venn_rows],
        },
        "recompra_cdl": {
            "grupos": [{"label": r["grupo"], "qt": ii(r["qt"]), "pct": fi(r["pct"]),
                        "ticket_medio": ii(r["ticket_medio"])} for r in rec_rows],
            "base_cdl": base_cdl,
            "veio_do_cdl": veio_do_cdl,
            "taxa_recompra": round(veio_do_cdl * 100.0 / base_cdl, 2) if base_cdl else 0.0,
        },
    }

# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing Odisseia report...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            repo = Path(__file__).parent.parent.parent
            subprocess.run(["git", "add", str(OUT)], check=True, cwd=repo)
            subprocess.run(["git", "commit", "-m", f"data: odisseia-perfil refresh {datetime.date.today()}"], check=True, cwd=repo)
            subprocess.run(["git", "push", "origin", "main"], check=True, cwd=repo)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
