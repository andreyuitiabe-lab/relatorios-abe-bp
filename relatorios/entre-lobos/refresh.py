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
}

# Benchmark fixo: testes de segmentação da fase [VENDA] do ELS (20/05–17/07/2026).
# Fonte: els-analise.md — atribuição pixel Meta (facebook_ads_funnel), não o modelo interno.
BENCH_ELS = [
    {"nome": "Teste sinal forte",            "roas": 2.13, "spend": "R$ 15k",  "ref": False},
    {"nome": "LKL compradores ELS 1%",       "roas": 1.90, "spend": "R$ 28k",  "ref": False},
    {"nome": "LKL viewers do doc",           "roas": 1.68, "spend": "R$ 53k",  "ref": False},
    {"nome": "Advantage amplo (referência)", "roas": 1.40, "spend": "R$ 4,1M", "ref": True},
    {"nome": "Remarketing quente (Viu o Doc)","roas": 1.15, "spend": "R$ 3,6k","ref": False},
    {"nome": "LKL 1% genérico",              "roas": 0.98, "spend": "R$ 34k",  "ref": False},
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

    print("  leads ELB26 por dia...", flush=True)
    leads_rows = bq(Q_LEADS_DIA)

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "campaign": TAG,
        "sementes": sementes,
        "leads_dia": {
            "labels": [str(r["dia"]) for r in leads_rows],
            "leads":  [ii(r["leads"]) for r in leads_rows],
        },
        "total_leads": sum(ii(r["leads"]) for r in leads_rows),
        "bench_els": BENCH_ELS,
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
