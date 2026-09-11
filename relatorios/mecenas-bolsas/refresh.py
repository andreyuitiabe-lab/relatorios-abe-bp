#!/usr/bin/env python3
"""
Mecenas — Bolsas: vendidas × distribuídas.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Queries canônicas em queries/*.sql (se corrigir, atualizar o arquivo — não criar novo).
Roda via `bqq` (ADC — não expira; nunca usar `bq query`).
"""

import csv
import datetime
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data.json"
QDIR = HERE / "queries"

# Lado beneficiário fora do BQ: controle antigo do CS em planilha (Google Sheets
# "Mecenas — controle de instituições", aba de instituições, ref. 04/03/2026).
PLANILHA = {
    "ref": "2026-03-04",
    "beneficiados": 25169,
    "instituicoes": 235,
    "beneficiados_ativos": 3378,
    "instituicoes_ativas": 74,
}


def bqq(sql_file: str) -> list[dict]:
    """Roda queries/<sql_file> no BigQuery via bqq e devolve lista de dicts (valores str)."""
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        out = f.name
    r = subprocess.run(["bqq", str(QDIR / sql_file), "-o", out, "-n", "1"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{sql_file}: {r.stderr.strip()[-2000:]}")
    return list(csv.DictReader(open(out, encoding="utf-8")))


def f(v):
    try:
        return float(v) if v not in (None, "", "null", "NaN", "nan") else 0.0
    except (TypeError, ValueError):
        return 0.0


def i(v):
    return int(f(v))


def build() -> dict:
    print("  01 vendas por ano × tipo...", flush=True)
    vendas = bqq("01_vendas_bolsas.sql")
    print("  02 vendas sem número...", flush=True)
    sem_numero = bqq("02_vendas_sem_numero.sql")
    print("  03 distribuição por ano × sistema...", flush=True)
    dist = bqq("03_distribuicao.sql")
    print("  04 instituições...", flush=True)
    inst = bqq("04_instituicoes.sql")
    print("  05 totais...", flush=True)
    tot = bqq("05_totais.sql")[0]
    print("  06 por produto...", flush=True)
    produtos = bqq("06_por_produto.sql")

    # ── vendas: pivot ano → {padrao, certificacao} ────────────────────────────
    anos = sorted({i(r["ano"]) for r in vendas if r["ano"] not in ("", "null")})
    v_ano = {a: {"padrao": 0, "certificacao": 0, "receita": 0.0, "tx": 0} for a in anos}
    tipo_tot = {"padrao": {"bolsas": 0, "tx": 0, "receita": 0.0, "contas": 0},
                "certificacao": {"bolsas": 0, "tx": 0, "receita": 0.0, "contas": 0}}
    for r in vendas:
        if r["ano"] in ("", "null"):
            continue
        a, t = i(r["ano"]), r["tipo"]
        v_ano[a][t] += i(r["qt_bolsas"])
        v_ano[a]["receita"] += f(r["vl_receita"])
        v_ano[a]["tx"] += i(r["qt_tx"])
        tipo_tot[t]["bolsas"] += i(r["qt_bolsas"])
        tipo_tot[t]["tx"] += i(r["qt_tx"])
        tipo_tot[t]["receita"] += f(r["vl_receita"])
        tipo_tot[t]["contas"] += i(r["qt_contas"])  # soma de contas/ano ≠ distintas; KPI usa 05

    # ── distribuição: pivot ano → ativadas/vigentes; sistemas agregados ───────
    d_ano = {}
    sistemas = {}
    for r in dist:
        a = i(r["ano"]) if r["ano"] not in ("", "null") else None
        s = r["sistema"]
        if a is not None:
            d = d_ano.setdefault(a, {"assinaturas": 0, "contas": 0, "vigentes": 0})
            d["assinaturas"] += i(r["qt_assinaturas"])
            d["contas"] += i(r["qt_contas"])
            d["vigentes"] += i(r["qt_vigentes"])
        ss = sistemas.setdefault(s, {"assinaturas": 0, "vigentes": 0, "anos": []})
        ss["assinaturas"] += i(r["qt_assinaturas"])
        ss["vigentes"] += i(r["qt_vigentes"])
        if a is not None:
            ss["anos"].append(a)

    todos_anos = sorted(set(anos) | set(d_ano))

    sem_num_tot = {
        "tx": sum(i(r["qt_tx"]) for r in sem_numero),
        "receita": round(sum(f(r["vl_receita"]) for r in sem_numero), 2),
        "est_min": sum(i(r["qt_bolsas_est_min"]) for r in sem_numero),
        "est_max": sum(i(r["qt_bolsas_est_max"]) for r in sem_numero),
        "top": [{"oferta": r["oferta"], "tx": i(r["qt_tx"]), "receita": f(r["vl_receita"])}
                for r in sem_numero[:6]],
    }

    total_dist_subs = sum(i(r["qt_assinaturas"]) for r in dist)
    total_vig_subs = sum(i(r["qt_vigentes"]) for r in dist)
    total_vig_contas = i(tot["qt_contas_vigentes"])  # distinto (soma por ano duplicaria)

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "kpi": {
            "bolsas_vendidas": tipo_tot["padrao"]["bolsas"] + tipo_tot["certificacao"]["bolsas"],
            "receita": round(tipo_tot["padrao"]["receita"] + tipo_tot["certificacao"]["receita"], 2),
            "contas_doadoras": i(tot["qt_contas_doadoras"]),
            "assinaturas_ativadas": total_dist_subs,
            "contas_beneficiarias": i(tot["qt_contas_beneficiarias"]),
            "vigentes_assinaturas": total_vig_subs,
            "vigentes_contas": total_vig_contas,
        },
        "vendas_tipo": [
            {"tipo": t, **{k: (round(v, 2) if k == "receita" else v) for k, v in d.items()}}
            for t, d in tipo_tot.items()
        ],
        "ano": [
            {
                "ano": a,
                "vendidas": v_ano.get(a, {}).get("padrao", 0) + v_ano.get(a, {}).get("certificacao", 0),
                "vendidas_padrao": v_ano.get(a, {}).get("padrao", 0),
                "vendidas_cert": v_ano.get(a, {}).get("certificacao", 0),
                "receita": round(v_ano.get(a, {}).get("receita", 0.0), 2),
                "ativadas": d_ano.get(a, {}).get("assinaturas", 0),
                "vigentes": d_ano.get(a, {}).get("vigentes", 0),
            }
            for a in todos_anos
        ],
        "sem_numero": sem_num_tot,
        "produtos": [
            {"produto": r["produto"], "vendidas": i(r["qt_bolsas_vendidas"]),
             "receita": f(r["vl_receita"]), "distribuidas": i(r["qt_assinaturas_distribuidas"]),
             "vigentes": i(r["qt_vigentes"])}
            for r in produtos
        ],
        "sistemas": [
            {"sistema": s, "assinaturas": d["assinaturas"], "vigentes": d["vigentes"],
             "periodo": f"{min(d['anos'])}–{max(d['anos'])}" if d["anos"] else "—"}
            for s, d in sorted(sistemas.items(), key=lambda kv: -kv[1]["assinaturas"])
        ],
        "instituicoes": {
            "contas_com_instituicao": i(tot["qt_contas_com_instituicao"]),
            "contas_total": i(tot["qt_contas_beneficiarias"]),
            "top": [{"inst": r["inst"], "contas": i(r["qt_contas"])} for r in inst[:15]],
        },
        "planilha": PLANILHA,
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing mecenas-bolsas data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m",
                            f"data: mecenas-bolsas refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
