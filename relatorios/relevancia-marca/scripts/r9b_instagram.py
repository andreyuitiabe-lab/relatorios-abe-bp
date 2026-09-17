#!/usr/bin/env python3
"""Rodada 9b — Instagram (Graph API, 16/09/2026) × vendas, no mesmo crivo e pareado do YouTube.
Série: data/ig_diario.csv (reach, accounts_engaged, total_interactions, shares, saves, views, website_clicks,
profile_views por dia). Testa independência de spend, ρ→tx/CAC residualizados, pareado por quintil de spend,
exclusão de abertura/fechamento, e compara com YouTube (views orgânicas de vídeo longo e inscritos)."""
import sys, numpy as np, pandas as pd
from pathlib import Path
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE
from teste_pareado_sem_lancamento import janelas
rng = np.random.default_rng(7); OUT=[]
def say(s=""): print(s); OUT.append(s)
p = carregar_painel()[["dia","tx_total","receita_total","tx_ads","spend_total","ga4_organic_social"]]
PD = BASE.parent.parent/"performance-diaria"/"data"
v = pd.read_csv(PD/"vendas_diarias_canal_campanha.csv", parse_dates=["dia"]); tv = v.groupby("dia").agg(tx_total=("tx","sum"), receita_total=("receita","sum")).reset_index()
tv["tx_ads"] = v[v.canal.isin(["Ads Meta","Ads Google"])].groupby("dia").tx.sum().reindex(tv.dia).values
sp = pd.read_csv(PD/"spend_vendas_campanha_fonte.csv", parse_dates=["dia"]).fillna(0).groupby("dia").spend.sum().rename("spend_total").reset_index()
ga = pd.read_csv(PD/"ga4_sessions_canal.csv", parse_dates=["dia"]); gaw = ga.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
ext = tv.merge(sp, on="dia", how="left"); ext = ext[ext.dia > p.dia.max()]; ext["ga4_organic_social"] = gaw["Organic Social"].reindex(ext.dia).values
df = pd.concat([p, ext]).sort_values("dia")
ig = pd.read_csv(BASE/"ig_diario.csv", parse_dates=["dia"]).rename(columns=lambda c: c if c=="dia" else "ig_"+c); df = df.merge(ig, on="dia", how="left")
yt = pd.read_csv(BASE/"yt_diario.csv", parse_dates=["day"]).rename(columns={"day":"dia"}); df = df.merge(yt[["dia","views","estimatedMinutesWatched","subscribersGained"]], on="dia", how="left")
o = pd.read_csv(BASE/"yt_diario_origem.csv", parse_dates=["dia"]); w = o.pivot_table(index="dia", columns="origem", values="views", aggfunc="sum").fillna(0)
w["yt_org_longo"] = w.sum(axis=1) - w.get("ADVERTISING",0) - w.get("SHORTS",0); w["yt_inscritos"] = w.get("SUBSCRIBER",0)
df = df.merge(w[["yt_org_longo","yt_inscritos"]].reset_index(), on="dia", how="left")
df = df[(df.dia >= "2025-08-02") & (df.dia <= "2026-09-12")].reset_index(drop=True)
em, lanc, fech, _, _ = janelas(df); df["em_venda"]=em; df["lanc"]=lanc; df["fech"]=fech; df["cac_ads"] = df.spend_total/df.tx_ads.replace(0,np.nan)
say(f"dias com accounts_engaged>0: {(df.ig_accounts_engaged>0).sum()} · primeiro dia: {df.loc[df.ig_accounts_engaged>0,'dia'].min()}")
say(f"painel {df.dia.min():%d/%m/%y}→{df.dia.max():%d/%m/%y}, {len(df)} dias · IG reach mediana {df.ig_reach.median():,.0f}/dia · accounts_engaged {df.ig_accounts_engaged.median():,.0f} · shares {df.ig_shares.median():,.0f} · website_clicks {df.ig_website_clicks.median():,.0f}")
def resid(y, X):
    yl = np.log1p(y.astype(float).clip(lower=0)); ok = yl.notna() & np.isfinite(yl) & X.notna().all(axis=1)
    b,*_ = np.linalg.lstsq(X[ok].values, yl[ok].values, rcond=None); r = yl - X.values@b; r[~ok]=np.nan; return r
X = pd.get_dummies(df.dia.dt.dayofweek, prefix="d", drop_first=True).astype(float)
X = pd.concat([X, pd.get_dummies(df.dia.dt.month, prefix="m", drop_first=True).astype(float)], axis=1)
X["ls"]=np.log1p(df.spend_total); X["v"]=df.em_venda; X["t"]=(df.dia-df.dia.min()).dt.days/365; X.insert(0,"c",1.0)
r_tx, r_cac = resid(df.tx_total, X), resid(df.cac_ads, X)
say("\n(1) CRIVO — Instagram vs YouTube (resíduos de DOW+mês+spend+fase+tendência):")
say(f"{'indicador':<36}{'ρ spend':>9}{'indep?':>8}{'ρ→tx':>9}{'ρ→CAC':>9}")
IND = [("ig_reach","IG alcance/dia"),("ig_accounts_engaged","IG contas engajadas/dia"),("ig_total_interactions","IG interações/dia"),("ig_shares","IG compartilhamentos/dia"),("ig_saves","IG salvamentos/dia"),("ig_views","IG views/dia"),("ig_website_clicks","IG cliques no site/dia"),("ig_profile_views","IG visitas ao perfil/dia"),("ga4_organic_social","GA4 Organic Social (antigo)"),("yt_org_longo","YT views orgânicas longo"),("yt_inscritos","YT views de inscritos"),("estimatedMinutesWatched","YT minutos assistidos"),("subscribersGained","YT inscritos ganhos")]
for c,n in IND:
    if df[c].notna().sum()<100: continue
    rs = stats.spearmanr(df[c], df.spend_total, nan_policy="omit")[0]; rc = resid(df[c], X)
    a = stats.spearmanr(rc, r_tx, nan_policy="omit"); k = stats.spearmanr(rc, r_cac, nan_policy="omit")
    st = lambda x: f"{x[0]:+.3f}{'*' if x[1]<.05 else ' '}"; ind = "SIM" if abs(rs)<.3 else ("meio" if abs(rs)<.55 else "NÃO")
    say(f"{n:<36}{rs:>+9.3f}{ind:>8}{st(a):>9}{st(k):>9}")
def pareado(d, x, y):
    d = d.dropna(subset=[x,y]).copy(); d["bs"]=pd.qcut(d.spend_total,5,labels=False,duplicates="drop"); d["bd"]=d.dia.dt.dayofweek.isin([5,6]).astype(int).astype(str)+"_"+d.em_venda.astype(int).astype(str)
    difs,pesos,A,B=[],[],[],[]
    for _,g in d.groupby(["bs","bd"]):
        if len(g)<10: continue
        m=g[x].median(); a,b=g[g[x]>m][y],g[g[x]<=m][y]
        if len(a)<4 or len(b)<4: continue
        difs.append(a.mean()/b.mean()); pesos.append(len(g)); A.append(a.values); B.append(b.values)
    pesos=np.array(pesos,float); r=np.average(difs,weights=pesos)
    boots=[np.average([rng.choice(a,len(a),True).mean()/rng.choice(b,len(b),True).mean() for a,b in zip(A,B)],weights=pesos) for _ in range(2000)]
    lo,hi=np.percentile(boots,[2.5,97.5]); pv=2*min((np.array(boots)<=1).mean(),(np.array(boots)>=1).mean()); return f"{100*(r-1):+6.1f}% IC[{100*(lo-1):+.1f},{100*(hi-1):+.1f}] p={pv:.3f} n={int(pesos.sum())}"
say("\n(2) PAREADO alta vs baixa (quintil spend × fds × fase), SEM abertura nem fechamento de campanha:")
d2 = df[~df.lanc & ~df.fech]
for c,n in [("ig_reach","IG alcance"),("ig_accounts_engaged","IG contas engajadas"),("ig_shares","IG compartilhamentos"),("ig_website_clicks","IG cliques no site"),("yt_org_longo","YT views orgânicas longo"),("yt_inscritos","YT views de inscritos")]:
    say(f" [{n}]")
    for y in ["tx_total","receita_total","cac_ads","spend_total"]: say(f"   {y:<14} {pareado(d2, c, y)}")
say("\n(3) IG × YT: os dois medem a mesma coisa?")
for a_,b_ in [("ig_reach","yt_org_longo"),("ig_accounts_engaged","yt_inscritos"),("ig_shares","yt_org_longo"),("ig_reach","ga4_organic_social")]:
    ra, rb = resid(df[a_],X), resid(df[b_],X); say(f"   ρ resíduos {a_} × {b_} = {stats.spearmanr(ra, rb, nan_policy='omit')[0]:+.3f}")
say("\n(4) Dias dos cases no Instagram (reach e cliques no site vs mediana mesmo-DOW-4-semanas):")
s_r, s_c = df.set_index("dia").ig_reach, df.set_index("dia").ig_website_clicks
esp = lambda s,d: np.median([s.get(d-pd.Timedelta(weeks=k), np.nan) for k in (1,2,3,4)])
for d in pd.to_datetime(["2026-08-14","2026-08-17","2026-09-10","2026-09-11","2026-09-12","2026-09-13"]):
    say(f"   {d:%d/%m %a}  reach {s_r[d]:>10,.0f} ({100*(s_r[d]/esp(s_r,d)-1):+.0f}% vs esp.)  cliques site {s_c[d]:>6,.0f} ({100*(s_c[d]/esp(s_c,d)-1):+.0f}%)")
(BASE/"r9b_instagram.txt").write_text("\n".join(OUT)); print("salvo em", BASE/"r9b_instagram.txt")
