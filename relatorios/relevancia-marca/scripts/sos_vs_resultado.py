#!/usr/bin/env python3
"""Rodada 6 — o resultado completo usando Share of Search como indicador de relevância.

Três testes, mesma máquina das rodadas anteriores:
  A) Semanal (spend BQ, 56 sem): correlação residualizada SoS × volume/eficiência, lags 0-2
  B) Quartis Q4 vs Q1 com bootstrap (níveis interpretáveis)
  C) mCAC dos saltos de budget em semanas de SoS alto vs baixo (rodada 3 refeita com SoS)
  D) Mensal longo (2022-2026, spend-planilha como piso): CAC mensal × SoS com leads
"""
import numpy as np, pandas as pd, sys
from pathlib import Path
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import BASE

rng = np.random.default_rng(20260825)

# ---------- dados ----------
sos = pd.read_csv(BASE/"share_of_search.csv", parse_dates=["semana"])
sos["dia"] = sos.semana + pd.Timedelta(days=7)   # Trends rotula início (dom); painel rotula fim
SOS_COLS = ["sos_midias","sos_streamings","sos_todos","bp"]

sem = pd.read_csv(BASE/"painel_semanal.csv", parse_dates=["dia"])
sem = sem.merge(sos[["dia"]+SOS_COLS], on="dia", how="left")

def resid(y, X):
    yl = np.log1p(pd.Series(y).astype(float).clip(lower=0))
    ok = yl.notna() & np.isfinite(yl) & X.notna().all(axis=1)
    b,*_ = np.linalg.lstsq(X[ok].values, yl[ok].values, rcond=None)
    r = yl - X.values @ b; r[~ok] = np.nan
    return r

Xs = pd.get_dummies(sem.dia.dt.month, prefix="m", drop_first=True).astype(float)
Xs["log_spend"] = np.log1p(sem.spend_total)
Xs["trend"] = np.arange(len(sem))/52
Xs.insert(0,"const",1.0)

ALVOS = {"tx_total":"Transações","receita_total":"Receita","tx_organico":"Tx orgânicas",
         "cac_ads":"CAC ads (neg=bom)","roas_dia":"ROAS","conv_por_sessao":"Conv/1k sessões"}

R = {c: resid(sem[c], Xs) for c in list(ALVOS)+SOS_COLS}

print("="*100)
print("A) SEMANAL (56 sem, spend BQ) — Spearman resíduo SoS(t) × resíduo alvo(t+lag), * p<0,05")
print("="*100)
for sc, sn in [("sos_todos","SoS todos"),("sos_midias","SoS mídias"),("bp","Busca BP absoluta")]:
    print(f"\n--- {sn} ---")
    for ac, an in ALVOS.items():
        row = f"  {an:18s}"
        for lag in (0,1,2):
            x, y = R[sc], R[ac].shift(-lag)
            mk = x.notna()&y.notna()
            if mk.sum()<30: row += f"  L{lag}: n<30 "; continue
            r,p = stats.spearmanr(x[mk],y[mk])
            row += f"  L{lag}:{r:+.2f}{'*' if p<0.05 else ' '}"
        print(row)

print("\n"+"="*100)
print("B) QUARTIS — semanas de SoS-todos alto (Q4) vs baixo (Q1), níveis, bootstrap 2000")
print("="*100)
d = sem.copy(); d["r"] = R["sos_todos"]
d = d.dropna(subset=["r"])
q1,q4 = d.r.quantile(.25), d.r.quantile(.75)
alta, baixa = d[d.r>=q4], d[d.r<=q1]
print(f"n: {len(alta)} alta / {len(baixa)} baixa")
for ac,an in ALVOS.items():
    a,b = alta[ac].dropna(), baixa[ac].dropna()
    if len(a)<5: continue
    boots = [rng.choice(a,len(a),True).mean()/rng.choice(b,len(b),True).mean() for _ in range(2000)]
    lo,hi = np.percentile(boots,[2.5,97.5])
    _,p = stats.mannwhitneyu(a,b,alternative="two-sided")
    print(f"  {an:18s} baixa {b.mean():12,.1f}  alta {a.mean():12,.1f}  {100*(a.mean()/b.mean()-1):+6.1f}%"
          f"  p={p:.3f}  IC95[{100*(lo-1):+.0f}%,{100*(hi-1):+.0f}%]")

print("\n"+"="*100)
print("C) mCAC DOS SALTOS DE BUDGET × SoS da semana (rodada 3 refeita com SoS-todos)")
print("="*100)
ev = pd.read_csv(BASE/"mcac_eventos.csv", parse_dates=["dia"])
ev = ev.merge(sos[["semana","sos_todos"]].assign(key=1), how="cross", suffixes=("","_s")) if False else ev
ev = pd.merge_asof(ev.sort_values("dia"), sos[["semana","sos_todos"]].sort_values("semana"),
                   left_on="dia", right_on="semana", direction="backward")
# residualizar SoS da tendência (z vs MM8 semanal) para não confundir com regime
srz = sos.set_index("semana")["sos_todos"]
z = (srz - srz.rolling(8,min_periods=4).mean())/srz.rolling(8,min_periods=4).std()
ev = pd.merge_asof(ev.sort_values("dia"), z.rename("sos_z").reset_index().sort_values("semana"),
                   left_on="dia", right_on="semana", direction="backward")
v = ev[ev.mcac.notna()&(ev.mcac>0)&(ev.mcac<5000)&ev.sos_z.notna()]
for direcao in ("up","down"):
    dd = v[v.direcao==direcao]
    if len(dd)<30: continue
    corte = dd.sos_z.median()
    a,b = dd[dd.sos_z>corte].mcac, dd[dd.sos_z<=corte].mcac
    _,p = stats.mannwhitneyu(a,b,alternative="two-sided")
    rho,pr = stats.spearmanr(dd.sos_z, dd.mcac)
    print(f"  saltos {direcao} (n={len(dd)}): mCAC mediano SoS baixo R$ {b.median():,.0f} | alto R$ {a.median():,.0f}"
          f" -> {100*(a.median()/b.median()-1):+.1f}%  p={p:.3f} | Spearman {rho:+.3f} (p={pr:.3f})")
# só VENDA
vv = v[v.fase=="VENDA"]
for direcao in ("up",):
    dd = vv[vv.direcao==direcao]
    if len(dd)<30: continue
    corte = dd.sos_z.median()
    a,b = dd[dd.sos_z>corte].mcac, dd[dd.sos_z<=corte].mcac
    _,p = stats.mannwhitneyu(a,b,alternative="two-sided")
    rho,pr = stats.spearmanr(dd.sos_z, dd.mcac)
    print(f"  [VENDA] up (n={len(dd)}): baixo R$ {b.median():,.0f} | alto R$ {a.median():,.0f}"
          f" -> {100*(a.median()/b.median()-1):+.1f}%  p={p:.3f} | Spearman {rho:+.3f} (p={pr:.3f})")

print("\n"+"="*100)
print("D) MENSAL LONGO (2022-2026, spend-planilha piso) — CAC mensal × SoS, z vs MM12")
print("="*100)
sosm = sos.copy(); sosm["mes"] = sosm.semana.dt.to_period("M").dt.to_timestamp()
mm = sosm.groupby("mes")[SOS_COLS].mean()
rec = pd.read_csv(BASE/"receita_mensal.csv", parse_dates=["mes"]).set_index("mes")
sp = pd.read_csv("/Users/andre.abe/meu_projeto/personas_ssr/data/meta_spend_diario.csv", parse_dates=[0])
sp["mes"] = pd.to_datetime(sp[sp.columns[0]]).dt.to_period("M").dt.to_timestamp()
spm = sp.groupby("mes")["spend_meta"].sum().rename("spend")
dm = mm.join(rec,how="inner").join(spm,how="inner")
dm = dm[dm.spend>0].iloc[:-1]
dm["cac_mensal"] = dm.spend/dm.tx
dm["roas_mensal"] = dm.receita/dm.spend
def zmm12(x): return (x-x.rolling(12,min_periods=6).mean())/x.rolling(12,min_periods=6).std()
print(f"n = {len(dm)} meses")
for sc,sn in [("sos_todos","SoS todos"),("sos_midias","SoS mídias")]:
    x = zmm12(dm[sc])
    for ac,an in [("cac_mensal","CAC mensal (neg=bom)"),("roas_mensal","ROAS mensal")]:
        row = f"  {sn:12s} x {an:22s}"
        for lead in (0,1,2,3):
            y = zmm12(dm[ac]).shift(-lead)
            mk = x.notna()&y.notna()
            if mk.sum()<24: row+=f"  L{lead}: n<24"; continue
            r,p = stats.spearmanr(x[mk],y[mk])
            row += f"  L{lead}:{r:+.2f}{'*' if p<0.05 else ' '}"
        print(row)
