#!/usr/bin/env python3
"""Avalia candidatos a indicador de relevância diária com um critério único.

Um indicador só serve se: (1) tem série diária utilizável; (2) é INDEPENDENTE de spend
— senão mede orçamento, como o social orgânico; (3) move junto com vendas/eficiência
depois de controlar mídia e calendário.
"""
import numpy as np, pandas as pd, sys
from pathlib import Path
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE

df = carregar_painel()
ga4 = pd.read_csv(BASE/"ga4_sessions_canal.csv", parse_dates=["dia"])
w = ga4.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
df = df.merge(w[["Referral"]].rename(columns={"Referral":"ga4_referral"}).reset_index(), on="dia")

# fontes novas
for arq, cols in [("wikipedia.csv", ["wiki_views"]),
                  ("marca_google.csv", ["impressoes_marca","cliques_marca"]),
                  ("zenvia_inbound.csv", ["contatos_novos","suporte"])]:
    t = pd.read_csv(BASE/arq, parse_dates=["dia"])
    df = df.merge(t[["dia"]+cols], on="dia", how="left")

df["cac_ads"] = df.spend_total / df.tx_ads.replace(0, np.nan)

CANDIDATOS = {
    "ga4_organic_video":  "YouTube orgânico (GA4)",
    "ga4_organic_search": "Busca orgânica (GA4)",
    "ga4_direct":         "Tráfego direto (GA4)",
    "ga4_referral":       "Referral (GA4)",
    "ga4_organic_social": "Social orgânico (GA4)",
    "wiki_views":         "Wikipedia — verbete BP",
    "impressoes_marca":   "Impressões busca de marca (Google Ads KW)",
    "cliques_marca":      "Cliques busca de marca (Google Ads KW)",
    "contatos_novos":     "Contatos novos no Zenvia",
    "suporte":            "Contatos de Suporte (inbound)",
    "leads_organicos":    "Leads orgânicos",
}

def resid(y, X):
    yl = np.log1p(y.astype(float).clip(lower=0))
    ok = yl.notna() & np.isfinite(yl) & X.notna().all(axis=1)
    b, *_ = np.linalg.lstsq(X[ok].values, yl[ok].values, rcond=None)
    r = yl - X.values @ b; r[~ok] = np.nan
    return r

X = pd.get_dummies(df.dia.dt.dayofweek, prefix="d", drop_first=True).astype(float)
X = pd.concat([X, pd.get_dummies(df.dia.dt.month, prefix="m", drop_first=True).astype(float)], axis=1)
X["log_spend"] = np.log1p(df.spend_total); X["venda"] = df.em_venda
X["aq"] = df.em_aquecimento; X["t"] = (df.dia-df.dia.min()).dt.days/365
X.insert(0,"const",1.0)

r_tx  = resid(df.tx_total, X)
r_cac = resid(df.cac_ads, X)

print(f"{'indicador':<42}{'dias':>6}{'ρ c/ spend':>12}{'indep?':>9}{'ρ→vendas':>11}{'ρ→CAC':>9}{'veredito':>26}")
print("-"*116)
linhas=[]
for c, nome in CANDIDATOS.items():
    s = df[c]
    n = int(s.notna().sum())
    if n < 100:
        print(f"{nome:<42}{n:>6}{'—':>12}{'—':>9}{'—':>11}{'—':>9}{'série insuficiente':>26}"); continue
    rho_sp,_ = stats.spearmanr(s, df.spend_total, nan_policy="omit")
    rc = resid(s, X)
    m1 = rc.notna() & r_tx.notna(); rho_tx,p_tx = stats.spearmanr(rc[m1], r_tx[m1])
    m2 = rc.notna() & r_cac.notna(); rho_cac,p_cac = stats.spearmanr(rc[m2], r_cac[m2])
    indep = "SIM" if abs(rho_sp) < 0.30 else ("meio" if abs(rho_sp) < 0.55 else "NÃO")
    if indep=="NÃO": ver = "mede orçamento"
    elif p_tx<0.05 and p_cac<0.05 and rho_tx>0 and rho_cac<0: ver = "★ volume + eficiência"
    elif p_tx<0.05 and rho_tx>0: ver = "só volume"
    elif p_cac<0.05 and rho_cac<0: ver = "só eficiência"
    else: ver = "sem sinal"
    print(f"{nome:<42}{n:>6}{rho_sp:>12.3f}{indep:>9}{rho_tx:>10.3f}{'*' if p_tx<0.05 else ' '}"
          f"{rho_cac:>8.3f}{'*' if p_cac<0.05 else ' '}{ver:>26}")
    linhas.append(dict(indicador=nome, dias=n, rho_spend=rho_sp, indep=indep,
                       rho_vendas=rho_tx, p_vendas=p_tx, rho_cac=rho_cac, p_cac=p_cac, veredito=ver))
pd.DataFrame(linhas).to_csv(BASE/"avaliacao_fontes.csv", index=False)
print("\n* = p<0,05 | ρ c/ spend: |ρ|<0,30 = independente · >0,55 = mede orçamento")
print("ρ→CAC negativo é BOM (aquisição mais barata quando o indicador sobe)")
