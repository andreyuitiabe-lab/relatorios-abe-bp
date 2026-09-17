#!/usr/bin/env python3
"""Rodada 9b — audiência REAL do YouTube (Analytics API, 16/09/2026) × vendas.

Substitui o proxy GA4 Organic Video pelas views/dia do canal (data/yt_diario.csv) e refaz:
(1) crivo da rodada 4 (independência de spend, ρ→vendas, ρ→CAC residualizados);
(2) pareado alta/baixa dentro de quintil de spend × fds × fase (rodada 2/8), com e sem lançamentos;
(3) lag: views de ontem → resultado de hoje;
(4) jun–set/2026 semanal: views, receita, spend, CAC;
(5) dias dos 3 vídeos-case: views do vídeo × resíduo de receita vs mesmo-DOW-4-semanas.
Painel: relevancia-marca (ago/2025→20/08/2026) emendado com performance-diaria (→13/09/2026).
"""
import sys, numpy as np, pandas as pd
from pathlib import Path
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE
from teste_pareado_sem_lancamento import janelas
PD = BASE.parent.parent / "performance-diaria" / "data"
rng = np.random.default_rng(20260916)
OUT = []
def say(s=""): print(s); OUT.append(s)

# ---------- painel emendado ----------
p = carregar_painel()[["dia", "tx_total", "receita_total", "tx_ads", "spend_total", "ga4_organic_video", "sessions_total", "tx_digital"]]
v = pd.read_csv(PD / "vendas_diarias_canal_campanha.csv", parse_dates=["dia"])
tv = v.groupby("dia").agg(tx_total=("tx", "sum"), receita_total=("receita", "sum")).reset_index()
tv["tx_ads"] = v[v.canal.isin(["Ads Meta", "Ads Google"])].groupby("dia").tx.sum().reindex(tv.dia).values
sp = pd.read_csv(PD / "spend_vendas_campanha_fonte.csv", parse_dates=["dia"]).fillna(0).groupby("dia").spend.sum().rename("spend_total").reset_index()
ext = tv.merge(sp, on="dia", how="left")
ext = ext[ext.dia > p.dia.max()]
ga = pd.read_csv(PD / "ga4_sessions_canal.csv", parse_dates=["dia"])
gaw = ga.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
ext["ga4_organic_video"] = gaw["Organic Video"].reindex(ext.dia).values
ext["sessions_total"] = gaw.sum(axis=1).reindex(ext.dia).values
df = pd.concat([p, ext], ignore_index=True).sort_values("dia").reset_index(drop=True)
yt = pd.read_csv(BASE / "yt_diario.csv", parse_dates=["day"]).rename(columns={"day": "dia"})
df = df.merge(yt, on="dia", how="left")
df = df[df.dia <= "2026-09-12"]  # Analytics defasa ~2 dias
em_venda, lanc, fech, _, _ = janelas(df); df["em_venda"] = em_venda; df["dia_lancamento"] = lanc
df["cac_ads"] = df.spend_total / df.tx_ads.replace(0, np.nan)
df["conv_por_sessao"] = 1000 * df.tx_total / df.sessions_total
df["min_por_view"] = df.estimatedMinutesWatched / df.views
say(f"painel: {df.dia.min():%d/%m/%Y} → {df.dia.max():%d/%m/%Y}, {len(df)} dias · views/dia mediana {df.views.median():,.0f} · p90 {df.views.quantile(.9):,.0f}")
say(f"ρ(views YouTube, GA4 Organic Video) = {stats.spearmanr(df.views, df.ga4_organic_video, nan_policy='omit')[0]:+.3f} — o proxy era {'bom' if stats.spearmanr(df.views, df.ga4_organic_video, nan_policy='omit')[0] > .5 else 'FRACO'}")

# ---------- (1) crivo ----------
def resid(y, X):
    yl = np.log1p(y.astype(float).clip(lower=0)); ok = yl.notna() & np.isfinite(yl) & X.notna().all(axis=1)
    b, *_ = np.linalg.lstsq(X[ok].values, yl[ok].values, rcond=None); r = yl - X.values @ b; r[~ok] = np.nan; return r
X = pd.get_dummies(df.dia.dt.dayofweek, prefix="d", drop_first=True).astype(float)
X = pd.concat([X, pd.get_dummies(df.dia.dt.month, prefix="m", drop_first=True).astype(float)], axis=1)
X["ls"] = np.log1p(df.spend_total); X["v"] = df.em_venda; X["t"] = (df.dia - df.dia.min()).dt.days / 365; X.insert(0, "c", 1.0)
r_tx, r_cac, r_rec = resid(df.tx_total, X), resid(df.cac_ads, X), resid(df.receita_total, X)
say("\n(1) CRIVO da rodada 4 com audiência real (resíduos de DOW+mês+spend+fase+tendência; Spearman):")
say(f"{'indicador':<34}{'ρ spend':>9}{'ρ→tx':>9}{'ρ→receita':>11}{'ρ→CAC':>9}")
for c, n in [("views", "YouTube views/dia (Analytics)"), ("estimatedMinutesWatched", "minutos assistidos/dia"), ("subscribersGained", "inscritos ganhos/dia"),
             ("min_por_view", "duração média (min/view)"), ("ga4_organic_video", "GA4 Organic Video (proxy antigo)")]:
    rc = resid(df[c], X); rs = stats.spearmanr(df[c], df.spend_total, nan_policy="omit")[0]
    a = stats.spearmanr(rc, r_tx, nan_policy="omit"); b = stats.spearmanr(rc, r_rec, nan_policy="omit"); k = stats.spearmanr(rc, r_cac, nan_policy="omit")
    st = lambda x: f"{x[0]:+.3f}{'*' if x[1] < .05 else ' '}"
    say(f"{n:<34}{rs:>+9.3f}{st(a):>9}{st(b):>11}{st(k):>9}")

# ---------- (2) pareado ----------
def pareado(d, xcol, ycol, strata=("bin_spend", "bin_dow"), nboot=2000):
    d = d.dropna(subset=[xcol, ycol]).copy()
    d["bin_spend"] = pd.qcut(d.spend_total, 5, labels=False, duplicates="drop")
    d["bin_dow"] = d.dia.dt.dayofweek.isin([5, 6]).astype(int).astype(str) + "_" + d.em_venda.astype(int).astype(str)
    difs, pesos, A, B = [], [], [], []
    for _, g in d.groupby(list(strata)):
        if len(g) < 10: continue
        med = g[xcol].median(); a, b = g[g[xcol] > med][ycol], g[g[xcol] <= med][ycol]
        if len(a) < 4 or len(b) < 4 or b.mean() == 0: continue
        difs.append(a.mean() / b.mean()); pesos.append(len(g)); A.append(a.values); B.append(b.values)
    pesos = np.array(pesos, float); r = np.average(difs, weights=pesos)
    boots = [np.average([rng.choice(a, len(a), True).mean() / rng.choice(b, len(b), True).mean() for a, b in zip(A, B)], weights=pesos) for _ in range(nboot)]
    lo, hi = np.percentile(boots, [2.5, 97.5]); pv = 2 * min((np.array(boots) <= 1).mean(), (np.array(boots) >= 1).mean())
    return r, lo, hi, pv, int(pesos.sum())
fmt = lambda r: f"{100*(r[0]-1):+6.1f}% IC[{100*(r[1]-1):+.1f},{100*(r[2]-1):+.1f}] p={r[3]:.3f} (n={r[4]})"
say("\n(2) PAREADO alta vs baixa de VIEWS REAIS dentro de quintil de spend × fds × fase:")
for lab, d in [("todos os dias", df), ("sem lançamentos (venda_start ±3d)", df[~df.dia_lancamento])]:
    say(f" [{lab}]")
    for yc in ["tx_total", "receita_total", "cac_ads", "conv_por_sessao", "spend_total"]:
        say(f"   views → {yc:<16} {fmt(pareado(d, 'views', yc))}")
say(" [mesma coisa com o proxy GA4, para comparar]")
for yc in ["tx_total", "cac_ads"]:
    say(f"   GA4 OV → {yc:<15} {fmt(pareado(df, 'ga4_organic_video', yc))}")

# ---------- (3) lag ----------
df["views_ontem"] = df.views.shift(1); df["views_anteontem"] = df.views.shift(2)
say("\n(3) LAG — views de ONTEM / ANTEONTEM → hoje (pareado pelo spend de hoje):")
for xc in ["views_ontem", "views_anteontem"]:
    for yc in ["tx_total", "cac_ads"]:
        say(f"   {xc:<16} → {yc:<10} {fmt(pareado(df, xc, yc))}")
say(f"   ρ lag-1 das views (bruto) = {df.views.autocorr(1):+.3f}")

# ---------- (4) jun–set semanal ----------
say("\n(4) JUN–SET/2026 por semana (seg–dom): views do canal, receita, spend, CAC ads")
w = df[df.dia >= "2026-06-01"].set_index("dia").resample("W-SUN").agg(views=("views", "sum"), minutos=("estimatedMinutesWatched", "sum"), inscritos=("subscribersGained", "sum"),
    receita=("receita_total", "sum"), tx=("tx_total", "sum"), spend=("spend_total", "sum"), tx_ads=("tx_ads", "sum"), dias=("views", "count"))
w["cac_ads"] = w.spend / w.tx_ads; w["roas"] = w.receita / w.spend
say(f"{'semana até':<12}{'views':>12}{'inscritos':>10}{'receita':>12}{'spend':>10}{'ROAS':>6}{'CAC ads':>9}")
for d, r in w.iterrows():
    say(f"{d:%d/%m}{'':<7}{r.views:>12,.0f}{r.inscritos:>10,.0f}{r.receita/1e6:>11.2f}M{r.spend/1e6:>9.2f}M{r.roas:>6.2f}{r.cac_ads:>9,.0f}")
wk = w[w.dias >= 6]
say(f" Spearman semanal jun–set (n={len(wk)}): views×receita {stats.spearmanr(wk.views, wk.receita)[0]:+.2f} · views×spend {stats.spearmanr(wk.views, wk.spend)[0]:+.2f} · views×CAC {stats.spearmanr(wk.views, wk.cac_ads)[0]:+.2f} · views×ROAS {stats.spearmanr(wk.views, wk.roas)[0]:+.2f}")

# ---------- (5) cases ----------
say("\n(5) VÍDEOS-CASE: views do vídeo no dia × resíduo de receita (real ÷ mediana mesmo-DOW-4-semanas − 1) e de spend")
cases = pd.read_csv(BASE / "yt_cases_diario.csv", parse_dates=["dia"])
s_rec = df.set_index("dia").receita_total; s_sp = df.set_index("dia").spend_total; s_tx = df.set_index("dia").tx_total; s_views = df.set_index("dia").views
def esp(s, d):
    vals = [s.get(d - pd.Timedelta(weeks=k), np.nan) for k in (1, 2, 3, 4)]; vals = [x for x in vals if pd.notna(x)]
    return np.median(vals) if len(vals) >= 2 else np.nan
say(f"{'case':<16}{'dia':<8}{'views vídeo':>12}{'% do canal':>11}{'receita':>10}{'vs esp.':>9}{'tx vs esp.':>11}{'spend vs esp.':>14}")
for nome, g in cases.groupby("case", sort=False):
    for r in g.head(5).itertuples():
        d = r.dia
        if d not in s_rec.index: continue
        say(f"{nome:<16}{d:%d/%m %a}{r.views:>12,}{100*r.views/s_views[d]:>10.0f}%{s_rec[d]/1e3:>9,.0f}k{100*(s_rec[d]/esp(s_rec,d)-1):>+8.0f}%{100*(s_tx[d]/esp(s_tx,d)-1):>+10.0f}%{100*(s_sp[d]/esp(s_sp,d)-1):>+13.0f}%")
    say("")
(BASE / "r9b_youtube_real.txt").write_text("\n".join(OUT))
print("salvo em", BASE / "r9b_youtube_real.txt")
