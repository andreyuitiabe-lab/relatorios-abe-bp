#!/usr/bin/env python3
"""
Clubinho do Livro BP — recepção de planos e preços (SSR) + benchmark do Clube do Livro.

Uso:
  python refresh.py          # atualiza data.json (passo padrão)
  python refresh.py --push   # atualiza + git add/commit/push — só com ok do André

Duas fontes:
  1. BigQuery: mix de planos do CdL (queries/cdl_mix_planos.sql), via cliente Python (ADC).
  2. SSR: consolidado local das 3 sessões (personas_ssr/output/clubinho_ssr_set2026_consolidado.csv).
     O CSV tem id_user e fica fora do repo; aqui entram só agregados e respostas sintéticas.
"""

import json, subprocess, sys, datetime, warnings
from pathlib import Path

HERE = Path(__file__).parent
OUT  = HERE / "data.json"
SSR  = Path.home() / "meu_projeto/personas_ssr/output/clubinho_ssr_set2026_consolidado.csv"

BRACOS = {  # preço mensal Desbravador / Navegante / Completa
    "A": (69.90, 79.90, 89.90),
    "B": (79.90, 89.90, 99.90),
    "C": (89.90, 99.90, 109.90),
}
PLANOS = ["Desbravador", "Navegante", "Completa"]
RENDAS = ["alta", "media", "baixa"]

# ─── premissas de julgamento (não saem de dado; revisar à mão) ────────────────
# Divisão estimada para o P&L: ponderação entre "considera" (score>=3) e "decidido" (4–5),
# puxada para o "considera" porque o SSR superestima o entusiasmo da alta renda.
MIX_PL   = {"Desbravador": 45, "Navegante": 30, "Completa": 25}
BANDA_PL = {"Desbravador": "35–55%", "Navegante": "25–35%", "Completa": "20–35%"}
# Volume calibrado por produtos com score de alta renda parecido (Odisseia 3,30 → ~3.800 reais).
CENARIOS = [("Conservador", 1500), ("Referência", 3000), ("Otimista", 5000)]

TEMAS = {  # regex sobre a resposta sintética
    "Preço / peso do total anual":         r"caro|preço|pesa|orçamento|apertad|mil|anual|1\.?\d{3}",
    "Cita neto(a) ou presente":            r"presente|neto",
    "Conteúdo: história do Brasil, valores": r"história do brasil|valores|virtude|heró|patri",
    "Sem criança de 4–8 na família":       r"não tenho (filho|neto|criança)|sem (filho|neto)|já crescid|já são grandes|adult",
    "Jogos online = mais tela":            r"tela|jogos? online|celular|tablet",
    "Trava de 12 meses / querer ver antes": r"amostra|ver antes|experimentar|um livro antes|folhear antes|sem compromisso|cancelar|fidelidade|12 meses|um ano inteiro",
    "Audiobook":                           r"audio|áudio",
    "Livro físico, capa dura, papel":      r"papel|físico|capa dura|tocar|folhear",
}

CITACOES = [  # (rótulo, filtro) — pega a 1ª resposta que casa, preferindo o braço B
    ("Decidido → Completa", lambda d: (d.plano == "Completa") & (d.score_likert >= 4) & d.resposta_ssr.str.contains("audio", case=False)),
    ("Em dúvida → Desbravador", lambda d: (d.plano == "Desbravador") & (d.score_likert == 3) & d.resposta_ssr.str.contains("dispens", case=False)),
    ("Objeção ao Navegante", lambda d: d.resposta_ssr.str.contains(r"tela", case=False) & (d.score_likert <= 3)),
    ("Trava de 12 meses", lambda d: d.resposta_ssr.str.contains(r"12 meses|um ano inteiro|amarrad", case=False) & (d.score_likert == 3)),
    ("Avó, presente", lambda d: d.resposta_ssr.str.contains("presente", case=False) & d.resposta_ssr.str.contains("net", case=False) & (d.score_likert >= 4)),
    ("Fora do público", lambda d: d.resposta_ssr.str.contains(r"não tenho filho", case=False) & (d.score_likert <= 2)),
]

# ─── BQ helper ───────────────────────────────────────────────────────────────
_CLIENT = None

def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    global _CLIENT
    if _CLIENT is None:
        warnings.filterwarnings("ignore")
        from google.cloud import bigquery
        _CLIENT = bigquery.Client(project="bp-datawarehouse")
    rows = _CLIENT.query(sql).result(max_results=max_rows)
    return [{k: (None if v is None else str(v)) for k, v in r.items()} for r in rows]

def r1(x): return round(float(x), 1)

# ─── build ───────────────────────────────────────────────────────────────────
def build_cdl() -> dict:
    print("  CdL: mix de planos (BQ)...", flush=True)
    rows = bq((HERE / "queries/cdl_mix_planos.sql").read_text())
    niveis = ["1 Só físico", "2 Físico + Digital", "3 Ouro (físico + Black Vitalício)"]
    out = {}
    for canal in ["Digital", "Comercial", "Total"]:
        sel = [r for r in rows if canal == "Total" or r["canal"] == canal]
        n = {nv: sum(int(r["pessoas"]) for r in sel if r["nivel"] == nv) for nv in niveis}
        tot = sum(n.values())
        out[canal] = {"n": [n[nv] for nv in niveis], "pct": [r1(100 * n[nv] / tot) for nv in niveis], "total": tot}
    upg = sum(int(r["pessoas"]) for r in rows if r["como"] == "upgrade")
    out["upgrade"] = {"n": upg, "pct": r1(100 * upg / out["Total"]["total"])}
    return out

def build_ssr() -> dict:
    import pandas as pd
    print("  SSR: consolidado local...", flush=True)
    d = pd.read_csv(SSR)
    d["plano"] = d.plano.str.strip().replace({"Coleção Completa": "Completa"})
    d["b"] = d.braco.str[0]
    d["top2"] = d.score_likert >= 4

    score = {b: {**{r: r1(g[g.nm_income_tier == r].score_likert.mean() * 100) / 100 for r in RENDAS},
                 "total": round(g.score_likert.mean(), 2)} for b, g in d.groupby("b")}
    top2 = {b: {**{r: r1(100 * g[g.nm_income_tier == r].top2.mean()) for r in RENDAS},
                "total": r1(100 * g.top2.mean())} for b, g in d.groupby("b")}

    dec = d[(d.plano != "Nenhum") & d.top2]
    con = d[d.plano != "Nenhum"]
    mix = lambda s: [r1(100 * (s.plano == p).mean()) for p in PLANOS]
    mix_dec, mix_con = mix(dec), mix(con)

    # receita por respondente = % top-2 do braço × ticket anual no mix agregado dos decididos
    receita = {}
    for b, (pd_, pn, pc) in BRACOS.items():
        ticket = sum(m / 100 * p * 12 for m, p in zip(mix_dec, (pd_, pn, pc)))
        receita[b] = {"ticket": round(ticket), "top2": top2[b]["total"], "indice": round(top2[b]["total"] / 100 * ticket)}

    # teste pareado de score (mesmas personas)
    w = d.pivot_table("score_likert", "id_user", "b")
    pares = []
    for a, b in [("A", "B"), ("B", "C"), ("A", "C")]:
        dl = w[b] - w[a]
        pares.append({"par": f"{b}−{a}", "delta": round(dl.mean(), 3), "t": round(dl.mean() / (dl.std(ddof=1) / len(dl) ** .5), 2),
                      "piora": int((dl < 0).sum()), "igual": int((dl == 0).sum()), "melhora": int((dl > 0).sum())})

    idade = {a: round(g.score_likert.mean(), 2) for a, g in d.groupby("nm_age_group")}

    temas = []
    for t, p in TEMAS.items():
        m = d.resposta_ssr.str.contains(p, case=False, regex=True)
        temas.append({"tema": t, "pct": r1(100 * m.mean()), "top2": r1(100 * d[m].top2.mean())})
    temas.sort(key=lambda x: -x["pct"])

    citacoes = []
    for rot, f in CITACOES:
        s = d[f(d)].sort_values(["b"], key=lambda c: c.map({"B": 0, "A": 1, "C": 2}))
        s = s[~s.resposta_ssr.isin([c["texto"] for c in citacoes])]  # sem repetir citação
        if len(s):
            r = s.iloc[0]
            citacoes.append({"rotulo": rot, "texto": r.resposta_ssr, "score": int(r.score_likert), "plano": r.plano,
                             "perfil": f"renda {r.nm_income_tier}, {r.nm_age_group.replace('_', '–').replace('–mais', '+')} anos, braço {r.b}"})

    return {"n_personas": int(d.id_user.nunique()), "n_respostas": len(d), "score": score, "top2": top2,
            "mix_decididos": mix_dec, "n_decididos": len(dec), "mix_considera": mix_con, "n_considera": len(con),
            "receita": receita, "pareado": pares, "idade": idade, "temas": temas, "citacoes": citacoes,
            "sem_crianca_pct": next(t["pct"] for t in temas if t["tema"].startswith("Sem criança"))}

def build() -> dict:
    ssr = build_ssr()
    # ticket anual dos cenários = divisão do P&L nos preços do braço B (recomendado)
    tb = sum(MIX_PL[p] / 100 * v * 12 for p, v in zip(PLANOS, BRACOS["B"]))
    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "bracos": {b: list(p) for b, p in BRACOS.items()},
        "planos": PLANOS,
        "cdl": build_cdl(),
        "ssr": ssr,
        "mix_pl": [MIX_PL[p] for p in PLANOS], "banda_pl": [BANDA_PL[p] for p in PLANOS],
        "ticket_cenarios": round(tb), "cenarios": [{"nome": n, "assinaturas": v, "receita_mi": round(v * tb / 1e6, 1)} for n, v in CENARIOS],
    }

# ─── main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing Clubinho report data...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: clubinho refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
