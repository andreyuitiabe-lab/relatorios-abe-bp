#!/usr/bin/env python3
"""
Relatório: Pesquisa de qualificação de leads — EVG × BP10.

Puxa do BQ (dtm_analytics_lead_conversion, tags EVG/BP10), agrega server-side
e escreve data.json. Nenhum número fica hardcoded no index.html.

Uso:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

TABLE = "bp-datawarehouse.datamart.dtm_analytics_lead_conversion"
OUT   = Path(__file__).parent / "data.json"
OUT_M = Path(__file__).parent / "matriz.json"

# ordem de exibição das categorias (baixo→alto / frio→quente); resto vai alfabético
CAT_ORDER = {
    "renda": ["Até R$ 2.000","Até R$ 5.000","R$ 2.000 – R$ 5.000","R$ 5.000 – R$ 10.000",
              "R$ 10.000 – R$ 15.000","Acima de R$ 15.000","Prefiro não informar"],
    "relacao_bp": ["Nunca ouvi falar","Consumo conteúdo gratuito (YouTube, redes sociais)",
                   "Já ouvi falar, mas nunca assisti nada","Já assinei no passado","Assino hoje"],
    "tempo_conhece_bp": ["Esse é meu primeiro contato","Menos de um mês","Até 6 meses",
                         "Entre 6 meses e 1 ano","Entre 1 e 3 anos","Mais que 3 anos"],
    "qtd_streaming": ["Nenhum","1","2","3","3 +"],
}

# perguntas da pesquisa in-funnel (chave -> rótulo curto)
QUESTIONS = {
    "renda":             "Renda",
    "relacao_bp":        "Relação com a BP",
    "tempo_conhece_bp":  "Há quanto tempo conhece",
    "fonte_confianca":   "Fonte de confiança",
    "qtd_streaming":     "Qtd. streamings",
    "streaming":         "Quais streamings",
    "midia_tradicional": "Mídia tradicional",
    "religiao":          "Religião",
}

def bq(sql: str, max_rows: int = 5000) -> list:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         f"--max_rows={max_rows}", sql],
        capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    out = r.stdout.strip()
    return json.loads(out) if out else []

def ii(v):
    try: return int(v) if v not in (None, "", "null") else 0
    except: return 0

# ─── base: 1 linha por email+campanha, survey desempacotada ────────────────────
def extract_expr():
    cols = ",\n    ".join(
        f"(SELECT a FROM UNNEST(survey) WHERE q = '{k}' LIMIT 1) AS {k}"
        for k in QUESTIONS)
    return f"""
WITH raw AS (
  SELECT
    nm_email, nm_tag, dt_registered_at_br,
    st_member_status_at_registration AS status,
    IF(qt_vendas > 0, 1, 0) AS conv,
    ARRAY(SELECT AS STRUCT sr.nm_question AS q, sr.nm_answer AS a
          FROM UNNEST(arr_survey_responses) ar, UNNEST(ar.st_data) sr) AS survey,
    ROW_NUMBER() OVER (PARTITION BY nm_email, nm_tag ORDER BY dt_registered_at_br) AS rn
  FROM `{TABLE}`
  WHERE nm_tag IN ('EVG','BP10')
),
d AS (
  SELECT nm_tag, dt_registered_at_br, status, conv,
    {cols}
  FROM raw WHERE rn = 1
),
dd AS (
  SELECT *,
    ({" OR ".join(f"{k} IS NOT NULL" for k in QUESTIONS)}) AS responded
  FROM d
)"""

BASE = extract_expr()

def build() -> dict:
    print("  overview + status...", flush=True)
    overview = bq(f"""{BASE}
      SELECT nm_tag, COUNT(*) n, SUM(conv) conv,
        COUNTIF(status='Não Membro') nm,
        SUM(IF(status='Não Membro',conv,0)) nm_conv,
        CAST(MIN(DATE(dt_registered_at_br)) AS STRING) dt_min,
        CAST(MAX(DATE(dt_registered_at_br)) AS STRING) dt_max
      FROM dd GROUP BY nm_tag""")

    status = bq(f"""{BASE}
      SELECT nm_tag, status, COUNT(*) n FROM dd GROUP BY nm_tag, status""")

    print("  cobertura das perguntas...", flush=True)
    cov_sel = ", ".join(f"COUNTIF({k} IS NOT NULL) {k}" for k in QUESTIONS)
    coverage = bq(f"{BASE} SELECT nm_tag, COUNT(*) n, {cov_sel} FROM dd GROUP BY nm_tag")

    print("  responder vs não (NM)...", flush=True)
    resp = bq(f"""{BASE}
      SELECT nm_tag, responded, COUNT(*) n, SUM(conv) conv
      FROM dd WHERE status='Não Membro' GROUP BY nm_tag, responded""")

    print("  conversão por resposta (NM)...", flush=True)
    bycat = bq(f"""{BASE}
      SELECT nm_tag, 'relacao_bp' q, relacao_bp a, COUNT(*) n, SUM(conv) c FROM dd WHERE status='Não Membro' AND relacao_bp IS NOT NULL GROUP BY 1,3
      UNION ALL SELECT nm_tag, 'renda', renda, COUNT(*), SUM(conv) FROM dd WHERE status='Não Membro' AND renda IS NOT NULL GROUP BY 1,3
      UNION ALL SELECT nm_tag, 'tempo_conhece_bp', tempo_conhece_bp, COUNT(*), SUM(conv) FROM dd WHERE status='Não Membro' AND tempo_conhece_bp IS NOT NULL GROUP BY 1,3
    """, max_rows=200)

    print("  combos renda × relação (NM)...", flush=True)
    combo = bq(f"""{BASE}
      SELECT nm_tag, renda, relacao_bp, COUNT(*) n, SUM(conv) c
      FROM dd WHERE status='Não Membro' AND renda IS NOT NULL AND relacao_bp IS NOT NULL
      GROUP BY 1,2,3 HAVING n >= 120""", max_rows=500)

    print("  pior perfil (frio)...", flush=True)
    cold = bq(f"""{BASE}
      SELECT nm_tag, COUNT(*) n, SUM(conv) c,
        SUM(CASE WHEN relacao_bp='Nunca ouvi falar'
             OR tempo_conhece_bp IN ('Esse é meu primeiro contato','Menos de um mês')
            THEN 1 ELSE 0 END) cold_n,
        SUM(CASE WHEN relacao_bp='Nunca ouvi falar'
             OR tempo_conhece_bp IN ('Esse é meu primeiro contato','Menos de um mês')
            THEN conv ELSE 0 END) cold_c
      FROM dd WHERE status='Não Membro' GROUP BY nm_tag""")

    # ─── montar dict ───────────────────────────────────────────────────────────
    def rate(c, n): return round(c / n * 100, 2) if n else 0.0

    ov = {r["nm_tag"]: r for r in overview}
    camps = {}
    for tag, r in ov.items():
        n, nm = ii(r["n"]), ii(r["nm"])
        camps[tag] = {
            "n": n, "conv": ii(r["conv"]), "convPct": rate(ii(r["conv"]), n),
            "nm": nm, "nmConvPct": rate(ii(r["nm_conv"]), nm),
            "dtMin": r["dt_min"], "dtMax": r["dt_max"],
            "status": [], "nmBase": rate(ii(r["nm_conv"]), nm),
        }
    for r in status:
        camps[r["nm_tag"]]["status"].append(
            {"label": r["status"], "n": ii(r["n"]),
             "pct": rate(ii(r["n"]), camps[r["nm_tag"]]["n"])})
    for t in camps:
        camps[t]["status"].sort(key=lambda x: -x["n"])

    cov = []
    covmap = {r["nm_tag"]: r for r in coverage}
    for k, lbl in QUESTIONS.items():
        row = {"key": k, "label": lbl}
        for tag in ("EVG", "BP10"):
            r = covmap.get(tag)
            row[tag] = rate(ii(r[k]), ii(r["n"])) if r else 0.0
        cov.append(row)

    respd = {}
    for r in resp:
        respd.setdefault(r["nm_tag"], {})[r["responded"] == "true"] = \
            {"n": ii(r["n"]), "convPct": rate(ii(r["conv"]), ii(r["n"]))}

    def cat_table(q):
        out = {}
        for r in bycat:
            if r["q"] != q: continue
            base = camps[r["nm_tag"]]["nmBase"]
            pct = rate(ii(r["c"]), ii(r["n"]))
            out.setdefault(r["nm_tag"], []).append({
                "answer": r["a"], "n": ii(r["n"]), "convPct": pct,
                "lift": round(pct / base, 2) if base else 0})
        for t in out: out[t].sort(key=lambda x: -x["convPct"])
        return out

    combos = []
    for r in combo:
        base = camps[r["nm_tag"]]["nmBase"]
        pct = rate(ii(r["c"]), ii(r["n"]))
        combos.append({"tag": r["nm_tag"], "renda": r["renda"],
                       "relacao": r["relacao_bp"], "n": ii(r["n"]),
                       "convPct": pct, "lift": round(pct / base, 2) if base else 0})
    combos.sort(key=lambda x: -x["convPct"])

    cold_out = {}
    for r in cold:
        base = camps[r["nm_tag"]]["nmBase"]
        pct = rate(ii(r["cold_c"]), ii(r["cold_n"]))
        cold_out[r["nm_tag"]] = {
            "n": ii(r["cold_n"]),
            "sharePct": rate(ii(r["cold_n"]), ii(r["n"])),
            "convPct": pct, "lift": round(pct / base, 2) if base else 0}

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "camps": camps,
        "coverage": cov,
        "responded": respd,
        "relacao": cat_table("relacao_bp"),
        "renda": cat_table("renda"),
        "tempo": cat_table("tempo_conhece_bp"),
        "combos": combos,
        "cold": cold_out,
    }

# ─── matriz.json: tabela-fato compacta p/ pivot dinâmico no navegador ──────────
NA = "(sem resposta)"

def build_matrix() -> dict:
    print("  tabela-fato (matriz)...", flush=True)
    attrs = list(QUESTIONS)
    dims = ", ".join(f"IFNULL({k}, '{NA}') {k}" for k in attrs)
    facts = bq(f"""{BASE}
      SELECT nm_tag, IF(status='Não Membro','NM','MEMBRO') pub, {dims},
             COUNT(*) n, SUM(conv) c
      FROM dd GROUP BY nm_tag, pub, {', '.join(attrs)}""", max_rows=20000)

    rows = []
    for r in facts:
        rows.append({"t": r["nm_tag"], "p": r["pub"], "n": ii(r["n"]), "c": ii(r["c"]),
                     **{k: r[k] for k in attrs}})

    # valores observados por atributo, na ordem de exibição
    values = {}
    for k in attrs:
        seen = {r[k] for r in rows}
        seen.discard(NA)
        ordered = [v for v in CAT_ORDER.get(k, []) if v in seen]
        ordered += sorted(v for v in seen if v not in ordered)
        if any(r[k] == NA for r in rows):
            ordered.append(NA)
        values[k] = ordered

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "attrs": [{"key": k, "label": QUESTIONS[k]} for k in attrs],
        "values": values,
        "facts": rows,
    }

if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing EVG×BP10 survey report from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        mat = build_matrix()
        OUT_M.write_text(json.dumps(mat, ensure_ascii=False), encoding="utf-8")
        print(f"✓ {OUT_M.name} — {len(mat['facts'])} grupos")
        if push:
            subprocess.run(["git", "add", str(OUT), str(OUT.parent)], check=True)
            subprocess.run(["git", "commit", "-m",
                            f"data: relatório pesquisa EVG×BP10 {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
