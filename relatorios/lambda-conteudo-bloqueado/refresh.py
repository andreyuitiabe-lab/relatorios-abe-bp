#!/usr/bin/env python3
"""
Refresh — Lambda · Campanha Conteúdo Bloqueado.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Fontes: staging.int_pipedrive_analytics (lista CB via nm_title 'UPSELL |%'),
masterdata.fct_transactions + dim_contact (vendas por pessoa),
datamart.dtm_seller_conversion_rate (o que o funil mostra hoje).
Só agregados vão para o data.json — nunca PII (repo público).
"""

import json, subprocess, sys, datetime
from pathlib import Path

TAG = "LAMBDA-CB"
DT_INICIO = "2026-07-15"   # início da campanha (1ª venda C0113 da base)
OUT = Path(__file__).parent / "data.json"

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

# ─── fragmentos compartilhados ───────────────────────────────────────────────
CB_PESSOAS = """
cb_pessoas AS (
  SELECT LOWER(nm_person_email) email,
         REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]','') tel,
         MIN(dt_created_at) dt_entrou_lista
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics`
  WHERE nm_title LIKE 'UPSELL |%'
  GROUP BY 1, 2
)"""

# venda Lambda = link C0113 / produto/oferta lambda (regra canônica, wiki fluxo-comercial.md)
EH_LAMBDA = """COALESCE(
      UPPER(t.nm_pptc_tracking_name) LIKE '%C0113%'
      OR LOWER(t.nm_gateway_product) LIKE '%lambda%'
      OR LOWER(t.nm_gateway_offer) LIKE '%lambda%', FALSE)"""

VENDAS = f"""
vendas AS (
  SELECT t.id_transaction, t.dt_ordered_at, t.vl_payment_gross, t.nm_plan_label,
         t.bl_lifetime_offer, t.bl_is_commercial_channel,
         {EH_LAMBDA} AS eh_lambda,
         LOWER(c.nm_email) email,
         REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]','') tel
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at >= '{DT_INICIO}'
)"""

# match por email e telefone em joins separados (OR no ON vira cross-join)
MATCH = """
match AS (
  SELECT v.*, p.dt_entrou_lista
  FROM cb_pessoas p JOIN vendas v ON p.email = v.email AND p.email != ''
  UNION DISTINCT
  SELECT v.*, p.dt_entrou_lista
  FROM cb_pessoas p JOIN vendas v ON p.tel = v.tel AND p.tel != ''
),
m AS (
  SELECT * FROM match
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_transaction ORDER BY dt_entrou_lista) = 1
)"""

# ─── queries ─────────────────────────────────────────────────────────────────
Q_LOTES = """
SELECT DATE(dt_created_at) dia, COUNT(*) qt
FROM `bp-datawarehouse.staging.int_pipedrive_analytics`
WHERE nm_title LIKE 'UPSELL |%'
GROUP BY 1 ORDER BY 1
"""

Q_BASE = """
WITH p AS (
  SELECT DISTINCT LOWER(nm_person_email) email,
         REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]','') tel
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics`
  WHERE nm_title LIKE 'UPSELL |%'
)
SELECT COUNT(*) leads FROM p
"""

Q_DESFECHO = f"""
WITH {CB_PESSOAS}, {VENDAS}, {MATCH},
por_pessoa AS (
  SELECT COALESCE(email, tel) pessoa,
    COUNTIF(eh_lambda) qt_lambda,
    COUNTIF(NOT eh_lambda AND bl_is_commercial_channel) qt_com,
    COUNTIF(NOT eh_lambda AND NOT bl_is_commercial_channel) qt_dig,
    SUM(vl_payment_gross) vl
  -- só vendas APÓS a entrada na lista (pedido de 30/jul)
  FROM m WHERE dt_ordered_at >= dt_entrou_lista GROUP BY 1
)
SELECT
  CASE WHEN qt_lambda > 0 THEN 'lambda'
       WHEN qt_com > 0 THEN 'outro_comercial'
       ELSE 'digital' END desfecho,
  COUNT(*) pessoas,
  SUM(qt_lambda + qt_com + qt_dig) vendas,
  ROUND(SUM(vl), 2) valor
FROM por_pessoa GROUP BY 1
"""

Q_LAMBDA_DIA = f"""
WITH {CB_PESSOAS}, {VENDAS}, {MATCH}
SELECT DATE(dt_ordered_at) dia, COUNT(*) qt, ROUND(SUM(vl_payment_gross), 2) vl
FROM m WHERE eh_lambda AND dt_ordered_at >= dt_entrou_lista GROUP BY 1 ORDER BY 1
"""

Q_LAMBDA_PLANO = f"""
WITH {CB_PESSOAS}, {VENDAS}, {MATCH}
SELECT nm_plan_label plano, COUNT(*) qt, ROUND(SUM(vl_payment_gross), 2) vl
FROM m WHERE eh_lambda AND dt_ordered_at >= dt_entrou_lista GROUP BY 1 ORDER BY vl DESC
"""

Q_TIMING = f"""
WITH {CB_PESSOAS}, {VENDAS}, {MATCH}
SELECT
  IF(eh_lambda, 'lambda', IF(bl_is_commercial_channel, 'comercial', 'digital')) canal,
  IF(dt_ordered_at >= dt_entrou_lista, 'depois', 'antes') timing,
  COUNT(*) qt, ROUND(SUM(vl_payment_gross), 2) vl,
  COUNTIF(bl_lifetime_offer) vitalicios
FROM m GROUP BY 1, 2
"""

# vendas pós-lista do comercial humano: quantas tinham abordagem anterior à lista
# (deal aberto de outro vendedor OU abordagem Zenvia iniciada antes da entrada)
Q_ABORDAGEM_PREVIA = f"""
WITH {CB_PESSOAS}, {VENDAS}, {MATCH},
pos AS (
  SELECT * FROM m
  WHERE NOT eh_lambda AND bl_is_commercial_channel AND dt_ordered_at >= dt_entrou_lista
),
previa AS (
  SELECT DISTINCT pos.id_transaction
  FROM pos
  JOIN `bp-datawarehouse.staging.int_pipedrive_analytics` d
    ON (LOWER(d.nm_person_email) = pos.email OR d.cd_person_cleaned_phone_number = pos.tel)
  WHERE d.nm_title NOT LIKE 'UPSELL |%'
    AND d.dt_created_at < pos.dt_entrou_lista
    AND COALESCE(d.dt_closed_at, CURRENT_DATETIME()) >= pos.dt_entrou_lista
  UNION DISTINCT
  SELECT DISTINCT pos.id_transaction
  FROM pos
  JOIN `bp-datawarehouse.datamart.dtm_sales_by_zenvia` z
    ON z.cd_cleaned_phone_number = pos.tel AND pos.tel != ''
  WHERE z.dt_approach_start < pos.dt_entrou_lista
    AND z.dt_approach_start >= pos.dt_entrou_lista - INTERVAL 60 DAY
)
SELECT
  COUNT(*) total_pos_lista,
  COUNTIF(id_transaction IN (SELECT id_transaction FROM previa)) com_abordagem_previa,
  ROUND(SUM(vl_payment_gross), 2) vl_pos_lista
FROM pos
"""

# cenário da base no momento da entrada na lista: flags (com sobreposição) +
# corte exclusivo por prioridade (abordagem humana > lista Lambda > compra 7d > zumbi > limpo)
Q_CENARIO = """
WITH cb AS (
  SELECT LOWER(nm_person_email) email,
         REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]','') tel,
         MIN(dt_created_at) dt_entrou
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics`
  WHERE nm_title LIKE 'UPSELL |%'
  GROUP BY 1,2
),
cbp AS (
  SELECT COALESCE(NULLIF(email,''), tel) pessoa, email, tel, dt_entrou FROM cb
),
outros_deals AS (
  SELECT LOWER(d.nm_person_email) email,
         REGEXP_REPLACE(d.cd_person_cleaned_phone_number, r'[^0-9]','') tel,
         d.dt_created_at, d.dt_closed_at,
         IF(d.nm_salesman_email = 'gustavo.koetz@brasilparalelo.com.br'
            OR d.nm_stage = '10. AWSALES LISTA', 'lambda', 'humano') tipo
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics` d
  WHERE d.nm_title NOT LIKE 'UPSELL |%'
),
deals_abertos AS (
  SELECT p.pessoa, d.tipo,
         d.dt_created_at >= p.dt_entrou - INTERVAL 60 DAY AS recente
  FROM cbp p JOIN outros_deals d ON p.email = d.email AND p.email != ''
  WHERE d.dt_created_at < p.dt_entrou
    AND COALESCE(d.dt_closed_at, DATETIME '9999-01-01') >= p.dt_entrou
  UNION DISTINCT
  SELECT p.pessoa, d.tipo,
         d.dt_created_at >= p.dt_entrou - INTERVAL 60 DAY
  FROM cbp p JOIN outros_deals d ON p.tel = d.tel AND p.tel != ''
  WHERE d.dt_created_at < p.dt_entrou
    AND COALESCE(d.dt_closed_at, DATETIME '9999-01-01') >= p.dt_entrou
),
-- conversa aberta = contato Zenvia em followUp no grupo Comercial (definição de
-- negócio, 30/jul). dim_zenvia_contacts é estado ATUAL do contato, não o do dia
-- da entrada — aceito como aproximação; TRIM: nm_group tem espaço à direita.
zenvia_followup AS (
  SELECT DISTINCT p.pessoa
  FROM cbp p JOIN `bp-datawarehouse.masterdata.dim_zenvia_contacts` z
    ON z.cd_cleaned_phone_number = p.tel AND p.tel != ''
  WHERE z.nm_status = 'followUp' AND TRIM(z.nm_group) = 'Comercial'
),
tx AS (
  SELECT t.dt_ordered_at, LOWER(c.nm_email) email,
         REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]','') tel
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at >= '2026-06-01'
),
compra_7d AS (
  SELECT DISTINCT p.pessoa FROM cbp p JOIN tx ON p.email = tx.email AND p.email != ''
  WHERE tx.dt_ordered_at >= p.dt_entrou - INTERVAL 7 DAY AND tx.dt_ordered_at < p.dt_entrou
  UNION DISTINCT
  SELECT DISTINCT p.pessoa FROM cbp p JOIN tx ON p.tel = tx.tel AND p.tel != ''
  WHERE tx.dt_ordered_at >= p.dt_entrou - INTERVAL 7 DAY AND tx.dt_ordered_at < p.dt_entrou
),
flags AS (
  SELECT
    p.pessoa,
    p.pessoa IN (SELECT pessoa FROM deals_abertos WHERE tipo = 'lambda') AS f_lambda,
    p.pessoa IN (SELECT pessoa FROM deals_abertos WHERE tipo = 'humano' AND recente) AS f_humano_60d,
    p.pessoa IN (SELECT pessoa FROM deals_abertos WHERE tipo = 'humano' AND NOT recente) AS f_humano_antigo,
    p.pessoa IN (SELECT pessoa FROM zenvia_followup) AS f_zenvia,
    p.pessoa IN (SELECT pessoa FROM compra_7d) AS f_compra7
  FROM cbp p
)
SELECT
  COUNT(*) base,
  COUNTIF(f_lambda) outra_lista_lambda,
  COUNTIF(f_humano_60d OR f_zenvia) abordagem_humana_ativa,
  COUNTIF(f_humano_antigo) deal_humano_zumbi,
  COUNTIF(f_compra7) comprou_7d_antes,
  COUNTIF(f_humano_60d OR f_zenvia) ex_abordagem_humana,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND f_lambda) ex_outra_lista_lambda,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND NOT f_lambda AND f_compra7) ex_comprou_7d,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND NOT f_lambda AND NOT f_compra7 AND f_humano_antigo) ex_deal_zumbi,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND NOT f_lambda AND NOT f_compra7 AND NOT f_humano_antigo) ex_limpo
FROM flags
"""

# o que o funil (dtm_seller_conversion_rate) mostra hoje para a campanha
Q_DASH_HOJE = """
WITH cb AS (
  SELECT ct.id_transaction, ct.vl_payment_gross
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate` m,
    UNNEST(m.arr_st_commercial_transactions) ct
  WHERE m.nm_label = 'Conteúdo bloqueado' OR m.nm_deal_source = 'Conteúdo bloqueado'
)
SELECT COUNT(DISTINCT id_transaction) qt, ROUND(SUM(vl_payment_gross), 2) vl
FROM cb
"""

# ─── build ───────────────────────────────────────────────────────────────────
def build() -> dict:
    print("  lotes da lista...", flush=True)
    lotes = bq(Q_LOTES)
    print("  base...", flush=True)
    base = bq(Q_BASE)[0]
    print("  desfecho por pessoa...", flush=True)
    desf = {r["desfecho"]: r for r in bq(Q_DESFECHO)}
    print("  vendas lambda por dia...", flush=True)
    ldia = bq(Q_LAMBDA_DIA)
    print("  vendas lambda por plano...", flush=True)
    lplano = bq(Q_LAMBDA_PLANO)
    print("  timing por canal...", flush=True)
    timing = {(r["canal"], r["timing"]): r for r in bq(Q_TIMING)}
    print("  abordagem prévia (pós-lista)...", flush=True)
    previa = bq(Q_ABORDAGEM_PREVIA)[0]
    print("  cenário na geração...", flush=True)
    cen = bq(Q_CENARIO)[0]
    print("  funil hoje (dtm_seller_conversion_rate)...", flush=True)
    dash = bq(Q_DASH_HOJE)[0]

    leads = ii(base["leads"])
    compraram = sum(ii(v["pessoas"]) for v in desf.values())

    def tget(canal, quando):
        r = timing.get((canal, quando), {})
        return {"qt": ii(r.get("qt")), "vl": fi(r.get("vl")), "vitalicios": ii(r.get("vitalicios"))}

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "periodo_inicio": DT_INICIO,
        "base": {"leads": leads, "sem_compra": leads - compraram},
        "lotes": {
            "labels": [str(r["dia"]) for r in lotes],
            "qt": [ii(r["qt"]) for r in lotes],
        },
        "desfecho": {
            k: {"pessoas": ii(v["pessoas"]), "vendas": ii(v["vendas"]), "valor": fi(v["valor"])}
            for k, v in desf.items()
        },
        "lambda_dia": {
            "labels": [str(r["dia"]) for r in ldia],
            "qt": [ii(r["qt"]) for r in ldia],
            "vl": [fi(r["vl"]) for r in ldia],
        },
        "lambda_planos": [
            {"plano": r["plano"], "qt": ii(r["qt"]), "vl": fi(r["vl"])} for r in lplano
        ],
        "timing": {
            "comercial": {"antes": tget("comercial", "antes"), "depois": tget("comercial", "depois")},
            "digital":   {"antes": tget("digital", "antes"),   "depois": tget("digital", "depois")},
        },
        "pos_lista": {
            "total": ii(previa["total_pos_lista"]),
            "com_abordagem_previa": ii(previa["com_abordagem_previa"]),
            "vl": fi(previa["vl_pos_lista"]),
        },
        "dash_hoje": {"qt": ii(dash["qt"]), "vl": fi(dash["vl"])},
        "cenario": {
            "base": ii(cen["base"]),
            "flags": {
                "abordagem_humana_ativa": ii(cen["abordagem_humana_ativa"]),
                "outra_lista_lambda": ii(cen["outra_lista_lambda"]),
                "comprou_7d_antes": ii(cen["comprou_7d_antes"]),
                "deal_humano_zumbi": ii(cen["deal_humano_zumbi"]),
            },
            "exclusivo": {
                "abordagem_humana": ii(cen["ex_abordagem_humana"]),
                "outra_lista_lambda": ii(cen["ex_outra_lista_lambda"]),
                "comprou_7d": ii(cen["ex_comprou_7d"]),
                "deal_zumbi": ii(cen["ex_deal_zumbi"]),
                "limpo": ii(cen["ex_limpo"]),
            },
        },
    }

# ─── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    push = "--push" in sys.argv
    print(f"Refreshing {TAG} report data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: {TAG} refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
