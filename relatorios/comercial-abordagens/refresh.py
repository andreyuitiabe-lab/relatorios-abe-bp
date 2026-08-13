#!/usr/bin/env python3
"""
Refresh — Pulso da abordagem do Comercial (últimos 14 dias completos vs 14 anteriores).

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Janela dinâmica: D-14..D-1 (dias completos, até ontem) vs D-28..D-15.
Método "o que o time oferece": menção ao tema na transcrição da conversa
(masterdata.dim_zenvia_approaches.nm_conversation, regex) — mesmo método
validado na análise odisseia-lancamento. Uma conversa pode citar vários temas.
As queries canônicas estão em queries/*.sql — manter em sincronia.
"""

import json, subprocess, sys, datetime
from pathlib import Path

HOJE = datetime.date.today()
FIM = HOJE - datetime.timedelta(days=1)          # último dia completo
INI = HOJE - datetime.timedelta(days=14)         # início da janela atual
INI_PREV = HOJE - datetime.timedelta(days=28)    # início da janela anterior
FIM_PREV = HOJE - datetime.timedelta(days=15)    # fim da janela anterior
OUT = Path(__file__).parent / "data.json"

TEMAS = {
    "odisseia": r"odiss[eé]ia",
    "cdl": r"clube do livro",
    "bp10": r"10 anos|dez anos|anivers[aá]rio",
    "vitalicio": r"vital[ií]cio",
    "mecenas": r"mecenas",
}

PRODUTO_CASE = """
  CASE
    WHEN nm_gateway_plan='clube-do-livro' OR nm_gateway_plan LIKE 'ebooks%clube%' THEN 'Clube do Livro'
    WHEN nm_gateway_plan='livro-odisseia-edicao-colecionador'
      OR LOWER(nm_gateway_product) LIKE '%odis%' THEN 'Odisseia'
    WHEN nm_gateway_plan LIKE 'mecenas%' THEN 'Mecenas'
    WHEN bl_lifetime_offer THEN 'Vitalício'
    ELSE 'Assinaturas/outros'
  END
"""


def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         "--project_id=bp-datawarehouse", f"--max_rows={max_rows}", sql],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    out = r.stdout.strip()
    return json.loads(out) if out else []


def fi(v):
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def ii(v):
    try: return int(float(v)) if v not in (None, "", "null") else 0
    except: return 0


TEMAS_COUNTIF = ",\n       ".join(
    f"COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'{rx}')) AS {k}"
    for k, rx in TEMAS.items()
)

Q_DIARIO = f"""
SELECT DATE(dt_approach_start) AS dia,
       COUNT(*) AS abordagens,
       COUNT(DISTINCT id_seller) AS vendedores,
       {TEMAS_COUNTIF}
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '{INI_PREV}' AND '{FIM}'
GROUP BY 1 ORDER BY 1
"""

Q_VENDAS_DIA = f"""
SELECT DATE(dt_ordered_at) AS dia,
       {PRODUTO_CASE} AS produto,
       COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND DATE(dt_ordered_at) BETWEEN '{INI_PREV}' AND '{FIM}'
GROUP BY 1,2 ORDER BY 1,2
"""

Q_STAGES = f"""
SELECT COALESCE(nm_stage, '(sem etapa)') AS stage, COUNT(*) AS abordagens
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '{INI}' AND '{FIM}'
GROUP BY 1 ORDER BY 2 DESC LIMIT 12
"""

Q_STAGES_ODI = f"""
SELECT COALESCE(nm_stage, '(sem etapa)') AS stage, COUNT(*) AS conversas
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '{INI}' AND '{FIM}'
  AND REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')
GROUP BY 1 ORDER BY 2 DESC LIMIT 8
"""


def build() -> dict:
    print("  série diária (abordagens + temas)...", flush=True)
    diario_rows = bq(Q_DIARIO)
    dias = [(INI_PREV + datetime.timedelta(days=i)).isoformat()
            for i in range((FIM - INI_PREV).days + 1)]
    base = {d: {"abordagens": 0, "vendedores": 0, **{k: 0 for k in TEMAS}} for d in dias}
    for r in diario_rows:
        d = r["dia"]
        if d in base:
            base[d]["abordagens"] = ii(r["abordagens"])
            base[d]["vendedores"] = ii(r["vendedores"])
            for k in TEMAS:
                base[d][k] = ii(r[k])
    diario = [{"dia": d, **base[d]} for d in dias]

    print("  vendas comerciais por dia/produto...", flush=True)
    vendas_rows = bq(Q_VENDAS_DIA)
    produtos = ["Odisseia", "Clube do Livro", "Vitalício", "Mecenas", "Assinaturas/outros"]
    vendas_dia = {d: {p: {"vendas": 0, "receita": 0.0} for p in produtos} for d in dias}
    for r in vendas_rows:
        d, p = r["dia"], r["produto"]
        if d in vendas_dia and p in vendas_dia[d]:
            vendas_dia[d][p] = {"vendas": ii(r["vendas"]), "receita": fi(r["receita"])}
    vendas = [{"dia": d, **{p: vendas_dia[d][p] for p in produtos}} for d in dias]

    # agregados por janela (atual = últimos 14, anterior = 14 antes)
    corte = INI.isoformat()
    def janela(rows, key):
        return [r for r in rows if (r["dia"] >= corte) == (key == "atual")]

    resumo = {}
    for key in ("atual", "anterior"):
        dd = janela(diario, key)
        vv = janela(vendas, key)
        tot_v = {p: sum(r[p]["vendas"] for r in vv) for p in produtos}
        tot_r = {p: sum(r[p]["receita"] for r in vv) for p in produtos}
        resumo[key] = {
            "abordagens": sum(r["abordagens"] for r in dd),
            "vendedores_pico": max((r["vendedores"] for r in dd), default=0),
            "mencoes": {k: sum(r[k] for r in dd) for k in TEMAS},
            "vendas": tot_v, "receita": tot_r,
            "vendas_total": sum(tot_v.values()), "receita_total": sum(tot_r.values()),
        }

    # conversão por conversa (aprox.): vendas do produto / conversas que mencionam o tema
    conv = {}
    mapa = {"odisseia": "Odisseia", "cdl": "Clube do Livro",
            "vitalicio": "Vitalício", "mecenas": "Mecenas"}
    for tema, prod in mapa.items():
        m = resumo["atual"]["mencoes"][tema]
        v = resumo["atual"]["vendas"][prod]
        conv[tema] = {"mencoes": m, "vendas": v,
                      "taxa_pct": round(100 * v / m, 1) if m else None}

    print("  etapas das conversas...", flush=True)
    stages = [{"stage": r["stage"], "abordagens": ii(r["abordagens"])} for r in bq(Q_STAGES)]
    stages_odi = [{"stage": r["stage"], "conversas": ii(r["conversas"])} for r in bq(Q_STAGES_ODI)]

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "config": {"ini": INI.isoformat(), "fim": FIM.isoformat(),
                   "ini_prev": INI_PREV.isoformat(), "fim_prev": FIM_PREV.isoformat(),
                   "produtos": produtos, "temas": list(TEMAS)},
        "diario": diario,
        "vendas": vendas,
        "resumo": resumo,
        "conversao": conv,
        "stages": stages,
        "stages_odisseia": stages_odi,
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing comercial-abordagens data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: comercial-abordagens refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
