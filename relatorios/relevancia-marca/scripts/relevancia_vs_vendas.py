#!/usr/bin/env python3
"""Relevância (audiência orgânica) × vendas: volume e eficiência.

Método: cada série é ortogonalizada contra mídia e calendário
(log spend, DOW, mês, tendência, fase de campanha). O resíduo é a parte
"não explicada por mídia" — é ele que responde se relevância tem sinal próprio.
Depois: correlação com lags 0..7 e teste de direção (relevância→venda vs venda→relevância).
"""
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE

RELEVANCIA = {
    "ga4_organic_social": "Redes sociais orgânico (GA4)",
    "ga4_organic_video": "YouTube orgânico (GA4 Organic Video)",
    "ga4_organic_search": "Busca orgânica (GA4)",
    "ga4_direct": "Tráfego direto (GA4)",
    "ga4_referral": "Referral (GA4)",
    "atencao_organica": "Atenção orgânica total (soma dos 5)",
}

VOLUME = {
    "tx_total": "Transações/dia",
    "receita_total": "Receita/dia",
    "tx_digital": "Transações digitais",
    "tx_organico": "Transações canais orgânicos",
    "tx_comercial": "Transações Comercial",
    "tx_primeira_compra": "Primeiras compras",
    "leads_organicos": "Leads orgânicos",
}

EFICIENCIA = {
    "cac_ads": "CAC de ads (spend/tx ads) — menor é melhor",
    "roas_dia": "ROAS do dia (receita total/spend)",
    "conv_por_sessao": "Transações digitais por 1k sessões",
    "conv_por_abordagem": "Conversão por abordagem Comercial",
    "ticket_medio": "Ticket médio",
}

CONTROLES_BASE = ["log_spend", "em_venda", "em_aquecimento", "trend"]


def preparar(df: pd.DataFrame, ga4_full: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(ga4_full, on="dia", how="left")
    df["atencao_organica"] = (df.ga4_organic_social + df.ga4_organic_video
                              + df.ga4_organic_search + df.ga4_direct + df.ga4_referral)
    df["roas_dia"] = df.receita_total / df.spend_total.replace(0, np.nan)
    df["log_spend"] = np.log1p(df.spend_total)
    df["trend"] = (df.dia - df.dia.min()).dt.days / 365.0
    return df


def desenhar_controles(df: pd.DataFrame, extra: list[str] | None = None) -> pd.DataFrame:
    X = pd.get_dummies(df.dia.dt.dayofweek, prefix="dow", drop_first=True).astype(float)
    X = pd.concat([X, pd.get_dummies(df.dia.dt.month, prefix="m", drop_first=True).astype(float)], axis=1)
    for c in CONTROLES_BASE + (extra or []):
        X[c] = df[c].astype(float)
    X.insert(0, "const", 1.0)
    return X


def residualizar(y: pd.Series, X: pd.DataFrame) -> pd.Series:
    """Resíduo de y ~ X, ignorando linhas inválidas mas devolvendo série completa."""
    yl = np.log1p(y.astype(float).clip(lower=0)) if (y.dropna() >= 0).all() else y.astype(float)
    ok = yl.notna() & np.isfinite(yl) & X.notna().all(axis=1)
    beta, *_ = np.linalg.lstsq(X[ok].values, yl[ok].values, rcond=None)
    res = yl - X.values @ beta
    res[~ok] = np.nan
    return res


def corr_com_lags(x: pd.Series, y: pd.Series, lags=range(0, 8)) -> pd.DataFrame:
    """x em t vs y em t+lag. Spearman (robusto a outliers)."""
    out = []
    for L in lags:
        a, b = (x.iloc[:-L] if L else x), (y.shift(-L).iloc[:-L] if L else y)
        m = a.notna() & b.notna()
        if m.sum() < 40:
            continue
        rho, p = stats.spearmanr(a[m], b[m])
        out.append({"lag": L, "n": int(m.sum()), "rho": rho, "p": p})
    return pd.DataFrame(out)


def main():
    df = carregar_painel()
    ga4 = pd.read_csv(BASE / "ga4_sessions_canal.csv", parse_dates=["dia"])
    w = ga4.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
    ga4_full = w[["Referral"]].rename(columns={"Referral": "ga4_referral"}).reset_index()
    df = preparar(df, ga4_full)

    X = desenhar_controles(df)
    res = pd.DataFrame({"dia": df.dia})
    for col in list(RELEVANCIA) + list(VOLUME) + list(EFICIENCIA):
        res[col] = residualizar(df[col], X)
    res.to_csv(BASE / "residuos_diarios.csv", index=False)

    # ---------- 1. Correlação bruta vs parcial (lag 0) ----------
    print("=" * 100)
    print("1. RELEVÂNCIA × RESULTADO — correlação BRUTA vs PARCIAL (removida mídia e calendário)")
    print("=" * 100)
    linhas = []
    for rc, rn in RELEVANCIA.items():
        for grupo, dic in (("VOLUME", VOLUME), ("EFICIÊNCIA", EFICIENCIA)):
            for yc, yn in dic.items():
                m = df[rc].notna() & df[yc].notna()
                bruta, _ = stats.spearmanr(df[rc][m], df[yc][m])
                m2 = res[rc].notna() & res[yc].notna()
                parcial, p = stats.spearmanr(res[rc][m2], res[yc][m2])
                linhas.append({"relevancia": rn, "grupo": grupo, "resultado": yn,
                               "rho_bruta": bruta, "rho_parcial": parcial, "p": p, "n": int(m2.sum())})
    tab = pd.DataFrame(linhas)
    tab.to_csv(BASE / "correlacoes_relevancia.csv", index=False)

    for rn in tab.relevancia.unique():
        sub = tab[tab.relevancia == rn]
        print(f"\n--- {rn} ---")
        print(sub[["grupo", "resultado", "rho_bruta", "rho_parcial", "p", "n"]]
              .to_string(index=False, float_format=lambda x: f"{x:7.3f}"))

    # ---------- 2. Lags: relevância antecede venda? ----------
    print("\n" + "=" * 100)
    print("2. LAGS — atenção orgânica (resíduo) em t vs resultado em t+lag")
    print("=" * 100)
    for yc, yn in [("receita_total", "Receita"), ("tx_total", "Transações"),
                   ("tx_organico", "Tx orgânicas"), ("cac_ads", "CAC ads"),
                   ("roas_dia", "ROAS"), ("conv_por_sessao", "Conv/1k sessões")]:
        c = corr_com_lags(res["atencao_organica"], res[yc])
        best = c.loc[c.rho.abs().idxmax()]
        s = "  ".join(f"L{int(r.lag)}:{r.rho:+.3f}{'*' if r.p < 0.05 else ' '}" for _, r in c.iterrows())
        print(f"{yn:18s} {s}   | melhor L{int(best.lag)} rho={best.rho:+.3f} p={best.p:.3g}")

    # ---------- 3. Direção: relevância→venda ou venda→relevância? ----------
    print("\n" + "=" * 100)
    print("3. DIREÇÃO — atenção(t)→receita(t+k) vs receita(t)→atenção(t+k)")
    print("=" * 100)
    for k in (1, 2, 3, 7):
        a = corr_com_lags(res["atencao_organica"], res["receita_total"], lags=[k]).iloc[0]
        b = corr_com_lags(res["receita_total"], res["atencao_organica"], lags=[k]).iloc[0]
        print(f"  k={k}: atenção→receita rho={a.rho:+.3f} (p={a.p:.3g})   |   "
              f"receita→atenção rho={b.rho:+.3f} (p={b.p:.3g})")

    # ---------- 4. Semanal (reduz ruído) ----------
    print("\n" + "=" * 100)
    print("4. AGREGADO SEMANAL — mesma pergunta com menos ruído (+ Google Trends)")
    print("=" * 100)
    sem = df.set_index("dia").resample("W-SUN").agg(
        atencao_organica=("atencao_organica", "sum"),
        ga4_organic_social=("ga4_organic_social", "sum"),
        ga4_organic_video=("ga4_organic_video", "sum"),
        receita_total=("receita_total", "sum"),
        tx_total=("tx_total", "sum"),
        tx_organico=("tx_organico", "sum"),
        spend_total=("spend_total", "sum"),
        tx_ads=("tx_ads", "sum"),
        sessions_total=("sessions_total", "sum"),
        tx_digital=("tx_digital", "sum"),
    ).reset_index()
    sem["cac_ads"] = sem.spend_total / sem.tx_ads.replace(0, np.nan)
    sem["roas_dia"] = sem.receita_total / sem.spend_total.replace(0, np.nan)
    sem["conv_por_sessao"] = 1000 * sem.tx_digital / sem.sessions_total
    sem["log_spend"] = np.log1p(sem.spend_total)
    sem["trend"] = np.arange(len(sem)) / 52.0
    sem["em_venda"] = 0.0
    sem["em_aquecimento"] = 0.0

    tr = pd.read_csv(BASE / "trends.csv", parse_dates=["dia"])
    # Trends rotula a semana pelo domingo de início; o resample W-SUN rotula pelo domingo final
    tr["semana"] = tr.dia + pd.Timedelta(days=7)
    sem = sem.merge(tr[["semana", "trends_bp"]].rename(columns={"semana": "dia"}), on="dia", how="left")

    Xs = pd.get_dummies(sem.dia.dt.month, prefix="m", drop_first=True).astype(float)
    for c in ["log_spend", "trend"]:
        Xs[c] = sem[c]
    Xs.insert(0, "const", 1.0)

    rs = pd.DataFrame({"dia": sem.dia})
    for c in ["atencao_organica", "ga4_organic_social", "ga4_organic_video", "trends_bp",
              "receita_total", "tx_total", "tx_organico", "cac_ads", "roas_dia", "conv_por_sessao"]:
        rs[c] = residualizar(sem[c], Xs)

    for xc, xn in [("atencao_organica", "Atenção orgânica"), ("ga4_organic_social", "Social orgânico"),
                   ("ga4_organic_video", "YouTube orgânico"), ("trends_bp", "Google Trends marca")]:
        print(f"\n--- {xn} (semanal, resíduo) ---")
        for yc, yn in [("receita_total", "Receita"), ("tx_total", "Transações"),
                       ("tx_organico", "Tx orgânicas"), ("cac_ads", "CAC ads"),
                       ("roas_dia", "ROAS"), ("conv_por_sessao", "Conv/1k sessões")]:
            c = corr_com_lags(rs[xc], rs[yc], lags=[0, 1, 2])
            if c.empty:
                continue
            s = "  ".join(f"L{int(r.lag)} rho={r.rho:+.3f}{'*' if r.p < 0.05 else ''}" for _, r in c.iterrows())
            print(f"  {yn:16s} {s}   (n={int(c.n.iloc[0])})")

    sem.to_csv(BASE / "painel_semanal.csv", index=False)
    rs.to_csv(BASE / "residuos_semanais.csv", index=False)


if __name__ == "__main__":
    main()
