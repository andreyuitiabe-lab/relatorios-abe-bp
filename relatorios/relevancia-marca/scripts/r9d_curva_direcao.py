#!/usr/bin/env python3
"""Rodada 9d (17/09/2026) — a eficiência é função só de (spend, audiência)?
Pergunta do André: no spend alto, a audiência é a única variável? E a curva depende de estar
SUBINDO ou DESCENDO? O próximo passo é aumentar, manter ou reduzir?

A. Balanço: o que MAIS varia entre spend-alto+audiência-alta e spend-alto+audiência-baixa.
B. Curva de resposta: audiência desloca o NÍVEL ou muda a INCLINAÇÃO (elasticidade) do spend?
C. Histerese: no mesmo nível de spend, subindo vs descendo dá o mesmo CAC?
D. Estado → próximo passo: dado (nível, direção, audiência), o que aconteceu quando escalou.
"""
import sys, numpy as np, pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.api as sm
sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE
from teste_pareado_sem_lancamento import janelas
PD = BASE.parent.parent/"performance-diaria"/"data"; rng=np.random.default_rng(19); OUT=[]
def say(s=""): print(s); OUT.append(s)

# ---------- painel ----------
p = carregar_painel()[["dia","tx_total","receita_total","tx_ads","tx_comercial","spend_total","ticket_medio"]]
v = pd.read_csv(PD/"vendas_diarias_canal_campanha.csv", parse_dates=["dia"])
g = v.groupby(["dia","canal"]).tx.sum().unstack(fill_value=0)
tv = v.groupby("dia").agg(tx_total=("tx","sum"), receita_total=("receita","sum")).reset_index()
tv["tx_ads"]=g.get("Ads Meta",0)+g.get("Ads Google",0); tv["tx_comercial"]=g.get("Comercial",0)
tv["ticket_medio"]=tv.receita_total/tv.tx_total
sv = pd.read_csv(PD/"spend_vendas_campanha_fonte.csv", parse_dates=["dia"]).fillna(0)
sp = sv.groupby("dia").spend.sum().rename("spend_total").reset_index()
ext = tv.merge(sp,on="dia",how="left"); ext=ext[ext.dia>p.dia.max()]
df = pd.concat([p,ext]).sort_values("dia")
o = pd.read_csv(BASE/"yt_diario_origem.csv",parse_dates=["dia"]); w=o.pivot_table(index="dia",columns="origem",values="views",aggfunc="sum").fillna(0)
w["yt"]=w.sum(axis=1)-w.get("ADVERTISING",0)-w.get("SHORTS",0)
df = df.merge(w[["yt"]].reset_index(),on="dia",how="left")
# mix de campanha e concentração
camp = sv.groupby(["dia","sigla"]).spend.sum().reset_index()
dom = camp.sort_values(["dia","spend"],ascending=[True,False]).groupby("dia").head(1).rename(columns={"sigla":"sigla_dom","spend":"spend_dom"})
tot = camp.groupby("dia").agg(n_camp=("sigla","nunique"), spend_camp=("spend","sum")).reset_index()
hhi = camp.assign(sh=lambda x: x.spend/x.groupby("dia").spend.transform("sum")).assign(sh2=lambda x: x.sh**2).groupby("dia").sh2.sum().rename("hhi").reset_index()
df = df.merge(dom[["dia","sigla_dom","spend_dom"]],on="dia",how="left").merge(tot,on="dia",how="left").merge(hhi,on="dia",how="left")
df["share_dom"]=df.spend_dom/df.spend_camp
df = df[(df.dia>="2025-08-01")&(df.dia<="2026-09-12")].dropna(subset=["yt"]).sort_values("dia").reset_index(drop=True)
em,lanc,fech,_,_=janelas(df); df["em_venda"]=em; df["lanc"]=lanc; df["fech"]=fech
df["cac_ads"]=df.spend_total/df.tx_ads.replace(0,np.nan)
df["dow"]=df.dia.dt.dayofweek; df["fds"]=df.dow.isin([5,6]).astype(int)
# direção: spend e audiência vs média móvel 7d anterior
df["spend_mm7"]=df.spend_total.shift(1).rolling(7).mean(); df["yt_mm7"]=df.yt.shift(1).rolling(7).mean()
df["spend_sobe"]=(df.spend_total>df.spend_mm7); df["yt_sobe"]=(df.yt>df.yt_mm7)
df["d_spend"]=df.spend_total/df.spend_mm7-1; df["d_yt"]=df.yt/df.yt_mm7-1
df["q_spend"]=pd.qcut(df.spend_total,5,labels=False,duplicates="drop")
df["yt_alta"]=df.groupby("q_spend").yt.transform(lambda s: s>s.median())
say(f"painel: {len(df)} dias · dias com mm7 completa: {df.spend_mm7.notna().sum()}")

# ===== A. BALANÇO =====
say("\n"+"="*104)
say("A. A AUDIÊNCIA É A ÚNICA COISA QUE MUDA? — balanço da célula spend ALTO (Q4+Q5), audiência alta vs baixa")
hi = df[df.q_spend>=3]
a, b = hi[hi.yt_alta], hi[~hi.yt_alta]
say(f"   n = {len(a)} dias (aud. alta) vs {len(b)} (aud. baixa)")
say(f"   {'variável':<34}{'aud. ALTA':>14}{'aud. BAIXA':>14}{'Δ':>10}{'p':>9}")
def cmp(nome, col, pct=False, fmt=",.0f"):
    x, y = a[col].astype(float).dropna(), b[col].astype(float).dropna()
    p = stats.mannwhitneyu(x, y).pvalue
    d = 100*(x.mean()/y.mean()-1) if y.mean() else np.nan
    say(f"   {nome:<34}{x.mean():>14{fmt}}{y.mean():>14{fmt}}{d:>+9.1f}%{p:>9.3f}")
for nome, col, f in [("spend total (R$)","spend_total",",.0f"),("views orgânicas","yt",",.0f"),("CAC de ads (R$)","cac_ads",",.0f"),
                     ("transações","tx_total",",.0f"),("ticket médio (R$)","ticket_medio",",.0f"),
                     ("nº de campanhas ativas","n_camp",",.1f"),("concentração do spend (HHI)","hhi",",.3f"),
                     ("share da campanha dominante","share_dom",",.3f"),("% fim de semana","fds",",.2f"),
                     ("% em janela de lançamento","lanc",",.2f"),("% em fechamento","fech",",.2f"),
                     ("Δ spend vs MM7","d_spend",",.3f"),("Δ audiência vs MM7","d_yt",",.3f")]:
    cmp(nome, col, fmt=f)
say(f"   campanha dominante (aud. alta): {a.sigla_dom.value_counts().head(4).to_dict()}")
say(f"   campanha dominante (aud. baixa): {b.sigla_dom.value_counts().head(4).to_dict()}")

# ===== B. NÍVEL OU INCLINAÇÃO =====
say("\n"+"="*104)
say("B. A AUDIÊNCIA DESLOCA O NÍVEL DA CURVA OU MUDA A INCLINAÇÃO? — a pergunta que decide se vale escalar nesses dias")
say("   log(tx_ads) = a + b·log(spend) + c·log(YT) + d·log(spend)×log(YT) + DOW + mês×ano + fase")
say("   d > 0 → a elasticidade ao spend é MAIOR em dia de audiência alta (escalar rende mais)")
say("   d = 0 e c > 0 → a audiência sobe o patamar, mas o retorno marginal do próximo real é o mesmo")
d = df.dropna(subset=["cac_ads"]).copy()
X = pd.get_dummies(d.dow, prefix="dow", drop_first=True).astype(float)
X = pd.concat([X, pd.get_dummies(d.dia.dt.month.astype(str)+"_"+d.dia.dt.year.astype(str), prefix="ym", drop_first=True).astype(float)], axis=1)
X["venda"]=d.em_venda.astype(float); X["lanc"]=d.lanc.astype(float); X["fech"]=d.fech.astype(float)
ls = np.log(d.spend_total); ly = np.log(d.yt)
X["ls"]=ls - ls.mean(); X["ly"]=ly - ly.mean(); X["ls_ly"]=X.ls*X.ly
Xc = sm.add_constant(X)
m = sm.OLS(np.log(d.tx_ads.clip(lower=1)), Xc).fit(cov_type="HAC", cov_kwds={"maxlags":7})
say(f"   b (elasticidade ao spend, na audiência média) = {m.params['ls']:+.3f}  (IC95 [{m.params['ls']-1.96*m.bse['ls']:+.3f},{m.params['ls']+1.96*m.bse['ls']:+.3f}], p={m.pvalues['ls']:.4f})")
say(f"   c (efeito da audiência, no spend médio)       = {m.params['ly']:+.3f}  (p={m.pvalues['ly']:.4f})")
say(f"   d (INTERAÇÃO spend × audiência)               = {m.params['ls_ly']:+.3f}  (IC95 [{m.params['ls_ly']-1.96*m.bse['ls_ly']:+.3f},{m.params['ls_ly']+1.96*m.bse['ls_ly']:+.3f}], p={m.pvalues['ls_ly']:.4f})")
sd = np.log(d.yt).std()
say(f"   → elasticidade ao spend em dia de audiência BAIXA (−1 dp): {m.params['ls']-m.params['ls_ly']*sd:+.3f}")
say(f"   → elasticidade ao spend em dia de audiência ALTA  (+1 dp): {m.params['ls']+m.params['ls_ly']*sd:+.3f}")
say(f"   Veredito: {'INCLINAÇÃO muda — escalar rende mais em dia de audiência alta' if m.pvalues['ls_ly']<0.10 and m.params['ls_ly']>0 else 'NÍVEL desloca, inclinação igual — a audiência não muda o retorno do próximo real'}")

# ===== C. HISTERESE =====
say("\n"+"="*104)
say("C. HISTERESE — no MESMO nível de spend, chegar SUBINDO é diferente de chegar DESCENDO?")
dd = df.dropna(subset=["spend_mm7","cac_ads"]).copy()
say(f"   {'quintil de spend':<18}{'n sobe':>8}{'CAC subindo':>13}{'n desce':>9}{'CAC descendo':>14}{'Δ':>9}{'p':>8}")
for q, gq in dd.groupby("q_spend"):
    su, de = gq[gq.spend_sobe].cac_ads, gq[~gq.spend_sobe].cac_ads
    if len(su)<8 or len(de)<8: continue
    p = stats.mannwhitneyu(su,de).pvalue
    say(f"   Q{int(q)+1:<17}{len(su):>8}{su.mean():>13,.0f}{len(de):>9}{de.mean():>14,.0f}{100*(su.mean()/de.mean()-1):>+8.1f}%{p:>8.3f}")
say("\n   Cruzando direção do SPEND × direção da AUDIÊNCIA (todos os dias; CAC médio e transações):")
say(f"   {'estado':<34}{'n':>5}{'CAC (R$)':>11}{'tx/dia':>9}{'spend/dia':>12}{'CAC vs médio':>14}")
cac_m = dd.cac_ads.mean()
for (ss, ys), gq in dd.groupby(["spend_sobe","yt_sobe"]):
    nome = f"spend {'↑' if ss else '↓'} · audiência {'↑' if ys else '↓'}"
    say(f"   {nome:<34}{len(gq):>5}{gq.cac_ads.mean():>11,.0f}{gq.tx_total.mean():>9,.0f}{gq.spend_total.mean():>12,.0f}{100*(gq.cac_ads.mean()/cac_m-1):>+13.1f}%")

# ===== D. ESTADO → PRÓXIMO PASSO =====
say("\n"+"="*104)
say("D. ESTADO HOJE → O QUE ACONTECEU AO ESCALAR AMANHÃ (mCAC observado por estado)")
say("   Para cada dia: Δspend de amanhã vs hoje e Δtx de amanhã vs hoje → mCAC = Δspend/Δtx quando ambos sobem.")
dd = dd.sort_values("dia").reset_index(drop=True)
dd["spend_am"]=dd.spend_total.shift(-1); dd["tx_am"]=dd.tx_ads.shift(-1)
dd["d_sp"]=dd.spend_am-dd.spend_total; dd["d_tx"]=dd.tx_am-dd.tx_ads
esc = dd[(dd.d_sp>0.05*dd.spend_total)&(dd.d_tx>0)].copy()
esc["mcac"]=esc.d_sp/esc.d_tx
say(f"   n = {len(esc)} dias em que o spend subiu >5% no dia seguinte e as vendas de ads subiram")
say(f"   {'estado de HOJE':<38}{'n':>5}{'mCAC mediano':>15}{'vs geral':>11}")
med = esc.mcac.median()
for nome, mask in [("audiência ALTA (no quintil de spend)", esc.yt_alta), ("audiência BAIXA", ~esc.yt_alta),
                   ("audiência SUBINDO (> MM7)", esc.yt_sobe), ("audiência CAINDO", ~esc.yt_sobe),
                   ("aud. alta E subindo", esc.yt_alta & esc.yt_sobe), ("aud. baixa E caindo", (~esc.yt_alta) & (~esc.yt_sobe)),
                   ("spend já vinha subindo", esc.spend_sobe), ("spend vinha caindo", ~esc.spend_sobe)]:
    sub = esc[mask]
    if len(sub)<10: continue
    say(f"   {nome:<38}{len(sub):>5}{sub.mcac.median():>14,.0f} {100*(sub.mcac.median()/med-1):>+10.1f}%")
say(f"   mCAC mediano geral: R$ {med:,.0f} · referência da wiki: LAN R$145 / PPT R$188 · teto de margem R$180")
# teste formal
A = esc[esc.yt_alta & esc.yt_sobe].mcac; B = esc[~(esc.yt_alta & esc.yt_sobe)].mcac
if len(A)>=10:
    say(f"   Teste: mCAC 'alta E subindo' (n={len(A)}, mediana R$ {A.median():,.0f}) vs resto (n={len(B)}, R$ {B.median():,.0f}) → Mann-Whitney p={stats.mannwhitneyu(A,B).pvalue:.3f}")
(BASE/"r9d_curva_direcao.txt").write_text("\n".join(OUT)); print("\nsalvo em", BASE/"r9d_curva_direcao.txt")
