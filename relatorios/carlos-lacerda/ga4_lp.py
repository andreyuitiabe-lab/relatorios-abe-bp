#!/usr/bin/env python3
"""Visitas de LP por dia (GA4) -> stdout JSON.

Roda com o interpretador da .venv do MCP GA4 (~/meu_projeto/BigQuery/mcp-ga4/.venv),
que e onde o google-analytics-data e o token OAuth vivem. Chamado pelo refresh.py.
Uso: <python da venv> ga4_lp.py '<json com janelas>' '<json com paths>'
"""
import json, sys, datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / "meu_projeto/BigQuery/mcp-ga4"))
from auth import get_credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

JANELAS, LP = json.loads(sys.argv[1]), json.loads(sys.argv[2])
PROPERTY = sys.argv[3]

client = BetaAnalyticsDataClient(credentials=get_credentials())
out = []
for sigla, j in JANELAS.items():
    resp = client.run_report(RunReportRequest(
        property=f"properties/{PROPERTY}",
        dimensions=[Dimension(name="date"), Dimension(name="pagePath")],
        metrics=[Metric(name="screenPageViews"), Metric(name="sessions")],
        date_ranges=[DateRange(start_date=j["d1"], end_date=j["d4"])],
        limit=100000,
    ))
    for row in resp.rows:
        dt_raw, path = row.dimension_values[0].value, row.dimension_values[1].value
        if path not in LP or LP[path][0] != sigla:
            continue
        dt = f"{dt_raw[:4]}-{dt_raw[4:6]}-{dt_raw[6:]}"
        out.append({
            "sigla": sigla, "dt": dt,
            "dia": (datetime.date.fromisoformat(dt) - datetime.date.fromisoformat(j["d1"])).days + 1,
            "tipo": LP[path][1], "path": path,
            "pageviews": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        })
print(json.dumps(out, ensure_ascii=False))
