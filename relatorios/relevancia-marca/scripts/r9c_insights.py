#!/usr/bin/env python3
"""Rodada 9c — busca de insights novos na relação YouTube × vendas (17/09/2026).

Oito hipóteses que as rodadas anteriores NÃO testaram. Cada bloco declara hipótese, método e
o que derrubaria o achado. Painel: relevancia-marca (ago/2025→20/08/2026) + performance-diaria
(→12/09/2026); audiência = Analytics API (views orgânicas de vídeo longo, sem anúncio/Shorts).
"""
import sys, numpy as np, pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE
from teste_pareado_sem_lancamento import janelas
PD = BASE.parent.parent / "performance-diaria" / "data"
rng = np.random.default_rng(17); OUT = []
def say(s=""): print(s); OUT.append(s)

# ---------- painel ----------
p = carregar_painel()[["dia","tx_total","receita_total","tx_ads","tx_crm","tx_comercial","tx_organico","spend_total","ticket_medio"]]
v = pd.read_csv(PD/"vendas_diarias_canal_campanha.csv", parse_dates=["dia"])
g = v.groupby(["dia","canal"]).tx.sum().unstack(fill_value=0)
tv = v.groupby("dia").agg(tx_total=("tx","sum"), receita_total=("receita","sum")).reset_index()
tv["tx_ads"] = g.get("Ads Meta",0) + g.get("Ads Google",0); tv["tx_crm"] = g.get("CRM",0)
tv["tx_comercial"] = g.get("Comercial",0); tv["tx_organico"] = g.get("Orgânico/Portal",0) + g.get("YouTube",0)
tv["ticket_medio"] = tv.receita_total / tv.tx_total
sp = pd.read_csv(PD/"spend_vendas_campanha_fonte.csv", parse_dates=["dia"]).fillna(0).groupby("dia").spend.sum().rename("spend_total").reset_index()
ext = tv.merge(sp, on="dia", how="left"); ext = ext[ext.dia > p.dia.max()]
df = pd.concat([p, ext]).sort_values("dia")
o = pd.read_csv(BASE/"yt_diario_origem.csv", parse_dates=["dia"])
w = o.pivot_table(index="dia", columns="origem", values="views", aggfunc="sum").fillna(0)
w["yt"] = w.sum(axis=1) - w.get("ADVERTISING",0) - w.get("SHORTS",0)
yt = pd.read_csv(BASE/"yt_diario.csv", parse_dates=["day"]).rename(columns={"day":"dia"})
df = df.merge(w[["yt"]].reset_index(), on="dia", how="left").merge(yt[["dia","views","estimatedMinutesWatched","subscribersGained","subscribersLost"]], on="dia", how="left")
df = df[(df.dia>="2025-08-01")&(df.dia<="2026-09-12")].dropna(subset=["yt"]).sort_values("dia").reset_index(drop=True)
em, lanc, fech, _, _ = janelas(df); df["em_venda"]=em; df["lanc"]=lanc; df["fech"]=fech
df["cac_ads"] = df.spend_total/df.tx_ads.replace(0,np.nan)
df["tx_nao_ads"] = df.tx_total - df.tx_ads
df["sub_liq"] = df.subscribersGained - df.subscribersLost
say(f"painel: {len(df)} dias ({df.dia.min():%d/%m/%y}→{df.dia.max():%d/%m/%y})")

def ctrl(d):
    X = pd.get_dummies(d.dia.dt.dayofweek, prefix="dow", drop_first=True).astype(float)
    X = pd.concat([X, pd.get_dummies(d.dia.dt.month.astype(str)+"_"+d.dia.dt.year.astype(str), prefix="ym", drop_first=True).astype(float)], axis=1)
    X["ls"]=np.log1p(d.spend_total); X["venda"]=d.em_venda.astype(float); X["lanc"]=d.lanc.astype(float); X["fech"]=d.fech.astype(float)
    return X

# ===== A. Quanto tempo dura o efeito? (distributed lag) =====
say("\n" + "="*100)
say("A. DURAÇÃO DO EFEITO — hipótese: o efeito é só do próprio dia (as rodadas anteriores só testaram lag 0 e 1).")
say("   Método: log(tx) ~ Σ log(YT) de D a D−10 + controles (DOW, mês×ano, spend, fase, lançamento, fechamento), HAC-14.")
d = df.copy()
for k in range(0, 11): d[f"l{k}"] = np.log1p(d.yt.shift(k))
d = d.dropna(subset=[f"l{k}" for k in range(11)])
X = ctrl(d); 
for k in range(11): X[f"l{k}"] = d[f"l{k}"]
X = sm.add_constant(X); y = np.log1p(d.tx_total)
m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags":14})
say(f"   {'lag':<6}{'coef':>9}{'p':>8}   acumulado")
acum = 0
for k in range(11):
    b = m.params[f"l{k}"]; acum += b
    say(f"   D−{k:<4}{b:>+9.3f}{m.pvalues[f'l{k}']:>8.3f}   {acum:+.3f}")
say(f"   Soma dos 11 lags (efeito de longo prazo de +1% de audiência sustentada): {acum:+.3f}")
say(f"   → +10% de audiência sustentada por 10 dias ≈ {100*(1.1**acum-1):+.1f}% de transações; só no dia ≈ {100*(1.1**m.params['l0']-1):+.1f}%")
sig = [k for k in range(11) if m.pvalues[f"l{k}"]<0.10]
say(f"   Lags com p<0,10: {sig if sig else 'nenhum além de D0'}")

# ===== B. Dose-resposta =====
say("\n" + "="*100)
say("B. DOSE-RESPOSTA — hipótese: o efeito é linear (alta vs baixa esconde a forma da curva).")
say("   Método: decis de audiência DENTRO do quintil de spend; média de tx e CAC por decil (resíduo de DOW/mês/spend).")
d = df.copy(); d["q_spend"] = pd.qcut(d.spend_total, 5, labels=False, duplicates="drop")
d["dec_yt"] = d.groupby("q_spend").yt.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
X = sm.add_constant(ctrl(d))
d["r_tx"] = np.log1p(d.tx_total) - sm.OLS(np.log1p(d.tx_total), X).fit().predict(X)
d["r_cac"] = np.log(d.cac_ads) - sm.OLS(np.log(d.cac_ads.fillna(d.cac_ads.median())), X).fit().predict(X)
say(f"   {'quintil de audiência (dentro do spend)':<42}{'n':>5}{'tx vs médio':>13}{'CAC vs médio':>14}{'views/dia (mediana)':>21}")
for q, gq in d.groupby("dec_yt"):
    say(f"   Q{int(q)+1} {'(mais baixa)' if q==0 else '(mais alta)' if q==4 else '':<38}{len(gq):>5}{100*(np.exp(gq.r_tx.mean())-1):>+12.1f}%{100*(np.exp(gq.r_cac.mean())-1):>+13.1f}%{gq.yt.median():>21,.0f}")

# ===== C. Quem vende nos dias de audiência alta? =====
say("\n" + "="*100)
say("C. HETEROGENEIDADE POR CANAL — hipótese: o ganho está em ads (mais tráfego → mais venda).")
say("   Método: pareado (quintil spend × fds × fase), sem abertura/fechamento, por canal de venda.")
def pareado(dd, x, y, nboot=1500):
    dd = dd.dropna(subset=[x,y]).copy()
    dd["bs"]=pd.qcut(dd.spend_total,5,labels=False,duplicates="drop")
    dd["bd"]=dd.dia.dt.dayofweek.isin([5,6]).astype(int).astype(str)+"_"+dd.em_venda.astype(int).astype(str)
    difs,pes,A,B=[],[],[],[]
    for _,gq in dd.groupby(["bs","bd"]):
        if len(gq)<10: continue
        med=gq[x].median(); a,b=gq[gq[x]>med][y],gq[gq[x]<=med][y]
        if len(a)<4 or len(b)<4 or b.mean()==0: continue
        difs.append(a.mean()/b.mean()); pes.append(len(gq)); A.append(a.values); B.append(b.values)
    if not difs: return None
    pes=np.array(pes,float); r=np.average(difs,weights=pes)
    bo=[np.average([rng.choice(a,len(a),True).mean()/rng.choice(b,len(b),True).mean() for a,b in zip(A,B)],weights=pes) for _ in range(nboot)]
    lo,hi=np.percentile(bo,[2.5,97.5]); pv=2*min((np.array(bo)<=1).mean(),(np.array(bo)>=1).mean())
    return r,lo,hi,pv
dlim = df[~df.lanc & ~df.fech]
say(f"   {'canal':<22}{'efeito':>10}{'IC95':>22}{'p':>8}{'% das tx':>10}")
for c,n in [("tx_total","TOTAL"),("tx_ads","Ads (Meta+Google)"),("tx_crm","CRM"),("tx_comercial","Comercial"),("tx_organico","Orgânico+YouTube"),("tx_nao_ads","Tudo menos ads")]:
    r = pareado(dlim, "yt", c)
    if r: say(f"   {n:<22}{100*(r[0]-1):>+9.1f}%  [{100*(r[1]-1):>+6.1f}, {100*(r[2]-1):>+6.1f}]{r[3]:>8.3f}{100*df[c].sum()/df.tx_total.sum():>9.0f}%")
r = pareado(dlim, "yt", "ticket_medio"); say(f"   {'Ticket médio':<22}{100*(r[0]-1):>+9.1f}%  [{100*(r[1]-1):>+6.1f}, {100*(r[2]-1):>+6.1f}]{r[3]:>8.3f}")

# ===== D. Onde o efeito é maior: dia de spend alto ou baixo? =====
say("\n" + "="*100)
say("D. INTERAÇÃO COM SPEND — hipótese: o efeito é igual em qualquer nível de investimento.")
say("   Método: efeito da audiência DENTRO de cada quintil de spend (alta vs baixa no próprio quintil).")
say(f"   {'quintil de spend':<20}{'spend mediano':>15}{'n':>5}{'Δ transações':>14}{'Δ CAC':>10}")
for q, gq in df.assign(qs=pd.qcut(df.spend_total,5,labels=False,duplicates="drop")).groupby("qs"):
    med = gq.yt.median(); a, b = gq[gq.yt>med], gq[gq.yt<=med]
    if len(a)<8 or len(b)<8: continue
    dtx = 100*(a.tx_total.mean()/b.tx_total.mean()-1); dcac = 100*(a.cac_ads.mean()/b.cac_ads.mean()-1)
    say(f"   Q{int(q)+1:<18}{gq.spend_total.median():>14,.0f}{len(gq):>5}{dtx:>+13.1f}%{dcac:>+9.1f}%")

# ===== E. Assimetria =====
say("\n" + "="*100)
say("E. ASSIMETRIA — hipótese: subir audiência ajuda tanto quanto cair prejudica.")
say("   Método: top decil e bottom decil de audiência (dentro do quintil de spend) vs os 80% do meio.")
d = df.copy(); d["q_spend"]=pd.qcut(d.spend_total,5,labels=False,duplicates="drop")
d["p_yt"] = d.groupby("q_spend").yt.transform(lambda s: s.rank(pct=True))
X = sm.add_constant(ctrl(d)); d["r_tx"] = np.log1p(d.tx_total) - sm.OLS(np.log1p(d.tx_total), X).fit().predict(X)
for lab, mask in [("decil MAIS BAIXO (p<10%)", d.p_yt<0.10), ("meio (10–90%)", (d.p_yt>=0.10)&(d.p_yt<=0.90)), ("decil MAIS ALTO (p>90%)", d.p_yt>0.90)]:
    say(f"   {lab:<28}n={mask.sum():>4}  tx vs esperado {100*(np.exp(d.r_tx[mask].mean())-1):>+6.1f}%")

# ===== F. Inscritos como ESTOQUE =====
say("\n" + "="*100)
say("F. INSCRITOS COMO ESTOQUE — hipótese: só o fluxo diário importa; o estoque acumulado não diz nada.")
say("   Método: semanal. Inscritos líquidos acumulados nas 4 semanas anteriores → vendas da semana, controlando spend.")
wk = df.set_index("dia").resample("W-SUN").agg(tx=("tx_total","sum"), receita=("receita_total","sum"), spend=("spend_total","sum"),
    tx_ads=("tx_ads","sum"), sub_liq=("sub_liq","sum"), yt=("yt","sum"), min_=("estimatedMinutesWatched","sum")).iloc[1:-1]
wk["cac"] = wk.spend/wk.tx_ads; wk["sub_acum4"] = wk.sub_liq.rolling(4).sum().shift(1); wk["yt_acum4"] = wk.yt.rolling(4).sum().shift(1)
wkc = wk.dropna()
Xw = pd.DataFrame({"const":1.0, "ls":np.log(wkc.spend), "t":np.arange(len(wkc))/52.0}, index=wkc.index)
for nome, col in [("inscritos líq. acum. 4 sem (defasado)","sub_acum4"), ("audiência acum. 4 sem (defasada)","yt_acum4"), ("inscritos líq. da própria semana","sub_liq")]:
    Xi = Xw.copy(); Xi["x"] = np.log1p(wkc[col].clip(lower=1))
    for alvo, ny in [("tx","transações"),("cac","CAC")]:
        mm = sm.OLS(np.log(wkc[alvo]), Xi).fit(cov_type="HAC", cov_kwds={"maxlags":4})
        say(f"   {nome:<40} → {ny:<11} elast. {mm.params['x']:+.3f} (p={mm.pvalues['x']:.3f}, n={len(wkc)})")
say(f"   Inscritos líquidos: mediana {wk.sub_liq.median():,.0f}/semana · pior semana {wk.sub_liq.min():,.0f} · melhor {wk.sub_liq.max():,.0f}")

# ===== G. Vídeos gigantes: event study =====
say("\n" + "="*100)
say("G. VÍDEOS GIGANTES — hipótese: um vídeo de milhões de views move a venda do dia.")
say("   Método: dias com vídeo novo >1M views em D0..D+2 (base classificada) vs placebo de todos os outros dias, resíduo controlado.")
bv = pd.read_csv(BASE/"yt_base_videos.csv", parse_dates=["publicado"])
big = bv[(bv.camada=="PROGRAMA") & (bv.an_views>1_000_000)][["publicado","titulo","an_views"]].sort_values("an_views", ascending=False)
say(f"   {len(big)} programas com +1M views desde ago/2025. Top 8:")
for r in big.head(8).itertuples(): say(f"     {r.publicado:%d/%m/%y}  {r.an_views:>10,.0f}  {r.titulo[:62]}")
d = df.copy(); X = sm.add_constant(ctrl(d)); d["r_tx"] = np.log1p(d.tx_total) - sm.OLS(np.log1p(d.tx_total), X).fit().predict(X)
d["r_cac"] = np.log(d.cac_ads.fillna(d.cac_ads.median())) - sm.OLS(np.log(d.cac_ads.fillna(d.cac_ads.median())), X).fit().predict(X)
dts = set(big.publicado.dt.normalize())
for k in range(0,4):
    mask = d.dia.isin({t+pd.Timedelta(days=k) for t in dts})
    if mask.sum()<5: continue
    say(f"   D+{k}: n={mask.sum():>3}  tx {100*(np.exp(d.r_tx[mask].mean())-1):>+6.1f}% (placebo p{100*(d.r_tx< d.r_tx[mask].mean()).mean():>4.0f})  CAC {100*(np.exp(d.r_cac[mask].mean())-1):>+6.1f}%")

# ===== H. Que tipo de conteúdo carrega o efeito =====
say("\n" + "="*100)
say("H. TIPO DE CONTEÚDO — hipótese: qualquer audiência vale igual (live de notícia = documentário).")
say("   Método: para cada dia, o programa mais visto publicado nos 2 dias anteriores; dias agrupados por tipo.")
bv["serie2"] = np.where(bv.titulo.str.contains("AO VIVO|REACT|Rasta News|RASTA", case=False, na=False), "live de notícia/react",
                np.where(bv.titulo.str.contains("DOCUMENT|FILME COMPLETO|EPIS[ÓO]DIO|COMPLETO", case=False, na=False), "documentário/filme",
                np.where(bv.titulo.str.contains("ENTREVISTA|SABATINA|BP NAS ELEI", case=False, na=False), "entrevista/sabatina", "outro programa")))
pr = bv[bv.camada=="PROGRAMA"].dropna(subset=["an_views"])
mapa = {}
for r in pr.itertuples():
    for k in range(0,3):
        dd = (r.publicado + pd.Timedelta(days=k)).normalize()
        if dd not in mapa or mapa[dd][0] < r.an_views: mapa[dd] = (r.an_views, r.serie2)
d["tipo_dia"] = d.dia.map(lambda x: mapa.get(x, (0,"sem programa grande"))[1])
d["views_prog"] = d.dia.map(lambda x: mapa.get(x, (0,None))[0])
say(f"   {'tipo do programa mais visto (D..D+2)':<34}{'n':>5}{'views med.':>12}{'tx vs esp.':>12}{'CAC vs esp.':>13}")
for t, gq in d[d.views_prog>100000].groupby("tipo_dia"):
    if len(gq)<10: continue
    say(f"   {t:<34}{len(gq):>5}{gq.views_prog.median():>12,.0f}{100*(np.exp(gq.r_tx.mean())-1):>+11.1f}%{100*(np.exp(gq.r_cac.mean())-1):>+12.1f}%")
base = d[d.views_prog<=100000]; say(f"   {'(dias sem programa >100k)':<34}{len(base):>5}{'—':>12}{100*(np.exp(base.r_tx.mean())-1):>+11.1f}%{100*(np.exp(base.r_cac.mean())-1):>+12.1f}%")

(BASE/"r9c_insights.txt").write_text("\n".join(OUT))
print("\nsalvo em", BASE/"r9c_insights.txt")
