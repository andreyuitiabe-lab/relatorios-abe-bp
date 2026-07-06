#!/usr/bin/env python3
"""
Refresh report data from BigQuery.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Copiar este arquivo para a pasta do relatório e adaptar:
  1. Mudar TABLE e TAG (ou remover TAG se não for campanha)
  2. Escrever as queries em Q_xxx
  3. Preencher build() com a lógica de transformação
  4. Garantir que build() retorna um dict compatível com o que initCharts(D) espera no index.html
"""

import json, subprocess, sys, datetime
from pathlib import Path

# ─── config ──────────────────────────────────────────────────────────────────
TABLE = "bp-datawarehouse.datamart.dtm_analytics_lead_conversion"
TAG   = "XXX"    # sigla da campanha (nm_tag), ou remover se não for campanha
OUT   = Path(__file__).parent / "data.json"

# ─── BQ helper ───────────────────────────────────────────────────────────────
def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    """Executa query no BQ e retorna lista de dicts (todos os valores são str)."""
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
    """Cast seguro para float."""
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def ii(v) -> int:
    """Cast seguro para int."""
    try: return int(v) if v not in (None, "", "null") else 0
    except: return 0

# ─── queries ─────────────────────────────────────────────────────────────────
# Definir uma constante por query. Usar f-strings com TABLE e TAG.
# Exemplo:
#
# Q_CONVERSAO = f"""
# SELECT
#   DATE_TRUNC(DATE(dt_registered_at), WEEK(MONDAY)) AS semana,
#   COUNT(*) AS leads,
#   COUNTIF(EXISTS (
#     SELECT 1 FROM UNNEST(arr_st_approved_transactions) t
#     WHERE t.days_to_purchase BETWEEN 0 AND 30
#   )) AS compradores
# FROM `{TABLE}`
# WHERE nm_tag = "{TAG}"
# GROUP BY 1 ORDER BY 1
# """

# ─── build ───────────────────────────────────────────────────────────────────
def build() -> dict:
    """Roda as queries e monta o dict que será salvo em data.json."""
    # Exemplo:
    # print("  conversão semanal...", flush=True)
    # conv_rows = bq(Q_CONVERSAO)
    #
    # return {
    #     "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    #     "campaign": TAG,
    #     "semanal": {
    #         "labels": [str(r["semana"]) for r in conv_rows],
    #         "leads":  [ii(r["leads"])   for r in conv_rows],
    #         "conv":   [fi(r["conv_pct"]) for r in conv_rows],
    #     },
    # }
    raise NotImplementedError("Preencher build() com as queries e transformações")

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
