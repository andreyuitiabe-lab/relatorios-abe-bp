#!/usr/bin/env python3
"""
Refresh — App Engajamento ELS Junho (Google Ads)

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

TABLE = "bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel"
OUT   = Path(__file__).parent / "data.json"

CAMPANHAS = [
    "[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v2",
    "[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v3",
    "[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | ios",
]

Q_DIARIO = f"""
SELECT
  nm_campaign_name,
  reference_date,
  ROUND(SUM(vl_amount_spent), 2)   AS spend,
  SUM(qt_impressions)              AS impressions,
  SUM(qt_outbound_clicks)          AS clicks
FROM `{TABLE}`
WHERE nm_campaign_name IN (
  '[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v2',
  '[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v3',
  '[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | ios'
)
GROUP BY 1, 2
ORDER BY 2, 1
"""

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

def build() -> dict:
    print("  diário por campanha...", flush=True)
    rows = bq(Q_DIARIO)

    # indexar por (data, campanha)
    by_date_camp: dict[tuple, dict] = {}
    for r in rows:
        k = (r["reference_date"], r["nm_campaign_name"])
        by_date_camp[k] = {
            "spend":       fi(r["spend"]),
            "impressions": ii(r["impressions"]),
            "clicks":      ii(r["clicks"]),
        }

    # datas únicas ordenadas
    dates = sorted({r["reference_date"] for r in rows})
    labels = [d[5:] for d in dates]  # "YYYY-MM-DD" → "MM-DD"
    labels = [f"{d[8:10]}/{d[5:7]}" for d in dates]  # "DD/MM"

    def serie(camp_name, campo):
        return [
            by_date_camp.get((d, camp_name), {}).get(campo, None)
            for d in dates
        ]

    ios_key = "[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | ios"
    av2_key = "[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v2"
    av3_key = "[LAN] [ELS] [ENGAJAMENTO] [APP] Junho | Android v3"

    def totais_camp(key):
        sp = sum(v["spend"]       for k, v in by_date_camp.items() if k[1] == key)
        im = sum(v["impressions"] for k, v in by_date_camp.items() if k[1] == key)
        cl = sum(v["clicks"]      for k, v in by_date_camp.items() if k[1] == key)
        ds = len({k[0] for k in by_date_camp if k[1] == key})
        return sp, im, cl, ds

    ios_sp, ios_im, ios_cl, ios_ds = totais_camp(ios_key)
    av2_sp, av2_im, av2_cl, av2_ds = totais_camp(av2_key)
    av3_sp, av3_im, av3_cl, av3_ds = totais_camp(av3_key)

    total_sp = ios_sp + av2_sp + av3_sp
    total_im = ios_im + av2_im + av3_im
    total_cl = ios_cl + av2_cl + av3_cl

    def ctr(cl, im): return round(cl / im * 100, 4) if im else 0
    def cpc(sp, cl): return round(sp / cl, 2) if cl else 0
    def cpm(sp, im): return round(sp / im * 1000, 2) if im else 0

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "campaign":   "ELS App Engajamento Junho",
        "totais": {
            "spend":       round(total_sp, 2),
            "impressions": total_im,
            "clicks":      total_cl,
            "ctr":         ctr(total_cl, total_im),
            "cpc":         cpc(total_sp, total_cl),
            "cpm":         cpm(total_sp, total_im),
        },
        "campanhas": [
            {
                "nome":       ios_key,
                "nome_curto": "iOS",
                "spend":      round(ios_sp, 2),
                "impressions": ios_im,
                "clicks":     ios_cl,
                "ctr":        ctr(ios_cl, ios_im),
                "cpc":        cpc(ios_sp, ios_cl),
                "cpm":        cpm(ios_sp, ios_im),
                "dias":       ios_ds,
                "sem_dados":  ios_ds == 0,
            },
            {
                "nome":       av2_key,
                "nome_curto": "Android v2",
                "spend":      round(av2_sp, 2),
                "impressions": av2_im,
                "clicks":     av2_cl,
                "ctr":        ctr(av2_cl, av2_im),
                "cpc":        cpc(av2_sp, av2_cl),
                "cpm":        cpm(av2_sp, av2_im),
                "dias":       av2_ds,
                "sem_dados":  av2_ds == 0,
            },
            {
                "nome":       av3_key,
                "nome_curto": "Android v3",
                "spend":      round(av3_sp, 2),
                "impressions": av3_im,
                "clicks":     av3_cl,
                "ctr":        ctr(av3_cl, av3_im),
                "cpc":        cpc(av3_sp, av3_cl),
                "cpm":        cpm(av3_sp, av3_im),
                "dias":       av3_ds,
                "sem_dados":  av3_ds == 0,
            },
        ],
        "diario": {
            "labels":                labels,
            "ios_spend":             serie(ios_key, "spend"),
            "android_v2_spend":      serie(av2_key, "spend"),
            "android_v3_spend":      serie(av3_key, "spend"),
            "ios_impressions":       serie(ios_key, "impressions"),
            "android_v2_impressions": serie(av2_key, "impressions"),
            "ios_clicks":            serie(ios_key, "clicks"),
            "android_v2_clicks":     serie(av2_key, "clicks"),
        },
    }

if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing ELS App Engajamento from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: ELS app-engajamento refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
