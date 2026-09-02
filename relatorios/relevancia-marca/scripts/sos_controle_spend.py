#!/usr/bin/env python3
"""Fase 1.3b — controle de spend no backtest do SoS.

Correlação parcial SoS(t) × transações(t+1) removendo o spend Meta do mês t (z vs MM12).
Fonte de spend: planilha histórica 2022-06→2026-06 (personas_ssr/data/meta_spend_diario.csv)
⚠️ subreporta até −32% vs BQ (auditoria calculadora, sprint 0) — usar como piso; refazer com
spend BQ quando a série ago/2025+ tiver ~2 anos.
"""
import numpy as np, pandas as pd
from scipy import stats
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data"
SPEND = "/Users/andre.abe/meu_projeto/personas_ssr/data/meta_spend_diario.csv"

sos = pd.read_csv(BASE/"share_of_search.csv", parse_dates=["semana"])
sos["mes"] = sos.semana.dt.to_period("M").dt.to_timestamp()
m = sos.groupby("mes")[["sos_midias","sos_streamings","sos_todos","bp"]].mean()
rec = pd.read_csv(BASE/"receita_mensal.csv", parse_dates=["mes"]).set_index("mes")
df = m.join(rec, how="inner").iloc[:-1]

s = pd.read_csv(SPEND, parse_dates=[0])
s["mes"] = pd.to_datetime(s[s.columns[0]]).dt.to_period("M").dt.to_timestamp()
d2 = df.join(s.groupby("mes")[s.columns[-1]].sum().rename("spend_meta"), how="inner")
d2 = d2[d2.spend_meta > 0]

def zmm12(x):
    return (x - x.rolling(12, min_periods=6).mean()) / x.rolling(12, min_periods=6).std()

print(f"n = {len(d2)} meses com spend")
for sc in ["sos_midias","sos_streamings","sos_todos","bp"]:
    x, y, z = zmm12(d2[sc]), zmm12(d2["tx"]).shift(-1), zmm12(d2["spend_meta"])
    mk = (x.notna() & y.notna() & z.notna()).values
    xv, yv, zv = x.values[mk], y.values[mk], z.values[mk]
    A = np.vstack([np.ones(mk.sum()), zv]).T
    rx = xv - A @ np.linalg.lstsq(A, xv, rcond=None)[0]
    ry = yv - A @ np.linalg.lstsq(A, yv, rcond=None)[0]
    rb, _ = stats.spearmanr(xv, yv)
    rp, pp = stats.spearmanr(rx, ry)
    print(f"  {sc:16s} L1 bruta {rb:+.2f} -> parcial(-spend) {rp:+.2f}{'*' if pp<0.05 else ''} (n={int(mk.sum())})")
