#!/usr/bin/env python3
"""
Atualiza data.json do relatório Apoiador R$ 1,90.

Uso:
  python3 refresh.py      # roda as queries e grava data.json (sem commit)

Cada queries/<nome>.sql tem só o SELECT final; base.sql tem as CTEs comuns (coorte e flags por pessoa).
Saída só com agregados — o repo é público, nada por pessoa entra no data.json.
Queries via cliente Python do BigQuery (ADC, igual ao bqq). Nunca `bq query`.
"""

import json, sys, datetime, warnings
from pathlib import Path

HERE = Path(__file__).parent
Q = HERE / "queries"
OUT = HERE / "data.json"
NOMES = ["resumo", "perfil_origem", "semanal", "depois", "consumo", "checkouts"]

_CLIENT = None


def bq(sql: str) -> list[dict]:
    global _CLIENT
    if _CLIENT is None:
        warnings.filterwarnings("ignore")
        from google.cloud import bigquery
        _CLIENT = bigquery.Client(project="bp-datawarehouse")
    rows = _CLIENT.query(sql).result()
    return [dict(r.items()) for r in rows]


def build() -> dict:
    base = (Q / "base.sql").read_text()
    out = {"updated_at": datetime.datetime.now().isoformat(timespec="seconds")}
    for nome in NOMES:
        print(f"  {nome}...", flush=True)
        out[nome] = bq(base + "\n" + (Q / f"{nome}.sql").read_text())
    out["resumo"] = out["resumo"][0]
    return out


if __name__ == "__main__":
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
