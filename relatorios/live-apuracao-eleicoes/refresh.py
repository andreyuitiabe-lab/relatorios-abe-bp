#!/usr/bin/env python3
"""
Live de apuração das eleições (04/10/2026) — inserções da oferta Black November × LP × vendas.

Usage:
  python refresh.py          # atualiza data.json (passo padrão)

Queries em queries/*.sql rodam via cliente Python do BigQuery (ADC, igual ao ~/bin/bqq).
Os horários das falas não estão no BQ: vêm de falas.json, conferidos na transcrição do vídeo.
"""

import json, datetime, warnings
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data.json"
DIA = "2026-10-04"
JANELA_VENDA_MIN = 30   # vendas atribuídas a uma fala: do bloco da fala até 30 min ou a próxima fala
JANELA_LP_MIN = 15      # views da LP atribuídas a uma fala: 15 min a partir do bloco da fala

_CLIENT = None

def bq(nome: str) -> list[dict]:
    global _CLIENT
    if _CLIENT is None:
        warnings.filterwarnings("ignore")
        from google.cloud import bigquery
        _CLIENT = bigquery.Client(project="bp-datawarehouse")
    sql = (HERE / "queries" / f"{nome}.sql").read_text()
    print(f"  {nome}...", flush=True)
    return [dict(r.items()) for r in _CLIENT.query(sql).result()]

def minutos(hhmm: str) -> int:
    h, m = map(int, hhmm.split(":")); return h * 60 + m

def bloco(m: int) -> str:
    return f"{DIA} {m // 60:02d}:{m % 60:02d}"

def build() -> dict:
    falas = json.loads((HERE / "falas.json").read_text())
    lp = {r["bloco"]: r for r in bq("lp_checkout_5min")}
    vendas = {r["bloco"]: r for r in bq("vendas_5min")}
    diario = bq("vendas_diarias")
    ofertas = bq("ofertas")
    perfil = bq("perfil_cesta")
    funil = bq("funil")[0]

    # série de 5 min, 15:00–23:55 do dia da live
    serie = []
    for m in range(15 * 60, 24 * 60, 5):
        b = bloco(m); l = lp.get(b, {}); v = vendas.get(b, {})
        serie.append({"t": b[-5:], "lp": int(l.get("lp_total") or 0), "lp_live": int(l.get("lp_live") or 0),
                      "checkout": int(l.get("checkout") or 0), "vendas": int(v.get("vendas") or 0),
                      "receita": float(v.get("receita") or 0)})

    # resultado de cada fala
    inicio = [minutos(f["hora"]) // 5 * 5 for f in falas["falas"]]
    por_fala = []
    for i, f in enumerate(falas["falas"]):
        a = inicio[i]
        fim_v = min(a + JANELA_VENDA_MIN, inicio[i + 1] if i + 1 < len(inicio) else 24 * 60)
        blocos_v = [bloco(m) for m in range(a, fim_v, 5)]
        blocos_lp = [bloco(m) for m in range(a, a + JANELA_LP_MIN, 5)]
        antes = [bloco(m) for m in range(a - 15, a, 5)]
        lp_janela = sum(int(lp.get(b, {}).get("lp_total") or 0) for b in blocos_lp)
        vd = sum(int(vendas.get(b, {}).get("vendas") or 0) for b in blocos_v)
        por_fala.append({**f,
            "janela": f"{blocos_v[0][-5:]}–{bloco(fim_v)[-5:]}",
            "lp_antes_5min": round(sum(int(lp.get(b, {}).get("lp_total") or 0) for b in antes) / 3),
            "lp_pico_5min": max(int(lp.get(b, {}).get("lp_total") or 0) for b in blocos_lp),
            "lp_15min": lp_janela,
            "vendas": vd,
            "receita": round(sum(float(vendas.get(b, {}).get("receita") or 0) for b in blocos_v)),
            "vendas_por_100_views": round(100 * vd / lp_janela, 1) if lp_janela else None})

    dia_live = [r for r in vendas if r.startswith(DIA)]
    tot_vendas = sum(int(vendas[b]["vendas"]) for b in vendas)
    tot_receita = sum(float(vendas[b]["receita"]) for b in vendas)
    vendas_dia = sum(int(vendas[b]["vendas"]) for b in dia_live)
    base = [r for r in diario if r["dia"] < DIA]
    vendas_base = sorted(int(r["vendas"]) for r in base)
    compradores = sum(int(r["pessoas"]) for r in perfil)

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "live": {k: falas[k] for k in ("video", "inicio", "fim")},
        "kpis": {
            "vendas": tot_vendas, "receita": round(tot_receita), "vendas_04": vendas_dia,
            "compradores": compradores,
            "vendas_dia_total": next(int(r["vendas"]) for r in diario if r["dia"] == DIA),
            "vendas_dia_mediana_base": vendas_base[len(vendas_base) // 2],
            "pct_em_janela_de_fala": round(100 * sum(f["vendas"] for f in por_fala) / vendas_dia, 1),
            "lp_usuarios": int(funil["lp_usuarios"]), "checkout_usuarios": int(funil["checkout_usuarios"]),
        },
        "serie": serie,
        "falas": por_fala,
        "outras_falas": falas["outras_falas"],
        "picos_sem_fala": falas["picos_sem_fala"],
        "diario": [{"dia": r["dia"], "vendas": int(r["vendas"]), "vendas_live": int(r["vendas_live"]),
                    "receita": float(r["receita"]), "receita_live": float(r["receita_live"])} for r in diario],
        "ofertas": [{"degrau": r["degrau"], "vendas": int(r["vendas"]), "receita": float(r["receita"]),
                     "ticket": float(r["ticket"])} for r in ofertas],
        "perfil": [{"seg": r["seg"], "cesta": r["cesta"], "pessoas": int(r["pessoas"]), "bump_2ano": int(r["bump_2ano"]),
                    "via_comercial": int(r["via_comercial"]), "receita": float(r["receita"])} for r in perfil],
    }

if __name__ == "__main__":
    print("Atualizando live-apuracao-eleicoes...")
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✓ {OUT.name} — {data['updated_at']}")
