#!/usr/bin/env python3
"""Rodada 9a (14/09/2026) — auditoria adversarial das rodadas 1–8.

Recomputa, a partir dos CSVs já em data/ e das saídas das queries 27–29, os pontos da
auditoria que exigiam número: decomposição volume×CAC (P2), estabilidade do IAC (P3),
erro-padrão clusterizado por pessoa (P4), MDE dos testes "nulos" (P5, P11), contaminação
por vídeo pago (P6), mix de campanha (P7), lag/persistência (P8), remarketing fora do CAC
e autocorrelação dos dias (não listados). Saída: data/r9a_auditoria.txt
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE
from teste_pareado_sem_lancamento import janelas, marca_alta

rng = np.random.default_rng(20260914)
OUT = []


def say(s=""):
    print(s); OUT.append(s)


def pareado(d, xcol, ycol, strata, minn=10, mina=4, nboot=2000):
    """Alta vs baixa de xcol dentro de cada estrato; razão de médias ponderada + bootstrap."""
    difs, pesos, A, B = [], [], [], []
    for _, g in d.groupby(strata):
        g = g.dropna(subset=[xcol, ycol])
        if len(g) < minn:
            continue
        med = g[xcol].median()
        a, b = g[g[xcol] > med][ycol], g[g[xcol] <= med][ycol]
        if len(a) < mina or len(b) < mina or b.mean() == 0:
            continue
        difs.append(a.mean() / b.mean()); pesos.append(len(g)); A.append(a.values); B.append(b.values)
    if not difs:
        return np.nan, np.nan, np.nan, np.nan, 0
    pesos = np.array(pesos, float); r = np.average(difs, weights=pesos)
    boots = [np.average([rng.choice(a, len(a), True).mean() / rng.choice(b, len(b), True).mean()
                         for a, b in zip(A, B)], weights=pesos) for _ in range(nboot)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    p = 2 * min((np.array(boots) <= 1).mean(), (np.array(boots) >= 1).mean())
    return r, lo, hi, p, int(pesos.sum())


def fmt(r, lo, hi, p, n=None):
    s = f"{100 * (r - 1):+6.1f}% IC[{100 * (lo - 1):+.1f},{100 * (hi - 1):+.1f}] p={p:.3f}"
    return s + (f" (dias={n})" if n else "")


# ---------- painel ----------
df = carregar_painel()
em_venda, lanc, fech, _, _ = janelas(df)
df["em_venda"] = em_venda; df["dia_lancamento"] = lanc
df["cac_ads_calc"] = df.spend_total / df.tx_ads
df["tx_nao_ads"] = df.tx_total - df.tx_ads
df["alta"] = marca_alta(df, "ga4_organic_video")
df["fds"] = df.dia.dt.dayofweek.isin([5, 6]).astype(int)
df["bin_spend"] = pd.qcut(df.spend_total, 5, labels=False, duplicates="drop")
df["bin_dow"] = df.fds.astype(str) + "_" + df.em_venda.astype(int).astype(str)
ORIG = ["bin_spend", "bin_dow"]
X = "ga4_organic_video"

# ---------- P2 ----------
say("=" * 100); say("P2 — volume e eficiência: um fato ou dois? (YT orgânico alta vs baixa, pareado por spend)")
for lab, d in [("todos os dias", df), ("sem lançamento", df[~df.dia_lancamento])]:
    say(f" [{lab}] n={len(d)}")
    res = {}
    for yc in ["tx_total", "tx_ads", "tx_nao_ads", "spend_total", "cac_ads_calc"]:
        res[yc] = pareado(d, X, yc, ORIG); say(f"   {yc:<14} {fmt(*res[yc])}")
    say(f"   CAC implícito (1+Δspend)/(1+Δtx_ads) = {100 * (res['spend_total'][0] / res['tx_ads'][0] - 1):+.1f}%")

# ---------- P3 ----------
say(); say("=" * 100); say("P3 — estabilidade do topo do IAC (n mín. 500 pessoa-dias; compradores por playlist)")
iac = pd.read_csv(BASE / "iac_ranking.csv")
iac["iac"] = iac.rpp14 / iac.rpp14.median(); iac["compradores"] = iac.com_compra_d1_d14
iac["tx"] = iac.tx_compra_pct / 100
iac["rank_tx"] = iac.tx.rank(ascending=False).astype(int)
iac["cv_min"] = 1 / np.sqrt(iac.compradores.clip(lower=1))
top = iac.head(12).copy(); top["rank_rpp"] = range(1, 13)
say(top[["rank_rpp", "nm_playlist", "pessoa_dias", "compradores", "iac", "cv_min", "tx_compra_pct", "rank_tx"]].round(3).to_string(index=False))
say(f" playlists: {len(iac)} · <30 compradores: {(iac.compradores < 30).sum()} ({100 * (iac.compradores < 30).mean():.0f}%) · <10: {(iac.compradores < 10).sum()}")
for pl in ["BP nas Eleições", "BP Entrevista"]:
    r = iac[iac.nm_playlist == pl].iloc[0]
    say(f" {pl}: taxa {r.tx_compra_pct:.2f}% rank por taxa {r.rank_tx}/{len(iac)} (por RPP: {int(iac.index[iac.nm_playlist == pl][0]) + 1})")

# ---------- P4 ----------
say(); say("=" * 100); say("P4 — erro-padrão clusterizado por pessoa (queries 27/28)")
q = pd.read_csv(BASE / "r9_cluster_q14.csv")
say(" Q14 (teste principal D+1..14), sabatina vs top-8 — log-RR, delta method:")
for st in ["membro", "freemium"]:
    for fx in ["1_leve", "2_medio", "3_heavy"]:
        t = q[(q.status == st) & (q.faixa_engaj == fx) & (q.grupo == "sabatina")].iloc[0]
        c = q[(q.status == st) & (q.faixa_engaj == fx) & (q.grupo == "top_playlist")].iloc[0]
        pt, pc = t.tx_compra_pct / 100, c.tx_compra_pct / 100; rr = pt / pc
        se_n = np.sqrt(t.var_naive / pt**2 + c.var_naive / pc**2); se_r = np.sqrt(t.var_robusta / pt**2 + c.var_robusta / pc**2)
        say(f"  {st:<8} {fx:<8} lift {rr:.2f}×  naive IC[{rr*np.exp(-1.96*se_n):.2f},{rr*np.exp(1.96*se_n):.2f}] p={2*stats.norm.sf(abs(np.log(rr)/se_n)):.4f}"
            f"  | robusto IC[{rr*np.exp(-1.96*se_r):.2f},{rr*np.exp(1.96*se_r):.2f}] p={2*stats.norm.sf(abs(np.log(rr)/se_r)):.4f}"
            f"  DEFF {t.deff:.2f}/{c.deff:.2f}  pd/pessoa {t.pd_por_pessoa:.2f}")
b = pd.read_csv(BASE / "r9_cluster_q25.csv")
say(" Q25 / Teste B (universo 08/06–03/07) — IC naive alargado pelo DEFF de cada grupo:")
for est, (st, fx) in {"membro_leve": ("membro", "1_leve"), "membro_medio": ("membro", "2_medio"), "membro_heavy": ("membro", "3_heavy")}.items():
    for jan, ccol, dcol in [("D+14", "c14", "deff14"), ("D+30", "c30", "deff30"), ("D+60", "c60", "deff60")]:
        t = b[(b.status == st) & (b.faixa_engaj == fx) & (b.grupo == "sabatina")].iloc[0]
        c = b[(b.status == st) & (b.faixa_engaj == fx) & (b.grupo == "top_playlist")].iloc[0]
        pt, pc = t[ccol] / t.pessoa_dias, c[ccol] / c.pessoa_dias; rr = pt / pc
        se_n = np.sqrt((1 - pt) / t[ccol] + (1 - pc) / c[ccol]); se_r = np.sqrt(t[dcol] * (1 - pt) / t[ccol] + c[dcol] * (1 - pc) / c[ccol])
        say(f"  {est:<13} {jan}: lift {rr:.2f}× naive p={2*stats.norm.sf(abs(np.log(rr)/se_n)):.4f} | robusto IC[{rr*np.exp(-1.96*se_r):.2f},{rr*np.exp(1.96*se_r):.2f}] p={2*stats.norm.sf(abs(np.log(rr)/se_r)):.4f}  DEFF {t[dcol]:.2f}/{c[dcol]:.2f}")

# ---------- P5 / P11 ----------
say(); say("=" * 100); say("P5 / P11 — efeito mínimo detectável (80% poder, α 5% bicaudal)")
Z = stats.norm.ppf(0.975) + stats.norm.ppf(0.8)


def mde(n_t, p0, n_c):
    d = Z * np.sqrt(p0 * (1 - p0) * (1 / n_t + 1 / n_c)); return (p0 + d) / p0


def katz(x1, n1, x0, n0):
    rr = (x1 / n1) / (x0 / n0); se = np.sqrt(1 / x1 - 1 / n1 + 1 / x0 - 1 / n0); return rr, rr * np.exp(-1.96 * se), rr * np.exp(1.96 * se)


q14 = pd.read_csv(BASE / "adesao_condicionado.csv")
for st, fx in [("freemium", "1_leve"), ("freemium", "2_medio"), ("freemium", "3_heavy"), ("membro", "1_leve"), ("membro", "2_medio")]:
    t = q14[(q14.status == st) & (q14.faixa_engaj == fx) & (q14.grupo == "sabatina")].iloc[0]
    c = q14[(q14.status == st) & (q14.faixa_engaj == fx) & (q14.grupo == "top_playlist")].iloc[0]
    rr, lo, hi = katz(t.com_compra, t.pessoa_dias, c.com_compra, c.pessoa_dias)
    say(f"  Q14 {st:<8} {fx:<8} n_t={t.pessoa_dias:>5} p0={c.tx_compra_pct:.2f}% lift {rr:.2f}× IC[{lo:.2f},{hi:.2f}]  MDE lift ≥ {mde(t.pessoa_dias, c.tx_compra_pct/100, c.pessoa_dias):.2f}×")
tb = pd.read_csv(BASE / "teste_b_resultado.csv"); tb = tb[tb.desenho.str.startswith("principal") & (tb.estrato == "freemium_todas")]
for _, r in tb.iterrows():
    say(f"  TesteB freemium {r.janela}: n_t={r.n_tratado} p0={r.tx_comparador_pct:.2f}% lift {r.lift:.2f}× IC[{r.lift_ic95_lo:.2f},{r.lift_ic95_hi:.2f}]  MDE lift ≥ {mde(r.n_tratado, r.tx_comparador_pct/100, r.n_comparador):.2f}×")
ta = pd.read_csv(BASE / "teste_a_resultado_por_sabatina.csv")
for _, r in ta[(ta.outcome == "d7") & ta.grupo.isin(["Pablo Marçal", "Renan Santos"])].iterrows():
    say(f"  TesteA D+7 {r.grupo:<14} n_t={r.n_t:>5} p0={r.taxa_c:.2f}% lift {r.lift:.2f}× IC[{r.lift_lo:.2f},{r.lift_hi:.2f}]  MDE lift ≥ {mde(r.n_t, r.taxa_c/100, r.n_c):.2f}×")
say(f"  TesteA pooled ALTA (Marçal+Renan) n_t=2.261 p0=0,57%: MDE lift ≥ {mde(2261, 0.0057, 20000):.2f}×")
say(" Case 11 de Setembro (1.757 usuários na plataforma; ~55% membro leve/médio sem compra 60d ≈ 966 pd):")
for p0, jan in [(0.0075, "D+7"), (0.0144, "D+14"), (0.0347, "D+60")]:
    say(f"   {jan}: p0={100*p0:.2f}% → MDE lift ≥ {mde(966, p0, 25000):.2f}×   (só leve, n≈527: ≥ {mde(527, p0, 25000):.2f}×)")
say(" Event study agregado (n=1 evento, janela 3 dias) — p95 do placebo:")
res = pd.read_csv(BASE / "residuos_diarios.csv", parse_dates=["dia"])
for c in ["receita_total", "tx_total", "cac_ads", "conv_por_sessao"]:
    r = res[c].values; m = np.array([r[i:i + 3].mean() for i in range(len(r) - 2)]); m = m[np.isfinite(m)]
    say(f"   {c:<16} p05 {100*(np.exp(np.percentile(m,5))-1):+.1f}%  p95 {100*(np.exp(np.percentile(m,95))-1):+.1f}%  MDE(80%) ≈ {100*(np.exp(2.8*m.std())-1):.0f}%")

# ---------- P6 ----------
say(); say("=" * 100); say("P6 — contaminação de vídeo pago no Organic Video (query 29 + GA4 Paid Video)")
ga4 = pd.read_csv(BASE / "ga4_sessions_canal.csv", parse_dates=["dia"])
w = ga4.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0).reset_index()
df = df.merge(w[["dia", "Paid Video"]].rename(columns={"Paid Video": "ga4_paid_video"}), on="dia")
g = pd.read_csv(BASE / "r9_spend_google_tipo.csv", parse_dates=["dia"]); df = df.merge(g, on="dia", how="left")
say(f" spend Google [YT]/vídeo: mediana R$ {df.spend_g_video.median():,.0f}/dia · {100*df.spend_g_video.sum()/df.spend_g_total.sum():.0f}% do Google · {100*df.spend_g_video.sum()/df.spend_total.sum():.1f}% do total")
for c, n in [("spend_total", "spend total"), ("spend_g_video", "spend Google [YT] vídeo"), ("views_g_video", "views pagas [YT]"),
             ("ga4_paid_video", "GA4 Paid Video sessões"), ("spend_g_marca", "spend busca de marca [KW]")]:
    r, p = stats.spearmanr(df[X], df[c], nan_policy="omit"); say(f"  ρ(Organic Video, {n:<26}) = {r:+.3f} (p={p:.3f})")
for c in ["spend_g_video", "views_g_video", "ga4_paid_video", "spend_meta"]:
    a, bb = df.loc[df.alta, c].mean(), df.loc[~df.alta, c].mean(); say(f"  média alta vs baixa {c:<16} {a:>10,.0f} vs {bb:>10,.0f}  Δ {100*(a/bb-1):+.1f}%")
df["bin_v"] = pd.qcut(df.spend_g_video.rank(method="first"), 3, labels=False)
say(" Pareado adicionando tercil de spend de vídeo ao estrato:")
for lab, d in [("todos", df), ("sem lançamento", df[~df.dia_lancamento])]:
    say(f"  [{lab}]")
    for yc in ["tx_total", "cac_ads_calc", "conv_por_sessao", "spend_total", "spend_g_video"]:
        say(f"    {yc:<16} {fmt(*pareado(d, X, yc, ['bin_spend', 'bin_v', 'bin_dow'], 8, 3))}")

# ---------- P7 ----------
say(); say("=" * 100); say("P7 — mix de campanha (sigla Meta dominante do dia) entre dias alta e baixa")
sv = pd.read_csv(BASE / "spend_vendas_campanha.csv", parse_dates=["dia"])
dom = sv.groupby(["dia", "sigla"]).spend.sum().reset_index().sort_values(["dia", "spend"], ascending=[True, False]).groupby("dia").head(1)
df = df.merge(dom.rename(columns={"sigla": "sigla_dom", "spend": "spend_dom"}), on="dia", how="left")
ct = pd.crosstab(df.sigla_dom, df.alta); ct["total"] = ct.sum(axis=1); ct["%alta"] = (100 * ct[True] / ct.total).round(0)
say(ct.sort_values("total", ascending=False).head(12).to_string())
d = df.dropna(subset=["sigla_dom"]).copy()
d["tercil"] = d.groupby("sigla_dom").spend_total.transform(lambda s: pd.qcut(s, 3, labels=False, duplicates="drop"))
for nome, strata in [("original: quintil spend × fds × em_venda", ORIG),
                     ("campanha dominante × fds × lançamento", ["sigla_dom", "fds", "dia_lancamento"]),
                     ("campanha dominante × fds × lançamento × tercil spend", ["sigla_dom", "fds", "dia_lancamento", "tercil"])]:
    say(f" [{nome}]")
    for yc in ["tx_total", "cac_ads_calc", "conv_por_sessao", "spend_total"]:
        say(f"   {yc:<16} {fmt(*pareado(d, X, yc, strata))}")

# ---------- P8 ----------
say(); say("=" * 100); say("P8 — indicador coincidente: persistência e lag em nível")


def resid(y):
    Xm = pd.get_dummies(df.dia.dt.dayofweek, prefix="d", drop_first=True).astype(float)
    Xm = pd.concat([Xm, pd.get_dummies(df.dia.dt.month, prefix="m", drop_first=True).astype(float)], axis=1)
    Xm["ls"] = np.log1p(df.spend_total); Xm["v"] = df.em_venda; Xm["t"] = (df.dia - df.dia.min()).dt.days / 365; Xm.insert(0, "c", 1.0)
    yl = np.log1p(y.astype(float)); ok = yl.notna() & np.isfinite(yl)
    bb, *_ = np.linalg.lstsq(Xm[ok].values, yl[ok].values, rcond=None); return yl - Xm.values @ bb


for c in [X, "tx_total", "cac_ads", "conv_por_sessao"]:
    r = resid(df[c]); say(f"  ρ(lag1) resíduo {c:<18}: {r.autocorr(1):+.3f}   lag7: {r.autocorr(7):+.3f}")
say(f"  P(alta hoje | alta ontem) = {df.alta[df.alta.shift(1) == True].mean():.3f}  vs P(alta) = {df.alta.mean():.3f}")
df["yt_ontem"] = df[X].shift(1); df["lanc_ontem"] = df.dia_lancamento.shift(1).fillna(False).astype(bool)
for lab, d in [("todos", df.dropna(subset=["yt_ontem"])), ("sem lançamento (dia e véspera)", df[~df.dia_lancamento & ~df.lanc_ontem].dropna(subset=["yt_ontem"]))]:
    say(f" [{lab}] n={len(d)}")
    for yc in ["tx_total", "cac_ads_calc", "conv_por_sessao", "spend_total"]:
        say(f"   YT ontem → {yc:<14} {fmt(*pareado(d, 'yt_ontem', yc, ORIG))}")
df["mm28"] = df[X].shift(2).rolling(28).mean(); df["sinal_ontem"] = (df.yt_ontem > 1.3 * df.mm28).astype(float)
d = df.dropna(subset=["mm28"])
for lab, dd in [("todos", d), ("sem lançamento", d[~d.dia_lancamento & ~d.lanc_ontem])]:
    difs, pesos = [], []
    for _, gg in dd.groupby(ORIG):
        a, bb = gg[gg.sinal_ontem == 1], gg[gg.sinal_ontem == 0]
        if len(a) < 3 or len(bb) < 3:
            continue
        difs.append((a.cac_ads_calc.mean() / bb.cac_ads_calc.mean(), a.tx_total.mean() / bb.tx_total.mean(), a.spend_total.mean() / bb.spend_total.mean())); pesos.append(len(gg))
    difs = np.array(difs); wts = np.array(pesos, float)
    say(f"  regra 'YT ontem > 1,3× MM28' [{lab}]: sinal em {int(dd.sinal_ontem.sum())}/{len(dd)} dias · CAC hoje {100*(np.average(difs[:,0],weights=wts)-1):+.1f}% · tx {100*(np.average(difs[:,1],weights=wts)-1):+.1f}% · spend {100*(np.average(difs[:,2],weights=wts)-1):+.1f}%")

# ---------- não listados ----------
say(); say("=" * 100); say("Não listados — remarketing fora do CAC; autocorrelação dos dias no bootstrap")
x = pd.read_csv(BASE / "r9_tx_ads_extra.csv", parse_dates=["dia"]); df = df.merge(x[["dia", "tx_ads_extra"]], on="dia")
df["cac_full"] = df.spend_total / (df.tx_ads + df.tx_ads_extra)
a, bb = df[df.alta], df[~df.alta]
say(f"  Adwords Remarketing + Instagram Ads = {100*df.tx_ads_extra.sum()/(df.tx_ads.sum()+df.tx_ads_extra.sum()):.1f}% das tx de ads; share alta {100*a.tx_ads_extra.sum()/(a.tx_ads.sum()+a.tx_ads_extra.sum()):.1f}% vs baixa {100*bb.tx_ads_extra.sum()/(bb.tx_ads.sum()+bb.tx_ads_extra.sum()):.1f}%")
for c in ["cac_ads_calc", "cac_full"]:
    say(f"  {c:<12} {fmt(*pareado(df, X, c, ORIG))}")
rho = resid(df.tx_total).autocorr(1)
say(f"  n efetivo do painel com ρ1={rho:.2f}: ≈ {385*(1-rho)/(1+rho):.0f} de 385 dias (bootstrap i.i.d. de dias é anti-conservador)")

(BASE / "r9a_auditoria.txt").write_text("\n".join(OUT))
print(f"\nsalvo em {BASE / 'r9a_auditoria.txt'}")
