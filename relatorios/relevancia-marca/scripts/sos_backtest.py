#!/usr/bin/env python3
"""Backtest do Share of Search (Fase 1.3): SoS mensal vs receita/vendas, lead 0–6 meses.

Duas transformações para matar tendência espúria (60 meses):
  (a) Δlog MoM — movimento curto;
  (b) z-score vs média móvel 12m — desvio do regime, preserva ciclos médios.
Referência de leitura: IPA/Hankins reporta lead de 6–12 meses em market share; nosso alvo
é a própria receita (não temos share externo), então esperamos leads mais curtos.
"""
import numpy as np, pandas as pd
from pathlib import Path
from scipy import stats

BASE = Path(__file__).resolve().parent.parent / "data"

sos = pd.read_csv(BASE/"share_of_search.csv", parse_dates=["semana"])
sos["mes"] = sos.semana.dt.to_period("M").dt.to_timestamp()
m_sos = sos.groupby("mes")[["sos_midias","sos_streamings","sos_todos","bp"]].mean()

rec = pd.read_csv(BASE/"receita_mensal.csv", parse_dates=["mes"]).set_index("mes")
df = m_sos.join(rec, how="inner").iloc[:-1]   # descarta mês corrente (parcial)
print(f"painel mensal: {len(df)} meses ({df.index.min():%Y-%m} → {df.index.max():%Y-%m})\n")

def dlog(s): return np.log(s.replace(0,np.nan)).diff()
def zmm12(s): 
    mm = s.rolling(12, min_periods=6).mean(); sd = s.rolling(12, min_periods=6).std()
    return (s - mm) / sd

ALVOS = {"receita":"Receita total", "tx":"Transações", "primeiras_compras":"Primeiras compras",
         "receita_novos":"Receita de novos"}
SOS = {"sos_midias":"SoS mídias", "sos_streamings":"SoS streamings", "sos_todos":"SoS todos",
       "bp":"Busca BP absoluta (sem denominador)"}

for tf_nome, tf in [("Δlog MoM", dlog), ("z vs MM12", zmm12)]:
    print("="*100)
    print(f"TRANSFORMAÇÃO: {tf_nome} — Spearman SoS(t) × alvo(t+lead), * p<0,05")
    print("="*100)
    header = f"{'indicador':<38}{'alvo':<20}" + "".join(f"{'L'+str(l):>9}" for l in range(0,7))
    print(header); print("-"*len(header))
    for sc, sn in SOS.items():
        x = tf(df[sc])
        for ac, an in ALVOS.items():
            y = tf(df[ac])
            row = f"{sn:<38}{an:<20}"
            for lead in range(0,7):
                yy = y.shift(-lead)
                m = x.notna() & yy.notna()
                if m.sum() < 24: row += f"{'—':>9}"; continue
                r,p = stats.spearmanr(x[m], yy[m])
                row += f"{r:>+8.2f}{'*' if p<0.05 else ' '}"
            print(row)
        print()
