#!/usr/bin/env python3
"""Fatia vs bolo: busca_BP = SoS × tamanho_da_categoria.

Pergunta do André: 'vale mais um pedaço de um bolo grande do que um bolo pequeno inteiro?'
Decompõe log(BP) = log(SoS) + log(categoria) e testa qual componente anda com vendas.
⚠️ Trends é índice relativo — o 'bolo' aqui é o índice da categoria na escala encadeada, não
volume absoluto (isso exigiria Keyword Planner / Search Console).
"""
import numpy as np, pandas as pd
from scipy import stats
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent / "data"

sos = pd.read_csv(BASE/"share_of_search.csv", parse_dates=["semana"])
MID = ["jovem pan","revista oeste","gazeta do povo","o antagonista"]
STR = ["netflix","prime video","globoplay","disney plus"]
sos["bolo_midias"] = sos.bp + sos[MID].sum(axis=1)
sos["bolo_todos"]  = sos.bp + sos[MID+STR].sum(axis=1)
sos["mes"] = sos.semana.dt.to_period("M").dt.to_timestamp()
m = sos.groupby("mes")[["bp","sos_midias","sos_todos","bolo_midias","bolo_todos"]].mean()

rec = pd.read_csv(BASE/"receita_mensal.csv", parse_dates=["mes"]).set_index("mes")
sp = pd.read_csv("/Users/andre.abe/meu_projeto/personas_ssr/data/meta_spend_diario.csv", parse_dates=[0])
sp["mes"] = pd.to_datetime(sp["dia"]).dt.to_period("M").dt.to_timestamp()
d = m.join(rec, how="inner").join(sp.groupby("mes")["spend_meta"].sum().rename("spend"), how="inner")
d = d[d.spend>0].iloc[:-1]

# ---- 1. decomposição de variância: o que move a busca da BP? ----
print("="*92)
print("1) DECOMPOSIÇÃO — log(BP) = log(SoS) + log(bolo)  |  variação MoM, 48 meses")
print("="*92)
for tag, sc, bc in [("mídias","sos_midias","bolo_midias"),("todos","sos_todos","bolo_todos")]:
    dl_bp = np.log(d.bp).diff(); dl_sos = np.log(d[sc]).diff(); dl_bolo = np.log(d[bc]).diff()
    ok = dl_bp.notna()
    cov_s = np.cov(dl_sos[ok], dl_bp[ok])[0,1]; cov_b = np.cov(dl_bolo[ok], dl_bp[ok])[0,1]
    var = dl_bp[ok].var()
    print(f"  categoria {tag:7s}: da variação da busca BP, {100*cov_s/var:5.1f}% vem da FATIA (SoS) e "
          f"{100*cov_b/var:5.1f}% do BOLO (categoria)  | corr(ΔSoS, Δbolo) = {np.corrcoef(dl_sos[ok], dl_bolo[ok])[0,1]:+.2f}")

# ---- 2. o episódio recente: SoS-mídias 7,6% -> 12,2% ----
print("\n"+"="*92)
print("2) EPISÓDIO RECENTE — SoS-mídias subiu para 12,2%: BP cresceu ou o bolo encolheu?")
print("="*92)
w = sos.set_index("semana")
ult = w.tail(4); hist = w.iloc[:-4]
for c, n in [("bp","busca BP"),("bolo_midias","bolo mídias (BP+4)"),("sos_midias","SoS mídias %")]:
    print(f"  {n:22s} histórico {hist[c].mean():9.2f}  |  últimas 4 sem {ult[c].mean():9.2f}  ->  {100*(ult[c].mean()/hist[c].mean()-1):+.0f}%")
for c in MID:
    print(f"    {c:20s} histórico {hist[c].mean():8.2f}  |  últimas 4 sem {ult[c].mean():8.2f}  ->  {100*(ult[c].mean()/hist[c].mean()-1):+.0f}%")

# ---- 3. qual componente anda com vendas (contemporâneo, controlado por spend) ----
print("\n"+"="*92)
print("3) QUAL COMPONENTE ANDA COM VENDAS — z vs MM12, contemporâneo, parcial controlando spend(t)")
print("="*92)
def z(x): return (x-x.rolling(12,min_periods=6).mean())/x.rolling(12,min_periods=6).std()
def parcial(x,y,c):
    mk = x.notna()&y.notna()&c.notna()
    A = np.vstack([np.ones(mk.sum()), c[mk].values]).T
    rx = x[mk].values - A@np.linalg.lstsq(A,x[mk].values,rcond=None)[0]
    ry = y[mk].values - A@np.linalg.lstsq(A,y[mk].values,rcond=None)[0]
    return stats.spearmanr(rx,ry)
zs = z(d.spend)
print(f"  {'componente':<26}{'× transações':>14}{'× receita':>12}{'× CAC':>10}{'× ticket':>11}")
d["cac"] = d.spend/d.tx; d["ticket"] = d.receita/d.tx
for c, n in [("bp","Busca BP (fatia×bolo)"),("sos_todos","Fatia: SoS todos"),("bolo_todos","Bolo: categoria todos"),
             ("sos_midias","Fatia: SoS mídias"),("bolo_midias","Bolo: categoria mídias")]:
    row = f"  {n:<26}"
    for a in ["tx","receita","cac","ticket"]:
        r,p = parcial(z(d[c]), z(d[a]), zs)
        row += f"{r:>+11.2f}{'*' if p<0.05 else ' '}"
    print(row)
print("\n  * p<0,05. Leitura: se a FATIA anda com vendas e o BOLO não, o share carrega o sinal;")
print("  se ambos andam, o que importa é a busca absoluta (fatia × bolo) — e o share sozinho engana.")
