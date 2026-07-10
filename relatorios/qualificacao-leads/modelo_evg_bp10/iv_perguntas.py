"""Leaderboard de perguntas da pesquisa: cobertura, IV (Information Value) e WOE por resposta.
Segmento: Não Membros (onde a pesquisa é o único sinal). Dataset EVG/BP10.
WOE com suavização Laplace (0.5) para células pequenas.
"""
import numpy as np
import pandas as pd

DATA = "/Users/andre.abe/meu_projeto/relatorios-abe-bp/relatorios/qualificacao-leads/modelo_evg_bp10/dataset_evg_bp10.csv"
QUESTIONS = ["renda", "relacao_bp", "tempo_conhece_bp", "fonte_confianca",
             "qtd_streaming", "streaming", "midia_tradicional", "religiao"]

df = pd.read_csv(DATA)
nm = df[df["st_member_status_at_registration"].eq("Não Membro")].copy()
y = nm["conv"].astype(int)
print(f"NM: {len(nm):,} leads | {y.sum()} conversões | base {y.mean():.3%}\n")

def woe_iv(series, target, incluir_na=True):
    s = series.astype("object").where(series.notna(), "__sem_resposta__") if incluir_na else series
    d = pd.DataFrame({"resp": s, "conv": target}).dropna(subset=["resp"])
    tot_conv, tot_nconv = d["conv"].sum(), (1 - d["conv"]).sum()
    g = d.groupby("resp").agg(n=("conv", "size"), conv=("conv", "sum"))
    g["nconv"] = g["n"] - g["conv"]
    g["pct_pop"] = g["n"] / g["n"].sum()
    g["taxa_conv"] = g["conv"] / g["n"]
    g["lift"] = g["taxa_conv"] / (tot_conv / (tot_conv + tot_nconv))
    # WOE suavizado
    g["pct_conv"] = (g["conv"] + 0.5) / (tot_conv + 0.5 * len(g))
    g["pct_nconv"] = (g["nconv"] + 0.5) / (tot_nconv + 0.5 * len(g))
    g["woe"] = np.log(g["pct_conv"] / g["pct_nconv"])
    g["iv_contrib"] = (g["pct_conv"] - g["pct_nconv"]) * g["woe"]
    return g, g["iv_contrib"].sum()

rows = []
for q in QUESTIONS:
    cobertura = nm[q].notna().mean()
    _, iv_total = woe_iv(nm[q], y, incluir_na=True)          # inclui não-resposta como nível
    g_resp, iv_resp = woe_iv(nm[q][nm[q].notna()], y[nm[q].notna()], incluir_na=False)
    rows.append({"pergunta": q, "cobertura_pct": round(cobertura * 100, 1),
                 "iv_total": round(iv_total, 3), "iv_entre_respondentes": round(iv_resp, 3),
                 "n_niveis": nm[q].nunique()})

lb = pd.DataFrame(rows).sort_values("iv_total", ascending=False)
print("=== LEADERBOARD DE PERGUNTAS (NM) ===")
print("iv_total inclui 'sem resposta' como nível (captura cobertura + separação)")
print(lb.to_string(index=False))
print("\nRégua IV: <0,02 inútil | 0,02–0,1 fraca | 0,1–0,3 média | 0,3–0,5 forte | >0,5 suspeita (vazamento)")

# detalhe das 3 melhores
print("\n=== WOE POR RESPOSTA (top 3 perguntas) ===")
for q in lb.head(3)["pergunta"]:
    g, iv = woe_iv(nm[q], y, incluir_na=True)
    g = g.sort_values("woe", ascending=False)
    print(f"\n--- {q} (IV={iv:.3f}) ---")
    print(g[["n", "pct_pop", "taxa_conv", "lift", "woe"]].round(
        {"pct_pop": 3, "taxa_conv": 4, "lift": 2, "woe": 2}).to_string())
