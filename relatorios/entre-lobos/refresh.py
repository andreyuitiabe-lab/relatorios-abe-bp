#!/usr/bin/env python3
"""
Refresh report data from BigQuery — ELB26 (relançamento Entre Lobos): sementes lookalike.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

TAG = "ELB26"
OUT = Path(__file__).parent / "data.json"

# ─── BQ helper ───────────────────────────────────────────────────────────────
def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    # via stdin: comentários '--' no início do SQL quebram o parse de flags do bq
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         "--project_id=bp-datawarehouse", f"--max_rows={max_rows}"],
        input=sql, capture_output=True, text=True
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
Q_SEMENTES = (Path(__file__).parent / "queries" / "elb26_sementes_lookalike.sql").read_text()
Q_SOCIO = (Path(__file__).parent / "queries" / "elb26_perfil_socio_expandido.sql").read_text()

SOCIO_LABELS = {
    "1_compradores_elb22":       "Compradores ELB 2022",
    "2_compradores_elb24":       "Compradores ELB 2024",
    "3_conversos_leads_elb24":   "Conversos de leads ELB24",
    "4_viewers_serie_principal": "Viewers série principal",
    "5_viewers_parte1_2023":     "Viewers Parte I (2023)",
    "6_viewers_entrevistas":     "Viewers entrevistas (superfãs)",
    "7_viewers_producao_2026":   "Viewers produção 2026",
    "8_compradores_els":         "Compradores ELS",
    "9_leads_aa_elb26":          "Leads A+/A ELB26 (IQL)",
}
# grupo de cada segmento: c = comprador de campanha, v = viewer, f = funil de lead
SOCIO_GRUPOS = {
    "1_compradores_elb22": "c", "2_compradores_elb24": "c", "8_compradores_els": "c",
    "4_viewers_serie_principal": "v", "5_viewers_parte1_2023": "v",
    "6_viewers_entrevistas": "v", "7_viewers_producao_2026": "v",
    "3_conversos_leads_elb24": "f", "9_leads_aa_elb26": "f",
}

Q_LEADS_DIA = f"""
SELECT DATE(ts_registered_at) AS dia, COUNT(*) AS leads
FROM `bp-lake.marketing.lead_registration`
WHERE nm_tag = "{TAG}"
GROUP BY 1 ORDER BY 1
"""

# Rótulos de exibição das sementes (mesma ordem/chave do SQL)
SEMENTES_LABELS = {
    "1_compradores_elb22":   "Compradores ELB 2022",
    "2_viewers_elb_todos":   "Viewers da série (todos, ≥5min)",
    "3_viewers_elb_12m":     "Viewers últimos 12 meses",
    "4_viewers_elb_1h_mais": "Viewers ≥1h de watch time",
    "5_compradores_els":     "Compradores ELS",
    "6_els_x_viewers_elb":   "Compradores ELS ∩ viewers ELB",
    "7_leads_aa_elb26":      "Leads A+/A do ELB26 (IQL)",
}

# IQL do ELB26 — agregados por faixa e por dia.
# Governança D20: repo público só recebe agregados (faixa/%), nunca pontos ou pesos.
# ⚠️ pré-merge (MR !2426) o fct_lead_iql atualiza só com dbt run manual — ver iql.md.
Q_IQL_FAIXAS = """
SELECT
  nm_iql_band AS faixa,
  COUNT(*) AS n,
  ROUND(100 * COUNTIF(qt_sales > 0) / COUNT(*), 2) AS pct_conv
FROM `bp-staging.dbt_abe.fct_lead_iql`
WHERE nm_tag = 'ELB26'
GROUP BY 1 ORDER BY 1
"""

Q_IQL_DIA = """
SELECT
  DATE(dt_registered_at_br) AS dia,
  COUNT(*) AS leads,
  ROUND(COUNTIF(nm_iql_band IN ('A+', 'A')) / COUNT(*) * 100, 1) AS pct_aa
FROM `bp-staging.dbt_abe.fct_lead_iql`
WHERE nm_tag = 'ELB26'
GROUP BY 1 ORDER BY 1
"""

# Perfil do espectador da produção 2026 (padrão do relatório el-salvador):
# novos viewers/dia, plano de assinatura, % membros ativos, % novos da campanha, score de upsell ML.
Q_V26_DIA = """
WITH v AS (
  SELECT LOWER(nm_email) AS email, MIN(DATE(dt_created_at)) AS dia
  FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
  WHERE nm_playlist LIKE 'Entre Lobos 2026%' AND nm_email IS NOT NULL
  GROUP BY 1
  HAVING SUM(vl_watch_time_seconds) >= 300
)
SELECT dia, COUNT(*) AS novos FROM v GROUP BY 1 ORDER BY 1
"""

Q_V26_PLANO = """
WITH v AS (
  SELECT LOWER(nm_email) AS email
  FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
  WHERE nm_playlist LIKE 'Entre Lobos 2026%' AND nm_email IS NOT NULL
  GROUP BY 1
  HAVING SUM(vl_watch_time_seconds) >= 300
),
u AS (
  SELECT LOWER(nm_email) AS email, MAX(id_user) AS id_user
  FROM `bp-datawarehouse.masterdata.dim_user`
  WHERE nm_email IS NOT NULL GROUP BY 1
),
s AS (
  SELECT id_user, nm_plan_label, nm_gateway_status,
    MIN(dt_started_at) OVER (PARTITION BY id_user) AS primeira_assinatura
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_user ORDER BY dt_started_at DESC) = 1
)
SELECT
  COALESCE(s.nm_plan_label, 'Sem assinatura') AS plano,
  COUNT(*) AS n,
  COUNTIF(s.nm_gateway_status = 'active') AS ativos,
  COUNTIF(DATE(s.primeira_assinatura) >= '2026-07-14') AS novos_campanha
FROM v
JOIN u USING (email)
LEFT JOIN s USING (id_user)
GROUP BY 1 ORDER BY n DESC
"""

Q_V26_UPSELL = """
WITH v26 AS (
  SELECT LOWER(nm_email) AS email, 'producao_2026' AS grupo
  FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
  WHERE nm_playlist LIKE 'Entre Lobos 2026%' AND nm_email IS NOT NULL
  GROUP BY 1 HAVING SUM(vl_watch_time_seconds) >= 300
),
vserie AS (
  SELECT LOWER(nm_email) AS email, 'serie_principal' AS grupo
  FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
  WHERE nm_playlist = 'Entre Lobos' AND nm_email IS NOT NULL
  GROUP BY 1 HAVING SUM(vl_watch_time_seconds) >= 300
),
g AS (SELECT * FROM v26 UNION ALL SELECT * FROM vserie),
u AS (
  SELECT LOWER(nm_email) AS email, MAX(id_user) AS id_user
  FROM `bp-datawarehouse.masterdata.dim_user`
  WHERE nm_email IS NOT NULL GROUP BY 1
)
SELECT g.grupo,
  COUNT(*) AS n_com_score,
  ROUND(AVG(p.cd_percentile_y_predicted_probabilities), 1) AS percentil_medio,
  ROUND(COUNTIF(p.cd_percentile_y_predicted_probabilities >= 80) / COUNT(*) * 100, 1) AS pct_top20
FROM g
JOIN u USING (email)
JOIN `bp-datawarehouse.ml_models.dtm_lead_score_predictions_upsell_current` p USING (id_user)
WHERE p.nm_target_variable = 'upsell_in_30_days'
GROUP BY 1
"""

# Mídia Meta ELB26 por dia/fase — alimenta o estado dinâmico da campanha e o CPL/CPLq
Q_MIDIA = """
SELECT reference_date AS dia,
  IF(nm_campaign_name LIKE '%[VENDA]%', 'venda', 'lead') AS fase,
  ROUND(SUM(vl_amount_spent)) AS spend,
  SUM(qt_total_sales) AS vendas
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE reference_date >= '2026-07-14'
  AND REGEXP_CONTAINS(LOWER(nm_campaign_name), r'(^|[^a-z])elb(26)?([^a-z0-9]|$)|entre[-_ ]?lobos')
GROUP BY 1, 2 ORDER BY 1
"""

# Sobreposição entre as sementes da arquitetura (base: tb_elb26_segmentos, snapshot 31/07)
Q_OVERLAP = """
WITH sementes AS (
  SELECT 'Compradores ELS' AS semente, email
  FROM `bp-staging.dbt_abe.tb_elb26_segmentos` WHERE segmento = '8_compradores_els'
  UNION ALL
  SELECT 'Compradores ELB22', email
  FROM `bp-staging.dbt_abe.tb_elb26_segmentos` WHERE segmento = '1_compradores_elb22'
  UNION ALL
  SELECT 'Conversor de funil', email
  FROM `bp-staging.dbt_abe.tb_elb26_segmentos`
  WHERE segmento IN ('9_leads_aa_elb26', '3_conversos_leads_elb24')
),
dedup AS (SELECT DISTINCT semente, email FROM sementes)
SELECT a.semente AS de, b.semente AS para,
  COUNT(DISTINCT a.email) AS n_de,
  COUNT(DISTINCT IF(b2.email IS NOT NULL, a.email, NULL)) AS n_overlap
FROM dedup a
CROSS JOIN (SELECT DISTINCT semente FROM dedup) b
LEFT JOIN dedup b2 ON b2.semente = b.semente AND b2.email = a.email
WHERE a.semente != b.semente
GROUP BY 1, 2
"""

# Forecast de cenários da venda: leads × R$/lead blended de campanhas de aquisição
# (coeficientes medidos em relatorios/aquecimento-vendas — receita total da campanha ÷ leads de aquecimento)
FORECAST_COEF = [
    {"cenario": "Conservador", "ancora": "DOM",  "coef": 14.8},
    {"cenario": "Central",     "ancora": "ELS",  "coef": 47.5},
    {"cenario": "Otimista",    "ancora": "ODD",  "coef": 110.3},
]

# Benchmark fixo: testes de segmentação da fase [VENDA] do ELS, comparados com o Advantage
# NA MESMA JANELA de spend do teste (+7d de cauda) — correção de 30/07 (ver els-analise.md).
# Os testes foram rajadas de 2–13 dias numa curva que decai 4,8→1,6; comparar com o agregado
# (1,40) era injusto. Atribuição pixel Meta (facebook_ads_funnel), não o modelo interno.
BENCH_ELS = [
    {"nome": "Carrinho abandonado",     "janela": "21–31/05", "spend": "R$ 1,5k",  "roas": 2.72, "adv": 1.52, "nota": "n=13, anedótico"},
    {"nome": "Sinal forte",             "janela": "21–29/05", "spend": "R$ 15k",   "roas": 1.98, "adv": 1.59, "nota": "+25%"},
    {"nome": "LKL compradores ELS",     "janela": "29–31/05", "spend": "R$ 27,5k", "roas": 1.64, "adv": 1.34, "nota": "+22%"},
    {"nome": "LKL 1% genérico",         "janela": "08–20/06", "spend": "R$ 34,5k", "roas": 0.97, "adv": 1.15, "nota": "−16%"},
    {"nome": "LKL viewers do doc",      "janela": "03–09/06", "spend": "R$ 52,8k", "roas": 0.91, "adv": 1.05, "nota": "−13% — o 1,68 antigo era outlier Comercial de R$40k"},
    {"nome": "Remarketing Viu o Doc",   "janela": "29–30/05", "spend": "R$ 2,1k",  "roas": 0.0,  "adv": 1.38, "nota": "zero vendas"},
]

# ─── build ───────────────────────────────────────────────────────────────────
def build() -> dict:
    print("  sementes (perfil + tamanho)...", flush=True)
    rows = {r["segmento"]: r for r in bq(Q_SEMENTES)}
    sementes = []
    for key, label in SEMENTES_LABELS.items():
        r = rows.get(key)
        if not r:
            continue
        sementes.append({
            "key": key,
            "label": label,
            "n": ii(r["n"]),
            "decil": fi(r["decil_medio"]),
            "decil7": fi(r["pct_decil7mais"]),
            "premium": fi(r["pct_cartao_premium"]),
            "masc": fi(r["pct_masc"]),
            "n_decil7": ii(r["n_decil7mais"]),
            "n_premium": ii(r["n_cartao_premium"]),
        })

    print("  perfil socioeconômico completo...", flush=True)
    socio_rows = {r["segmento"]: r for r in bq(Q_SOCIO)}
    FLOAT_KEYS = ["decil_medio", "pct_decil7", "renda_pc_mediana", "cob_renda",
                  "pct_black", "pct_plat_amex", "pct_gold", "pct_basico", "cob_cartao",
                  "pct_masc", "idade_media", "pct_14_29", "pct_30_44", "pct_45_59",
                  "pct_60_mais", "cob_idade", "pct_sudeste", "pct_sul", "pct_nordeste",
                  "pct_centrooeste", "pct_norte", "pct_capital", "pct_cid_grande",
                  "pct_cid_pequena", "cob_geo"]
    perfil_socio = []
    for key, label in SOCIO_LABELS.items():
        r = socio_rows.get(key)
        if not r:
            continue
        perfil_socio.append({"key": key, "label": label, "grupo": SOCIO_GRUPOS[key],
                             "n": ii(r["n"]),
                             **{k: fi(r[k]) for k in FLOAT_KEYS if k in r}})

    print("  leads ELB26 por dia...", flush=True)
    leads_rows = bq(Q_LEADS_DIA)

    print("  perfil do espectador (produção 2026)...", flush=True)
    v26_dia = bq(Q_V26_DIA)
    v26_plano = bq(Q_V26_PLANO)
    v26_upsell = {r["grupo"]: r for r in bq(Q_V26_UPSELL)}
    total_v26 = sum(ii(r["n"]) for r in v26_plano)
    espectador = {
        "total": total_v26,
        "ativos": sum(ii(r["ativos"]) for r in v26_plano),
        "novos_campanha": sum(ii(r["novos_campanha"]) for r in v26_plano),
        "dia": {
            "labels": [str(r["dia"]) for r in v26_dia],
            "novos": [ii(r["novos"]) for r in v26_dia],
        },
        "planos": [
            {"plano": r["plano"], "n": ii(r["n"]), "ativos": ii(r["ativos"])}
            for r in v26_plano[:8]
        ],
        "outros_planos": sum(ii(r["n"]) for r in v26_plano[8:]),
        "upsell": {
            g: {"n": ii(r["n_com_score"]), "percentil_medio": fi(r["percentil_medio"]),
                "pct_top20": fi(r["pct_top20"])}
            for g, r in v26_upsell.items()
        },
    }

    print("  IQL ELB26 (faixas + diário)...", flush=True)
    iql_faixas = bq(Q_IQL_FAIXAS)
    iql_dia = bq(Q_IQL_DIA)
    ordem = ["A+", "A", "B", "C", "D"]
    faixas = sorted(iql_faixas, key=lambda r: ordem.index(r["faixa"]))
    total_iql = sum(ii(r["n"]) for r in faixas)
    n_aa = sum(ii(r["n"]) for r in faixas if r["faixa"] in ("A+", "A"))

    # governança D20: garantir que só agregados vão ao repo público
    assert all(set(r.keys()) <= {"faixa", "n", "pct_conv"} for r in iql_faixas)
    assert all(set(r.keys()) <= {"dia", "leads", "pct_aa"} for r in iql_dia)

    print("  mídia por fase + overlap de sementes...", flush=True)
    midia_rows = bq(Q_MIDIA)
    dias_midia = sorted({str(r["dia"]) for r in midia_rows})
    midia = {
        "labels": dias_midia,
        "spend_lead":  [sum(fi(r["spend"]) for r in midia_rows if str(r["dia"]) == d and r["fase"] == "lead") for d in dias_midia],
        "spend_venda": [sum(fi(r["spend"]) for r in midia_rows if str(r["dia"]) == d and r["fase"] == "venda") for d in dias_midia],
        "vendas":      [sum(ii(r["vendas"]) for r in midia_rows if str(r["dia"]) == d) for d in dias_midia],
    }
    spend_lead_total = sum(midia["spend_lead"]) + sum(midia["spend_venda"])  # aquecimento: tudo pré-venda
    total_leads = sum(ii(r["leads"]) for r in leads_rows)
    custo = {
        "spend_lead_total": round(spend_lead_total),
        "cpl": round(spend_lead_total / total_leads, 2) if total_leads else None,
        "cplq": round(spend_lead_total / n_aa, 2) if n_aa else None,
        "nota": "CPL blendado: spend Meta ELB26 ÷ todos os leads da tag (inclui orgânico/CRM). "
                "CPLq = mesmo spend ÷ leads A+/A escorados.",
    }
    overlap_rows = bq(Q_OVERLAP)
    overlap = [
        {"de": r["de"], "para": r["para"], "n_de": ii(r["n_de"]),
         "pct": round(ii(r["n_overlap"]) / ii(r["n_de"]) * 100, 1) if ii(r["n_de"]) else 0}
        for r in overlap_rows
    ]
    forecast = [
        {**f, "receita": round(total_leads * f["coef"] / 1e6, 2)} for f in FORECAST_COEF
    ]

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "campaign": TAG,
        "sementes": sementes,
        "leads_dia": {
            "labels": [str(r["dia"]) for r in leads_rows],
            "leads":  [ii(r["leads"]) for r in leads_rows],
        },
        "total_leads": total_leads,
        "midia": midia,
        "custo": custo,
        "overlap": overlap,
        "forecast": forecast,
        "bench_els": BENCH_ELS,
        "perfil_socio": perfil_socio,
        "espectador": espectador,
        "iql": {
            "updated_ref": max((str(r["dia"]) for r in iql_dia), default=None),
            "total_escorados": total_iql,
            "n_aa": n_aa,
            "pct_aa": round(n_aa / total_iql * 100, 1) if total_iql else 0,
            "faixas": {
                "labels": [r["faixa"] for r in faixas],
                "n": [ii(r["n"]) for r in faixas],
                "conv": [fi(r["pct_conv"]) for r in faixas],
            },
            "dia": {
                "labels": [str(r["dia"]) for r in iql_dia],
                "pct_aa": [fi(r["pct_aa"]) for r in iql_dia],
                "leads": [ii(r["leads"]) for r in iql_dia],
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
