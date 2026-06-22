#!/usr/bin/env python3
"""
Refresh EVG lead qualification report data from BigQuery.
Usage: python refresh.py [--push]
  --push   after writing data.json, git add + commit + push to main
"""

import json, subprocess, sys, datetime
from pathlib import Path

TABLE = "bp-datawarehouse.datamart.dtm_analytics_lead_conversion"
TAG   = "EVG"
OUT   = Path(__file__).parent / "data.json"

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

def fi(v):
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def ii(v):
    try: return int(v) if v not in (None, "", "null") else 0
    except: return 0

# ─── queries ─────────────────────────────────────────────────────────────────
Q_MIX_CONV = f"""
WITH base AS (
  SELECT nm_email,
    (SELECT COUNT(*)>0 FROM UNNEST(arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou
  FROM `{TABLE}` WHERE nm_tag="{TAG}" AND ARRAY_LENGTH(arr_survey_responses)>0
),
resp AS (
  SELECT lc.nm_email, s.nm_question, s.nm_answer
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}"
)
SELECT r.nm_question, r.nm_answer,
  COUNT(DISTINCT r.nm_email) AS leads,
  COUNTIF(b.bl_comprou) AS compradores,
  ROUND(SAFE_DIVIDE(COUNTIF(b.bl_comprou), COUNT(DISTINCT r.nm_email))*100, 2) AS conv_pct
FROM resp r JOIN base b ON b.nm_email=r.nm_email
WHERE r.nm_question IN ("relacao_bp","renda")
GROUP BY 1,2 ORDER BY 1, 3 DESC
"""

Q_STREAM_MIX = f"""
WITH base AS (
  SELECT nm_email,
    (SELECT COUNT(*)>0 FROM UNNEST(arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou
  FROM `{TABLE}` WHERE nm_tag="{TAG}" AND ARRAY_LENGTH(arr_survey_responses)>0
),
tot AS (SELECT COUNT(DISTINCT nm_email) AS n FROM base),
rs AS (
  SELECT DISTINCT lc.nm_email, s.nm_answer
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}" AND s.nm_question="streaming"
)
SELECT rs.nm_answer,
  COUNT(DISTINCT rs.nm_email) AS leads,
  ROUND(COUNT(DISTINCT rs.nm_email)/(SELECT n FROM tot)*100, 1) AS pct_total,
  COUNTIF(b.bl_comprou) AS compradores,
  ROUND(SAFE_DIVIDE(COUNTIF(b.bl_comprou), COUNT(DISTINCT rs.nm_email))*100, 2) AS conv_pct
FROM rs JOIN base b ON b.nm_email=rs.nm_email
GROUP BY 1 ORDER BY 2 DESC LIMIT 20
"""

Q_COMBOS = f"""
WITH per_lead AS (
  SELECT lc.nm_email,
    IFNULL((SELECT SUM(t.vl_payment_gross) FROM UNNEST(lc.arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30), 0) AS receita,
    (SELECT COUNT(*)>0 FROM UNNEST(lc.arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou,
    ARRAY_TO_STRING(ARRAY(
      SELECT DISTINCT s.nm_answer
      FROM UNNEST(lc.arr_survey_responses) r, UNNEST(r.st_data) s
      WHERE s.nm_question="streaming" ORDER BY s.nm_answer
    ), " · ") AS combo
  FROM `{TABLE}` lc
  WHERE nm_tag="{TAG}" AND ARRAY_LENGTH(arr_survey_responses)>0
)
SELECT combo,
  COUNT(*) AS leads, COUNTIF(bl_comprou) AS compradores,
  ROUND(SAFE_DIVIDE(COUNTIF(bl_comprou), COUNT(*))*100, 2) AS conv_pct,
  ROUND(SAFE_DIVIDE(SUM(receita), COUNT(*)), 2) AS rpl,
  CASE WHEN STRPOS(combo,"Brasil Paralelo")>0 THEN 1 ELSE 0 END AS tem_bp
FROM per_lead
WHERE combo IS NOT NULL AND combo != ""
GROUP BY 1,6 HAVING COUNT(*)>=20
ORDER BY conv_pct DESC
"""

Q_SCORE = f"""
WITH base AS (
  SELECT nm_email,
    (SELECT COUNT(*)>0 FROM UNNEST(arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou
  FROM `{TABLE}` WHERE nm_tag="{TAG}" AND ARRAY_LENGTH(arr_survey_responses)>0
),
scores AS (
  SELECT lc.nm_email,
    MAX(CASE WHEN s.nm_question="relacao_bp" THEN
      CASE s.nm_answer
        WHEN "Assino hoje" THEN 3
        WHEN "Já assinei no passado" THEN 2
        WHEN "Consumo conteúdo gratuito (YouTube, redes sociais)" THEN 1
        WHEN "Já ouvi falar, mas nunca assisti nada" THEN 1
        ELSE 0 END ELSE 0 END) AS sc_rel,
    MAX(CASE WHEN s.nm_question="renda" THEN
      CASE s.nm_answer
        WHEN "Acima de R$ 20.000" THEN 3 WHEN "Acima de R$ 15.000" THEN 3
        WHEN "R$ 10.000 – R$ 20.000" THEN 3 WHEN "R$ 10.000 – R$ 15.000" THEN 2
        WHEN "R$ 5.000 – R$ 10.000" THEN 2 WHEN "R$ 2.000 – R$ 5.000" THEN 1
        ELSE 0 END ELSE 0 END) AS sc_renda
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}" GROUP BY 1
)
SELECT sc_rel+sc_renda AS score,
  COUNT(*) AS leads, COUNTIF(b.bl_comprou) AS compradores,
  ROUND(SAFE_DIVIDE(COUNTIF(b.bl_comprou), COUNT(*))*100, 2) AS conv_pct
FROM scores sc JOIN base b ON b.nm_email=sc.nm_email
GROUP BY 1 ORDER BY 1
"""

Q_TEMPO = f"""
WITH leads AS (
  SELECT nm_email,
    DATE_TRUNC(DATE(dt_registered_at), WEEK(MONDAY)) AS semana,
    (SELECT COUNT(*)>0 FROM UNNEST(arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou,
    ARRAY_LENGTH(arr_survey_responses)>0 AS respondeu
  FROM `{TABLE}` WHERE nm_tag="{TAG}"
)
SELECT semana,
  COUNT(*) AS leads, COUNTIF(respondeu) AS respondentes,
  ROUND(COUNTIF(respondeu)/COUNT(*)*100, 1) AS pct_resposta,
  COUNTIF(bl_comprou) AS compradores,
  ROUND(SAFE_DIVIDE(COUNTIF(bl_comprou), COUNT(*))*100, 2) AS conv_pct
FROM leads GROUP BY 1 ORDER BY 1
"""

Q_MATRIZ_REL_RENDA = f"""
WITH compra AS (
  SELECT nm_email,
    (SELECT COUNT(*)>0 FROM UNNEST(arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou
  FROM `{TABLE}` WHERE nm_tag="{TAG}" AND ARRAY_LENGTH(arr_survey_responses)>0
),
answers AS (
  SELECT lc.nm_email,
    MAX(CASE WHEN s.nm_question="relacao_bp" THEN s.nm_answer END) AS q_a,
    MAX(CASE WHEN s.nm_question="renda"      THEN s.nm_answer END) AS q_b
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}" GROUP BY 1
)
SELECT a.q_a, a.q_b, COUNT(*) AS n, COUNTIF(c.bl_comprou) AS comp,
  ROUND(SAFE_DIVIDE(COUNTIF(c.bl_comprou),COUNT(*))*100,2) AS conv
FROM answers a JOIN compra c ON a.nm_email=c.nm_email
WHERE a.q_a IS NOT NULL AND a.q_b IS NOT NULL
GROUP BY 1,2 ORDER BY 1,2
"""

Q_MATRIZ_REL_STREAM = f"""
WITH compra AS (
  SELECT nm_email,
    (SELECT COUNT(*)>0 FROM UNNEST(arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou
  FROM `{TABLE}` WHERE nm_tag="{TAG}" AND ARRAY_LENGTH(arr_survey_responses)>0
),
rel AS (
  SELECT lc.nm_email,
    MAX(CASE WHEN s.nm_question="relacao_bp" THEN s.nm_answer END) AS q_a
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}" GROUP BY 1
),
streams AS (
  SELECT DISTINCT lc.nm_email, s.nm_answer AS q_b
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}" AND s.nm_question="streaming"
)
SELECT r.q_a, s.q_b, COUNT(*) AS n, COUNTIF(c.bl_comprou) AS comp,
  ROUND(SAFE_DIVIDE(COUNTIF(c.bl_comprou),COUNT(*))*100,2) AS conv
FROM rel r JOIN streams s ON r.nm_email=s.nm_email JOIN compra c ON r.nm_email=c.nm_email
WHERE r.q_a IS NOT NULL
GROUP BY 1,2 ORDER BY 1,2
"""

Q_MATRIZ_RENDA_STREAM = f"""
WITH compra AS (
  SELECT nm_email,
    (SELECT COUNT(*)>0 FROM UNNEST(arr_st_approved_transactions) t
     WHERE t.days_to_purchase BETWEEN 0 AND 30) AS bl_comprou
  FROM `{TABLE}` WHERE nm_tag="{TAG}" AND ARRAY_LENGTH(arr_survey_responses)>0
),
renda AS (
  SELECT lc.nm_email,
    MAX(CASE WHEN s.nm_question="renda" THEN s.nm_answer END) AS q_a
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}" GROUP BY 1
),
streams AS (
  SELECT DISTINCT lc.nm_email, s.nm_answer AS q_b
  FROM `{TABLE}` lc, UNNEST(arr_survey_responses) r, UNNEST(r.st_data) s
  WHERE lc.nm_tag="{TAG}" AND s.nm_question="streaming"
)
SELECT r.q_a, s.q_b, COUNT(*) AS n, COUNTIF(c.bl_comprou) AS comp,
  ROUND(SAFE_DIVIDE(COUNTIF(c.bl_comprou),COUNT(*))*100,2) AS conv
FROM renda r JOIN streams s ON r.nm_email=s.nm_email JOIN compra c ON r.nm_email=c.nm_email
WHERE r.q_a IS NOT NULL
GROUP BY 1,2 ORDER BY 1,2
"""

Q_DAILY = f"""
WITH leads AS (
  SELECT DATE(dt_registered_at) AS dia,
    ARRAY_LENGTH(arr_survey_responses)>0 AS respondeu
  FROM `{TABLE}`
  WHERE nm_tag="{TAG}" AND DATE(dt_registered_at) >= "2026-05-21"
)
SELECT dia, COUNT(*) AS leads, COUNTIF(respondeu) AS respondentes,
  ROUND(COUNTIF(respondeu)/COUNT(*)*100, 0) AS taxa_pct
FROM leads GROUP BY 1 ORDER BY 1
"""

# ─── label mappings ──────────────────────────────────────────────────────────
STREAM_SHORT = {"Plataformas educacionais (Hotmart, Udemy, Coursera)": "Educacional"}
STREAM_ORDER = ["Netflix","Nenhum","Prime Video","Brasil Paralelo","Disney+","HBO Max","Globoplay","Educacional"]

RENDA_MIX_MAP = {
    "Até R$ 5.000":          "Até R$5k",
    "Até R$ 2.000":          "Até R$5k",
    "R$ 2.000 – R$ 5.000":  "Até R$5k",
    "R$ 5.000 – R$ 10.000": "R$5–10k",
    "R$ 10.000 – R$ 15.000":"R$10–15k",
    "R$ 10.000 – R$ 20.000":"R$10–15k",  # opção antiga → mais próxima atual
    "Acima de R$ 15.000":   ">R$15k",
    "Acima de R$ 20.000":   ">R$15k",    # opção antiga → mais próxima atual
    "Prefiro não informar":  "Não informa",
}
RENDA_MIX_ORDER = ["Até R$5k","Não informa","R$5–10k","R$10–15k",">R$15k"]
# grupos para o conv chart — agrega opções antigas nas faixas atuais
RENDA_CONV_GROUPS = [
    ("Até R$5k",    ["Até R$ 5.000","Até R$ 2.000","R$ 2.000 – R$ 5.000"]),
    ("R$5–10k",     ["R$ 5.000 – R$ 10.000"]),
    ("R$10–15k",    ["R$ 10.000 – R$ 15.000","R$ 10.000 – R$ 20.000"]),
    (">R$15k",      ["Acima de R$ 15.000","Acima de R$ 20.000"]),
    ("Não informa", ["Prefiro não informar"]),
]

REL_MIX_SHORT = {
    "Consumo conteúdo gratuito (YouTube, redes sociais)": "Consumo grátis",
    "Já ouvi falar, mas nunca assisti nada": "Já ouvi falar",
    "Já assinei no passado": "Já assinei",
    "Assino hoje": "Assino hoje",
    "Nunca ouvi falar": "Nunca ouvi",
}
REL_CONV_ORDER = [
    ("Assino hoje","Assino hoje"),
    ("Já assinei no passado","Já assinei"),
    ("Consumo conteúdo gratuito (YouTube, redes sociais)","Consumo grátis"),
    ("Já ouvi falar, mas nunca assisti nada","Já ouvi falar"),
    ("Nunca ouvi falar","Nunca ouvi"),
]

COMBO_ABBR = {
    "Brasil Paralelo":"BP", "Prime Video":"Prime", "Disney+":"Disney+",
    "HBO Max":"HBO", "Globoplay":"Globo", "Netflix":"Netflix",
    "Nenhum":"Nenhum",
    "Plataformas educacionais (Hotmart, Udemy, Coursera)":"Edu",
}
WEEKS_PT = {
    "2026-05-18":"18/mai","2026-05-25":"25/mai","2026-06-01":"01/jun",
    "2026-06-08":"08/jun","2026-06-15":"15/jun","2026-06-22":"22/jun",
    "2026-06-29":"29/jun",
}
MONTHS_PT = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]

# ─── helpers ─────────────────────────────────────────────────────────────────
def combo_label(c: str) -> str:
    return "+".join(COMBO_ABBR.get(p.strip(), p.strip()) for p in c.split("·"))

def combo_signal(c: str) -> str:
    has_bp   = "Brasil Paralelo" in c
    has_glob = "Globoplay" in c
    has_edu  = "Plataformas educacionais" in c
    if has_bp and has_glob: return "Globoplay + BP"
    if has_glob:            return "Globoplay"
    if has_bp and has_edu:  return "BP + edu"
    if has_bp:              return "BP"
    if has_edu:             return "edu"
    return ""

def combo_display(c: str) -> str:
    return c.replace("Plataformas educacionais (Hotmart, Udemy, Coursera)","Plataformas educacionais")

def weighted_conv(rows_by_ans: dict, keys: list[str]) -> float:
    leads = sum(ii(rows_by_ans[k]["leads"]) for k in keys if k in rows_by_ans)
    comp  = sum(ii(rows_by_ans[k]["compradores"]) for k in keys if k in rows_by_ans)
    return round(comp / leads * 100, 2) if leads else 0.0

# ─── build ────────────────────────────────────────────────────────────────────
def build() -> dict:
    print("  mix + conv (relacao_bp, renda)...", flush=True)
    mix_conv   = bq(Q_MIX_CONV)
    print("  streaming individual...", flush=True)
    stream_mix = bq(Q_STREAM_MIX)
    print("  streaming combos...", flush=True)
    combos     = bq(Q_COMBOS)
    print("  lead score...", flush=True)
    score_rows = bq(Q_SCORE)
    print("  weekly tempo...", flush=True)
    tempo_rows = bq(Q_TEMPO)
    print("  daily response rate...", flush=True)
    daily_rows = bq(Q_DAILY)
    print("  matriz cruzada (rel×renda, rel×stream, renda×stream)...", flush=True)
    mz_rel_renda    = bq(Q_MATRIZ_REL_RENDA)
    mz_rel_stream   = bq(Q_MATRIZ_REL_STREAM)
    mz_renda_stream = bq(Q_MATRIZ_RENDA_STREAM)

    # ── relacao_bp ──
    rel_rows   = [r for r in mix_conv if r["nm_question"] == "relacao_bp"]
    rel_by_ans = {r["nm_answer"]: r for r in rel_rows}
    rel_total  = sum(ii(r["leads"]) for r in rel_rows)

    mix_rel = {
        "labels": [REL_MIX_SHORT.get(r["nm_answer"], r["nm_answer"])
                   for r in sorted(rel_rows, key=lambda r: -ii(r["leads"]))],
        "data":   [round(ii(r["leads"]) / rel_total * 100, 1)
                   for r in sorted(rel_rows, key=lambda r: -ii(r["leads"]))],
    }
    conv_rel_pairs = sorted(
        [(lbl, fi(rel_by_ans[k]["conv_pct"]) if k in rel_by_ans else 0.0)
         for k, lbl in REL_CONV_ORDER],
        key=lambda x: -x[1]
    )
    conv_rel = {"labels": [p[0] for p in conv_rel_pairs], "data": [p[1] for p in conv_rel_pairs]}

    bench_evg_rel = [
        weighted_conv(rel_by_ans, ["Assino hoje","Já assinei no passado"]),
        weighted_conv(rel_by_ans, ["Consumo conteúdo gratuito (YouTube, redes sociais)"]),
        weighted_conv(rel_by_ans, ["Já ouvi falar, mas nunca assisti nada"]),
        weighted_conv(rel_by_ans, ["Nunca ouvi falar"]),
    ]

    # ── renda ──
    renda_rows   = [r for r in mix_conv if r["nm_question"] == "renda"]
    renda_by_ans = {r["nm_answer"]: r for r in renda_rows}

    renda_agg: dict[str, int] = {}
    for r in renda_rows:
        grp = RENDA_MIX_MAP.get(r["nm_answer"], r["nm_answer"])
        renda_agg[grp] = renda_agg.get(grp, 0) + ii(r["leads"])
    renda_total = sum(renda_agg.values())

    mix_renda = {
        "labels": RENDA_MIX_ORDER,
        "data":   [round(renda_agg.get(l, 0) / renda_total * 100, 1) for l in RENDA_MIX_ORDER],
    }
    conv_renda_pairs = sorted(
        [(lbl, weighted_conv(renda_by_ans, keys)) for lbl, keys in RENDA_CONV_GROUPS],
        key=lambda x: -x[1]
    )
    conv_renda = {"labels": [p[0] for p in conv_renda_pairs], "data": [p[1] for p in conv_renda_pairs]}

    bench_evg_renda = [
        weighted_conv(renda_by_ans, ["Até R$ 2.000","Até R$ 5.000","R$ 2.000 – R$ 5.000"]),
        weighted_conv(renda_by_ans, ["R$ 5.000 – R$ 10.000"]),
        weighted_conv(renda_by_ans, ["R$ 10.000 – R$ 15.000","R$ 10.000 – R$ 20.000",
                                     "Acima de R$ 15.000","Acima de R$ 20.000"]),
    ]

    # ── streaming individual ──
    stream_by_lbl = {STREAM_SHORT.get(r["nm_answer"], r["nm_answer"]): r for r in stream_mix}
    mix_stream = {
        "labels": STREAM_ORDER,
        "data":   [fi(stream_by_lbl.get(l, {}).get("pct_total", 0)) for l in STREAM_ORDER],
        "conv":   [fi(stream_by_lbl.get(l, {}).get("conv_pct", 0)) for l in STREAM_ORDER],
    }

    # ── streaming combos ──
    bubble_data   = []
    stream_combos = []
    for r in combos:
        c = r["combo"]
        bubble_data.append({"l":combo_label(c),"x":ii(r["leads"]),"y":fi(r["conv_pct"]),"c":ii(r["compradores"]),"bp":ii(r["tem_bp"])})
        stream_combos.append({"c":combo_display(c),"n":ii(r["leads"]),"cv":fi(r["conv_pct"]),"rpl":fi(r["rpl"]),"s":combo_signal(c)})
    stream_combos.sort(key=lambda d: -d["cv"])

    # ── lead score ──
    score_by_val = {ii(r["score"]): r for r in score_rows}
    score = {
        "leads": [ii(score_by_val.get(i, {}).get("leads", 0)) for i in range(7)],
        "conv":  [fi(score_by_val.get(i, {}).get("conv_pct", 0.0)) for i in range(7)],
    }

    # ── weekly tempo ──
    tempo: dict = {"labels": [], "taxaResposta": [], "taxaCompra": []}
    for r in tempo_rows:
        sem = str(r["semana"])
        if sem in WEEKS_PT:
            tempo["labels"].append(WEEKS_PT[sem])
            tempo["taxaResposta"].append(fi(r["pct_resposta"]))
            tempo["taxaCompra"].append(fi(r["conv_pct"]))

    # ── daily response rate ──
    tr_labels: list[str] = []
    tr_data:   list[int] = []
    tr_phases: list[str] = []
    for r in daily_rows:
        dia = str(r["dia"])
        m, d = int(dia[5:7]) - 1, int(dia[8:10])
        tr_labels.append(f"{d:02d}/{MONTHS_PT[m]}")
        taxa = ii(r["taxa_pct"])
        tr_data.append(taxa)
        if taxa < 10:
            tr_phases.append("grey")
        elif taxa < 65:
            tr_phases.append("amber")
        else:
            tr_phases.append("green")

    # ── matriz cruzada ──
    def to_cells(rows):
        return [{"qa": r["q_a"], "qb": r["q_b"], "n": ii(r["n"]), "conv": fi(r["conv"])} for r in rows]

    return {
        "updated_at":    datetime.datetime.now().isoformat(timespec="seconds"),
        "campaign":      TAG,
        "mixRel":        mix_rel,
        "mixRenda":      mix_renda,
        "mixStream":     mix_stream,
        "convRel":       conv_rel,
        "convRenda":     conv_renda,
        "bubble":        bubble_data,
        "streamCombos":  stream_combos,
        "score":         score,
        "tempo":         tempo,
        "taxaResposta":  {"labels": tr_labels, "data": tr_data, "phases": tr_phases},
        "benchEvgRenda": bench_evg_renda,
        "benchEvgRel":   bench_evg_rel,
        "matrizCruz": {
            "rel_renda":    to_cells(mz_rel_renda),
            "rel_stream":   to_cells(mz_rel_stream),
            "renda_stream": to_cells(mz_renda_stream),
        },
    }

# ─── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    push = "--push" in sys.argv
    print(f"Refreshing {TAG} report data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} written — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: EVG refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
