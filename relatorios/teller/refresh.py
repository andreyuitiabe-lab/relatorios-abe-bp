#!/usr/bin/env python3
"""
Refresh dos dados do relatório Teller a partir do BigQuery.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Escopo produto = nm_gateway_plan='teller' (standalone; SEM premium-teller / bundles).
Escopo campanha = nm_pptc_utm_campaign com tag TLR/TLR12.
"""

import json, subprocess, sys, datetime, math
from pathlib import Path

OUT = Path(__file__).parent / "data.json"
START = "2026-01-01"

def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         "--project_id=bp-datawarehouse", f"--max_rows={max_rows}", sql],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    out = r.stdout.strip()
    return json.loads(out) if out else []

def ii(v):
    try: return int(v) if v not in (None, "", "null") else 0
    except: return 0
def fi(v):
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def pearson(x, y):
    n = len(x)
    if n < 2: return 0.0
    mx, my = sum(x)/n, sum(y)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(x, y))
    sxx = sum((a-mx)**2 for a in x)
    syy = sum((b-my)**2 for b in y)
    if sxx == 0 or syy == 0: return 0.0
    return sxy / math.sqrt(sxx*syy)

# ─── queries ─────────────────────────────────────────────────────────────────
Q_VENDAS_PRODUTO = f"""
SELECT FORMAT_DATE('%Y-%m', DATE(dt_ordered_at)) mes,
       COUNT(*) n, ROUND(SUM(vl_payment_gross)) receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='{START}'
  AND nm_gateway_plan='teller'
GROUP BY 1 ORDER BY 1
"""

# Campanhas TLR recortadas pelo PERFIL REAL do comprador no momento da compra
# (não pelo nome do UTM — o nome reflete intenção do Marketing, não quem comprou)
Q_VENDAS_CAMPANHA = f"""
WITH camp AS (
  SELECT id_gateway_customer, dt_ordered_at, FORMAT_DATE('%Y-%m', DATE(dt_ordered_at)) mes
  FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='{START}'
    AND REGEXP_CONTAINS(LOWER(nm_pptc_utm_campaign), r'(^|[^a-z])tlr([^a-z]|$)|tlr12')
),
subs AS (SELECT id_gateway_customer,dt_started_at,dt_expires_in FROM masterdata.dim_subscriptions WHERE nm_type='paid' AND (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%')),
vital AS (SELECT DISTINCT id_gateway_customer,dt_ordered_at dt_vital FROM masterdata.fct_transactions WHERE nm_status='approved' AND bl_lifetime_offer AND LOWER(nm_gateway_product) NOT LIKE '%teller%')
SELECT c.mes,
  CASE WHEN (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=c.id_gateway_customer AND s.dt_started_at<c.dt_ordered_at AND s.dt_expires_in>=c.dt_ordered_at)>0
            OR (SELECT COUNT(1) FROM vital v WHERE v.id_gateway_customer=c.id_gateway_customer AND v.dt_vital<c.dt_ordered_at)>0 THEN 'membro'
       WHEN (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=c.id_gateway_customer AND s.dt_started_at<c.dt_ordered_at)>0 THEN 'ex_membro'
       ELSE 'nao_membro' END perfil,
  COUNT(*) n
FROM camp c GROUP BY 1,2 ORDER BY 1,2
"""

Q_PERFIL = f"""
WITH tb AS (SELECT id_gateway_customer, MIN(dt_ordered_at) dt_teller FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='{START}' AND nm_gateway_plan='teller' GROUP BY 1),
subs AS (SELECT id_gateway_customer,dt_started_at,dt_expires_in FROM masterdata.dim_subscriptions
         WHERE nm_type='paid' AND (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%')),
vital AS (SELECT DISTINCT id_gateway_customer,dt_ordered_at dt_vital FROM masterdata.fct_transactions
          WHERE nm_status='approved' AND bl_lifetime_offer AND LOWER(nm_gateway_product) NOT LIKE '%teller%')
SELECT CASE WHEN via.via_com THEN 'comercial' ELSE 'digital' END canal,
  CASE WHEN (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=tb.id_gateway_customer AND s.dt_started_at<dt_teller AND s.dt_expires_in>=dt_teller)>0
            OR (SELECT COUNT(1) FROM vital v WHERE v.id_gateway_customer=tb.id_gateway_customer AND v.dt_vital<dt_teller)>0 THEN 'membro'
       WHEN (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=tb.id_gateway_customer AND s.dt_started_at<dt_teller)>0 THEN 'ex_membro'
       ELSE 'nao_membro' END perfil,
  COUNT(*) compradores
FROM tb
JOIN (SELECT id_gateway_customer, MAX(bl_is_commercial_channel) via_com FROM masterdata.fct_transactions
      WHERE nm_gateway_plan='teller' AND dt_ordered_at>='{START}' GROUP BY 1) via USING(id_gateway_customer)
GROUP BY 1,2 ORDER BY 1,2
"""

Q_TIER_MEMBROS = f"""
WITH tb AS (SELECT id_gateway_customer, dt_ordered_at FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='{START}' AND nm_gateway_plan='teller')
SELECT s.nm_gateway_plan tier, COUNT(DISTINCT tb.id_gateway_customer) membros
FROM tb JOIN masterdata.dim_subscriptions s
  ON s.id_gateway_customer=tb.id_gateway_customer AND s.nm_type='paid'
 AND (s.nm_gateway_plan IS NULL OR s.nm_gateway_plan NOT LIKE '%teller%')
 AND s.dt_started_at<tb.dt_ordered_at AND s.dt_expires_in>=tb.dt_ordered_at
GROUP BY 1 ORDER BY membros DESC LIMIT 8
"""

Q_FUNIL_NM = f"""
WITH tb AS (SELECT id_gateway_customer, MIN(dt_ordered_at) dt_teller FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='{START}' AND nm_gateway_plan='teller' GROUP BY 1),
subs AS (SELECT id_gateway_customer,dt_started_at,dt_expires_in FROM masterdata.dim_subscriptions WHERE nm_type='paid' AND (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%')),
vital AS (SELECT DISTINCT id_gateway_customer,dt_ordered_at dt_vital FROM masterdata.fct_transactions WHERE nm_status='approved' AND bl_lifetime_offer AND LOWER(nm_gateway_product) NOT LIKE '%teller%'),
nm AS (SELECT tb.id_gateway_customer, dt_teller FROM tb
  WHERE (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=tb.id_gateway_customer AND s.dt_started_at<dt_teller)=0
    AND (SELECT COUNT(1) FROM vital v WHERE v.id_gateway_customer=tb.id_gateway_customer AND v.dt_vital<dt_teller)=0),
conv AS (SELECT DISTINCT nm.id_gateway_customer FROM nm JOIN masterdata.fct_transactions t USING(id_gateway_customer)
  WHERE t.nm_status='approved' AND t.dt_ordered_at>nm.dt_teller AND t.nm_gateway_plan NOT LIKE '%teller%'
    AND (t.nm_gateway_plan IN ('good','better','best','black','supporter','mecenas') OR t.bl_lifetime_offer)),
u AS (SELECT DISTINCT nm.id_gateway_customer, s.id_user FROM nm JOIN masterdata.dim_subscriptions s USING(id_gateway_customer) WHERE s.id_user IS NOT NULL),
esc AS (SELECT user_id, COUNT(DISTINCT DATE(time)) dias FROM events.fct_mixpanel__teller_media_playback_events WHERE time>='{START}' GROUP BY 1)
SELECT
  (SELECT COUNT(*) FROM nm) nao_membros,
  (SELECT COUNT(*) FROM conv) converteram,
  COUNT(DISTINCT u.id_gateway_customer) com_conta,
  COUNT(DISTINCT IF(e.user_id IS NOT NULL, u.id_gateway_customer, NULL)) ouviram,
  COUNT(DISTINCT IF(e.dias>=2, u.id_gateway_customer, NULL)) ouviram_2d
FROM u LEFT JOIN esc e ON e.user_id=u.id_user
"""

Q_ENGAJAMENTO = f"""
SELECT FORMAT_DATE('%Y-%m', DATE(time)) mes,
       COUNT(*) playbacks, COUNT(DISTINCT user_id) ouvintes, COUNT(DISTINCT media_id) livros
FROM events.fct_mixpanel__teller_media_playback_events
WHERE time>='{START}' GROUP BY 1 ORDER BY 1
"""

Q_OUVINTES_PERFIL = f"""
WITH ouvintes AS (SELECT DISTINCT user_id FROM events.fct_mixpanel__teller_media_playback_events WHERE time>='{START}' AND user_id IS NOT NULL),
sa AS (SELECT DISTINCT id_user,
    MAX(CASE WHEN (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%') THEN 1 ELSE 0 END) has_full,
    MAX(CASE WHEN nm_gateway_plan LIKE '%teller%' THEN 1 ELSE 0 END) has_tel
  FROM masterdata.dim_subscriptions WHERE nm_type='paid' AND nm_status IN ('active','wo renewal')
    AND dt_started_at<=CURRENT_DATETIME() AND dt_expires_in>=CURRENT_DATETIME() GROUP BY 1),
vital AS (SELECT DISTINCT s.id_user FROM masterdata.fct_transactions t JOIN masterdata.dim_subscriptions s USING(id_gateway_customer)
          WHERE t.nm_status='approved' AND t.bl_lifetime_offer)
SELECT CASE WHEN v.id_user IS NOT NULL OR sa.has_full=1 THEN 'membro_pleno'
            WHEN sa.has_tel=1 THEN 'so_teller' ELSE 'sem_assinatura' END perfil,
  COUNT(*) ouvintes
FROM ouvintes o LEFT JOIN sa ON sa.id_user=o.user_id LEFT JOIN vital v ON v.id_user=o.user_id
GROUP BY 1
"""

Q_TOP_LIVROS = f"""
SELECT b.nm_title titulo, b.nm_author autor, b.nm_genre genero, COUNT(DISTINCT p.user_id) ouvintes
FROM events.fct_mixpanel__teller_media_playback_events p JOIN events.dim_teller__audiobooks b ON b.id_book=p.media_id
WHERE p.time>='{START}' GROUP BY 1,2,3 ORDER BY ouvintes DESC LIMIT 10
"""

Q_GENEROS = f"""
SELECT COALESCE(b.nm_genre,'(sem)') genero, COUNT(DISTINCT p.user_id) ouvintes
FROM events.fct_mixpanel__teller_media_playback_events p JOIN events.dim_teller__audiobooks b ON b.id_book=p.media_id
WHERE p.time>='{START}' GROUP BY 1 ORDER BY ouvintes DESC LIMIT 8
"""

Q_SERIE_DIARIA = f"""
SELECT DATE(dt_ordered_at) dia,
  COUNTIF(nm_gateway_plan='teller') teller,
  COUNTIF(nm_gateway_plan IN ('good','better','best','black','supporter') AND NOT bl_lifetime_offer) gbb,
  COUNTIF(nm_gateway_plan NOT LIKE '%teller%') empresa
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='{START}' AND dt_ordered_at<CURRENT_DATE()
GROUP BY 1 ORDER BY 1
"""

# ─── build ───────────────────────────────────────────────────────────────────
def build() -> dict:
    print("  vendas produto...", flush=True); vp = bq(Q_VENDAS_PRODUTO)
    print("  vendas campanha...", flush=True); vc = bq(Q_VENDAS_CAMPANHA)
    print("  perfil...", flush=True); pf = bq(Q_PERFIL)
    print("  tier membros...", flush=True); tm = bq(Q_TIER_MEMBROS)
    print("  funil nao-membros...", flush=True); fn = bq(Q_FUNIL_NM)[0]
    print("  engajamento...", flush=True); en = bq(Q_ENGAJAMENTO)
    print("  perfil ouvintes...", flush=True); op = bq(Q_OUVINTES_PERFIL)
    print("  top livros...", flush=True); tl = bq(Q_TOP_LIVROS)
    print("  generos...", flush=True); gn = bq(Q_GENEROS)
    print("  serie diaria...", flush=True); sd = bq(Q_SERIE_DIARIA, max_rows=1000)

    meses = sorted({r["mes"] for r in vp} | {r["mes"] for r in vc} | {r["mes"] for r in en})

    def serie(rows, key, val, cast=ii):
        m = {r[key]: cast(r[val]) for r in rows}
        return [m.get(x, 0) for x in meses]

    # campanha TLR por perfil REAL do comprador
    camp = {}
    for r in vc:
        camp.setdefault(r["perfil"], {})[r["mes"]] = ii(r["n"])
    camp_series = {k: [camp.get(k, {}).get(x, 0) for x in meses] for k in ("membro", "ex_membro", "nao_membro")}
    camp_total = {k: sum(v) for k, v in camp_series.items()}

    # perfil agregado + por canal
    perfil_tot = {"membro": 0, "ex_membro": 0, "nao_membro": 0}
    perfil_canal = {"comercial": dict(perfil_tot), "digital": dict(perfil_tot)}
    for r in pf:
        perfil_tot[r["perfil"]] += ii(r["compradores"])
        perfil_canal[r["canal"]][r["perfil"]] += ii(r["compradores"])

    # correlacoes
    t = [ii(r["teller"]) for r in sd]; g = [ii(r["gbb"]) for r in sd]; e = [ii(r["empresa"]) for r in sd]
    corr = {"teller_gbb": round(pearson(t, g), 2),
            "teller_empresa": round(pearson(t, e), 2),
            "gbb_empresa": round(pearson(g, e), 2)}

    ouv = {r["perfil"]: ii(r["ouvintes"]) for r in op}

    receita_produto = sum(fi(r["receita"]) for r in vp)
    compradores_prod = sum(perfil_tot.values())
    ouvintes_medio = round(sum(ii(r["ouvintes"]) for r in en) / max(len(en), 1))

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "kpi": {
            "receita_produto": receita_produto,
            "compradores": compradores_prod,
            "ouvintes_medio_mes": ouvintes_medio,
            "pct_ouve": round(fn and ii(fn["ouviram"]) / max(ii(fn["com_conta"]), 1) * 100),
        },
        "meses": meses,
        "vendas_produto": {"n": serie(vp, "mes", "n"), "receita": serie(vp, "mes", "receita", fi)},
        "campanha": camp_series,
        "campanha_total": camp_total,
        "perfil": perfil_tot,
        "perfil_canal": perfil_canal,
        "tier_membros": [{"tier": r["tier"], "membros": ii(r["membros"])} for r in tm],
        "funil": {k: ii(fn[k]) for k in ("nao_membros", "converteram", "com_conta", "ouviram", "ouviram_2d")},
        "engajamento": {"ouvintes": serie(en, "mes", "ouvintes"), "playbacks": serie(en, "mes", "playbacks")},
        "ouvintes_perfil": ouv,
        "top_livros": [{"titulo": r["titulo"], "autor": r["autor"], "genero": r["genero"], "ouvintes": ii(r["ouvintes"])} for r in tl],
        "generos": [{"genero": r["genero"], "ouvintes": ii(r["ouvintes"])} for r in gn],
        "correlacao": corr,
    }

if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing Teller report data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: teller refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
