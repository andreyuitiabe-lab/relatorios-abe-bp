#!/usr/bin/env python3
"""Rodada 9b — o efeito do YouTube sobrevive ao calendário completo (estreias medidas, aberturas,
fechamentos/lotes, ofertas novas) das páginas lancamentos.md, cenario-comercial.md e campanhas-calendario.md?
(1) pareado excluindo cada tipo de evento e todos juntos; (2) regressão diária com todos os dummies +
log(spend) + DOW + mês + tendência, erro HAC; (3) placebo por permutação da série de YouTube dentro dos
estratos (o que um "efeito" espúrio parece); (4) preditivo fora da amostra: YT de ontem prevê CAC de hoje
além do calendário?"""
import sys, numpy as np, pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE
PD = BASE.parent.parent/"performance-diaria"/"data"; rng = np.random.default_rng(16); OUT=[]
def say(s=""): print(s); OUT.append(s)
# ---------- calendário completo (wiki 16/09/2026) ----------
ESTREIAS = ["2025-08-14","2025-08-16","2025-09-02","2025-09-23","2025-10-16","2025-11-17","2025-12-20","2025-12-24","2026-01-23","2026-01-26","2026-02-24","2026-03-03","2026-03-10","2026-03-12","2026-04-20","2026-05-07","2026-05-19","2026-07-08","2026-07-16","2026-07-28","2026-07-30","2026-08-12","2026-08-19","2026-08-31","2026-09-03","2026-09-09","2026-09-14"]
ABERTURAS = ["2025-08-14","2025-09-01","2025-09-02","2025-09-16","2025-09-23","2025-10-04","2025-10-16","2025-11-01","2025-12-02","2025-12-15","2026-01-26","2026-02-23","2026-03-03","2026-04-09","2026-04-20","2026-05-17","2026-05-20","2026-07-08","2026-07-16","2026-07-17","2026-07-20","2026-07-28","2026-09-01"]
FECHAMENTOS = ["2025-08-31","2025-09-19","2025-09-30","2025-10-12","2025-10-31","2025-11-30","2025-12-31","2026-02-05","2026-02-28","2026-03-31","2026-05-15","2026-06-01","2026-07-12","2026-08-19","2026-09-15"]
LOTES = ["2026-04-01","2026-05-12","2026-05-27","2026-07-20","2026-07-28","2026-08-06","2026-08-07","2026-08-18","2026-08-19","2026-08-20","2026-09-15"]
OFERTAS = ["2026-01-16","2026-01-26","2026-01-30","2026-02-05","2026-02-06","2026-02-17","2026-02-18","2026-02-20","2026-02-26","2026-03-04","2026-03-10","2026-03-30","2026-04-01","2026-04-02","2026-04-05","2026-04-07","2026-04-14","2026-04-20","2026-04-21","2026-04-22","2026-04-24","2026-04-28","2026-05-07","2026-05-11","2026-05-14","2026-05-20","2026-05-22","2026-05-26","2026-06-17","2026-06-18","2026-06-19","2026-07-08","2026-07-16","2026-07-21","2026-07-25","2026-07-27","2026-08-17","2026-08-25","2026-08-29","2026-09-10"]
def flag(dias, datas, antes=0, depois=0):
    f = pd.Series(False, index=dias.index)
    for d in pd.to_datetime(datas): f |= dias.between(d - pd.Timedelta(days=antes), d + pd.Timedelta(days=depois))
    return f
# ---------- painel ----------
p = carregar_painel()[["dia","tx_total","receita_total","tx_ads","spend_total","em_venda"]]
v = pd.read_csv(PD/"vendas_diarias_canal_campanha.csv", parse_dates=["dia"]); tv = v.groupby("dia").agg(tx_total=("tx","sum"), receita_total=("receita","sum")).reset_index()
tv["tx_ads"] = v[v.canal.isin(["Ads Meta","Ads Google"])].groupby("dia").tx.sum().reindex(tv.dia).values
sp = pd.read_csv(PD/"spend_vendas_campanha_fonte.csv", parse_dates=["dia"]).fillna(0).groupby("dia").spend.sum().rename("spend_total").reset_index()
ext = tv.merge(sp, on="dia", how="left"); ext = ext[ext.dia > p.dia.max()]; ext["em_venda"] = 1
df = pd.concat([p, ext]).sort_values("dia")
o = pd.read_csv(BASE/"yt_diario_origem.csv", parse_dates=["dia"]); w = o.pivot_table(index="dia", columns="origem", values="views", aggfunc="sum").fillna(0)
w["yt_org"] = w.sum(axis=1) - w.get("ADVERTISING",0) - w.get("SHORTS",0); w["yt_sub"] = w.get("SUBSCRIBER",0)
yt = pd.read_csv(BASE/"yt_diario.csv", parse_dates=["day"]).rename(columns={"day":"dia"})
df = df.merge(w[["yt_org","yt_sub"]].reset_index(), on="dia", how="left").merge(yt[["dia","views","estimatedMinutesWatched","subscribersGained"]], on="dia", how="left")
df = df[(df.dia>="2025-08-01")&(df.dia<="2026-09-12")].dropna(subset=["views"]).reset_index(drop=True)
df["cac_ads"] = df.spend_total/df.tx_ads.replace(0,np.nan)
df["f_estreia"] = flag(df.dia, ESTREIAS, 1, 1); df["f_abertura"] = flag(df.dia, ABERTURAS, 3, 3); df["f_fech"] = flag(df.dia, FECHAMENTOS, 2, 0)
df["f_lote"] = flag(df.dia, LOTES, 1, 1); df["f_oferta"] = flag(df.dia, OFERTAS, 0, 1); df["f_qualquer"] = df[["f_estreia","f_abertura","f_fech","f_lote","f_oferta"]].any(axis=1)
say(f"painel {len(df)} dias · dias marcados: estreia ±1 {df.f_estreia.sum()} · abertura ±3 {df.f_abertura.sum()} · fechamento −2..0 {df.f_fech.sum()} · lote/virada ±1 {df.f_lote.sum()} · oferta nova {df.f_oferta.sum()} · QUALQUER {df.f_qualquer.sum()} ({100*df.f_qualquer.mean():.0f}%) · limpos {(~df.f_qualquer).sum()}")
# ---------- (1) pareado ----------
def pareado(d, x, y, nboot=2000):
    d = d.dropna(subset=[x,y]).copy(); d["bs"]=pd.qcut(d.spend_total,5,labels=False,duplicates="drop"); d["bd"]=d.dia.dt.dayofweek.isin([5,6]).astype(int).astype(str)+"_"+d.em_venda.astype(int).astype(str)
    difs,pesos,A,B=[],[],[],[]
    for _,g in d.groupby(["bs","bd"]):
        if len(g)<10: continue
        m=g[x].median(); a,b=g[g[x]>m][y],g[g[x]<=m][y]
        if len(a)<4 or len(b)<4: continue
        difs.append(a.mean()/b.mean()); pesos.append(len(g)); A.append(a.values); B.append(b.values)
    if not difs: return "n insuficiente"
    pesos=np.array(pesos,float); r=np.average(difs,weights=pesos)
    boots=[np.average([rng.choice(a,len(a),True).mean()/rng.choice(b,len(b),True).mean() for a,b in zip(A,B)],weights=pesos) for _ in range(nboot)]
    lo,hi=np.percentile(boots,[2.5,97.5]); pv=2*min((np.array(boots)<=1).mean(),(np.array(boots)>=1).mean()); return f"{100*(r-1):+6.1f}% IC[{100*(lo-1):+.1f},{100*(hi-1):+.1f}] p={pv:.3f} n={int(pesos.sum())}"
say("\n(1) PAREADO de views orgânicas de vídeo longo, excluindo cada tipo de evento do calendário:")
for lab, mask in [("todos os dias", pd.Series(True,index=df.index)), ("sem estreia ±1", ~df.f_estreia), ("sem abertura ±3", ~df.f_abertura), ("sem fechamento −2..0", ~df.f_fech), ("sem lote/virada ±1", ~df.f_lote), ("sem oferta nova", ~df.f_oferta), ("SÓ DIAS LIMPOS (nenhum evento)", ~df.f_qualquer)]:
    d = df[mask]; say(f" [{lab}] n={len(d)}")
    for y in ["tx_total","cac_ads","spend_total"]: say(f"   {y:<12} {pareado(d,'yt_org',y)}")
say(" [SÓ DIAS LIMPOS, views de inscritos]"); 
for y in ["tx_total","cac_ads","spend_total"]: say(f"   {y:<12} {pareado(df[~df.f_qualquer],'yt_sub',y)}")
# ---------- (2) regressão com todos os dummies ----------
say("\n(2) REGRESSÃO diária log(y) ~ log(yt) + log(spend) + DOW + mês + tendência + em_venda + 5 dummies de calendário (HAC, 7 lags):")
def reg(y, x, d):
    X = pd.get_dummies(d.dia.dt.dayofweek, prefix="d", drop_first=True).astype(float)
    X = pd.concat([X, pd.get_dummies(d.dia.dt.month, prefix="m", drop_first=True).astype(float)], axis=1)
    X["ls"]=np.log1p(d.spend_total); X["t"]=(d.dia-d.dia.min()).dt.days/365; X["venda"]=d.em_venda.astype(float)
    for f in ["f_estreia","f_abertura","f_fech","f_lote","f_oferta"]: X[f]=d[f].astype(float)
    X["lx"]=np.log1p(d[x]); X=sm.add_constant(X); yl=np.log1p(d[y]); ok=yl.notna()&X.notna().all(axis=1)
    m = sm.OLS(yl[ok], X[ok]).fit(cov_type="HAC", cov_kwds={"maxlags":7}); return m
for x,n in [("yt_org","views orgânicas longo"),("estimatedMinutesWatched","minutos assistidos"),("subscribersGained","inscritos ganhos")]:
    for y in ["tx_total","cac_ads"]:
        m = reg(y, x, df); b=m.params["lx"]; se=m.bse["lx"]
        say(f"   {n:<24} → {y:<9} elasticidade {b:+.3f} (IC95 [{b-1.96*se:+.3f},{b+1.96*se:+.3f}], p={m.pvalues['lx']:.4f}) · calendário: estreia {m.params['f_estreia']:+.2f} abertura {m.params['f_abertura']:+.2f} fech {m.params['f_fech']:+.2f} lote {m.params['f_lote']:+.2f} oferta {m.params['f_oferta']:+.2f}")
m = reg("tx_total","yt_org",df)
say(f"   [leitura] +10% de views orgânicas ≈ {100*(1.1**m.params['lx']-1):+.1f}% transações, com TUDO o mais constante; abertura de carrinho vale {100*(np.exp(m.params['f_abertura'])-1):+.0f}% e fechamento {100*(np.exp(m.params['f_fech'])-1):+.0f}%")
# ---------- (3) placebo por permutação ----------
say("\n(3) PLACEBO — embaralhar a série de YouTube dentro de (quintil de spend × fds × fase) 500×: distribuição do 'efeito' espúrio")
d = df.dropna(subset=["yt_org","cac_ads"]).copy(); d["bs"]=pd.qcut(d.spend_total,5,labels=False,duplicates="drop"); d["bd"]=d.dia.dt.dayofweek.isin([5,6]).astype(int).astype(str)+"_"+d.em_venda.astype(int).astype(str)
def efeito(dd, x, y):
    difs,pesos=[],[]
    for _,g in dd.groupby(["bs","bd"]):
        if len(g)<10: continue
        m=g[x].median(); a,b=g[g[x]>m][y],g[g[x]<=m][y]
        if len(a)<4 or len(b)<4: continue
        difs.append(a.mean()/b.mean()); pesos.append(len(g))
    return np.average(difs,weights=pesos)
obs = {y: efeito(d,"yt_org",y) for y in ["tx_total","cac_ads"]}
plac = {y: [] for y in obs}
for _ in range(500):
    dd = d.copy(); dd["yt_perm"] = dd.groupby(["bs","bd"]).yt_org.transform(lambda s: rng.permutation(s.values))
    for y in obs: plac[y].append(efeito(dd,"yt_perm",y))
for y in obs:
    pl = np.array(plac[y]); pv = (np.abs(pl-1) >= abs(obs[y]-1)).mean()
    say(f"   {y:<9} observado {100*(obs[y]-1):+.1f}% · placebo p2.5–p97.5 [{100*(np.percentile(pl,2.5)-1):+.1f}%, {100*(np.percentile(pl,97.5)-1):+.1f}%] · p_placebo = {pv:.3f}")
# ---------- (4) preditivo fora da amostra ----------
say("\n(4) PREDITIVO — treino ago/25→mai/26, teste jun→set/26: o CAC de hoje é melhor previsto com o YouTube de ONTEM além do calendário e do spend?")
d = df.copy(); d["yt_ontem"]=d.yt_org.shift(1); d["sub_ontem"]=d.subscribersGained.shift(1); d=d.dropna(subset=["yt_ontem","cac_ads"])
tr, te = d[d.dia<"2026-06-01"], d[d.dia>="2026-06-01"]
def Xm(dd, extra):
    X = pd.get_dummies(dd.dia.dt.dayofweek, prefix="d", drop_first=True).astype(float).reindex(columns=[f"d_{i}" for i in range(1,7)], fill_value=0)
    X["ls"]=np.log1p(dd.spend_total); X["venda"]=dd.em_venda.astype(float)
    for f in ["f_estreia","f_abertura","f_fech","f_lote","f_oferta"]: X[f]=dd[f].astype(float)
    for e in extra: X[e]=np.log1p(dd[e])
    return sm.add_constant(X, has_constant="add")
for extra,n in [([],"só calendário+spend"),(["yt_ontem"],"+ YouTube de ontem"),(["sub_ontem"],"+ inscritos ganhos ontem")]:
    m = sm.OLS(np.log(tr.cac_ads), Xm(tr,extra)).fit(); pred = m.predict(Xm(te,extra)); err = np.log(te.cac_ads)-pred
    say(f"   {n:<28} RMSE fora da amostra {np.sqrt((err**2).mean()):.3f} · MAE {np.abs(err).mean():.3f} · R² fora {1-(err**2).sum()/((np.log(te.cac_ads)-np.log(te.cac_ads).mean())**2).sum():.3f}")
(BASE/"r9b_calendario_completo.txt").write_text("\n".join(OUT)); print("salvo em", BASE/"r9b_calendario_completo.txt")
