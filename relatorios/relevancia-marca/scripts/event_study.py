#!/usr/bin/env python3
"""Estudo de evento — lift das sabatinas (Renan 14/08, Marçal 17/08/2026).

Contrafactual por regressão OLS: log1p(y) ~ DOW + mês + log1p(spend) + fases de campanha.
Lift = resíduo médio na janela do evento; significância via placebo (todas as janelas
de mesmo tamanho fora dos eventos). Ref.: Brodersen et al. 2015; Lewis & Rao 2015.
"""
import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data"

EVENTOS = {
    "renan_14ago": pd.Timestamp("2026-08-14"),
    "marcal_17ago": pd.Timestamp("2026-08-17"),
}
JANELA = 3  # D0..D+2 (Renan D+3 = D0 do Marçal — janelas não podem se sobrepor)


def carregar_painel() -> pd.DataFrame:
    vendas = pd.read_csv(BASE / "serie_vendas.csv", parse_dates=["dia"])
    spend = pd.read_csv(BASE / "spend.csv", parse_dates=["dia"])
    zenvia = pd.read_csv(BASE / "zenvia.csv", parse_dates=["dia"])
    leads = pd.read_csv(BASE / "leads.csv", parse_dates=["dia"])
    ga4 = pd.read_csv(BASE / "ga4_sessions_canal.csv", parse_dates=["dia"])

    ga4_w = ga4.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
    ga4_w["sessions_total"] = ga4_w.sum(axis=1)
    ga4_w = ga4_w.rename(columns={
        "Direct": "ga4_direct", "Organic Search": "ga4_organic_search",
        "Organic Video": "ga4_organic_video", "Organic Social": "ga4_organic_social",
    })[["ga4_direct", "ga4_organic_search", "ga4_organic_video", "ga4_organic_social", "sessions_total"]]

    df = vendas.merge(spend, on="dia").merge(zenvia, on="dia", how="left") \
               .merge(leads, on="dia").merge(ga4_w, on="dia")

    # fases de campanha (dummies)
    per = pd.read_csv(BASE / "campanhas_periodos.csv",
                      parse_dates=["aquecimento_start", "aquecimento_end", "venda_start", "venda_end"])
    df["em_venda"] = 0
    df["em_aquecimento"] = 0
    for _, r in per.iterrows():
        if pd.notna(r.venda_start):
            fim = r.venda_end if pd.notna(r.venda_end) else df.dia.max()
            df.loc[df.dia.between(r.venda_start, fim), "em_venda"] = 1
        if pd.notna(r.aquecimento_start):
            fim = r.aquecimento_end if pd.notna(r.aquecimento_end) else df.dia.max()
            df.loc[df.dia.between(r.aquecimento_start, fim), "em_aquecimento"] = 1

    # métricas de resistência (esforço constante)
    df["conv_por_abordagem"] = df.tx_comercial / df.abordagens.replace(0, np.nan)
    df["conv_por_sessao"] = 1000 * df.tx_digital / df.sessions_total
    df["cac_ads"] = df.spend_total / df.tx_ads.replace(0, np.nan)
    df["ticket_medio"] = df.receita_total / df.tx_total
    return df.sort_values("dia").reset_index(drop=True)


def residuos(df: pd.DataFrame, col: str, mask_treino: pd.Series) -> pd.Series:
    """Resíduo de log1p(col) ~ DOW + mês + log1p(spend) + fases. Treina só fora dos eventos."""
    y = np.log1p(df[col].astype(float))
    X = pd.get_dummies(df.dia.dt.dayofweek, prefix="dow", drop_first=True).astype(float)
    X = pd.concat([X, pd.get_dummies(df.dia.dt.month, prefix="mes", drop_first=True).astype(float)], axis=1)
    X["log_spend"] = np.log1p(df.spend_total)
    X["em_venda"] = df.em_venda
    X["em_aquecimento"] = df.em_aquecimento
    X["trend"] = (df.dia - df.dia.min()).dt.days / 365.0
    X.insert(0, "const", 1.0)

    ok = mask_treino & y.notna() & np.isfinite(y)
    Xt, yt = X[ok].values, y[ok].values
    beta, *_ = np.linalg.lstsq(Xt, yt, rcond=None)
    pred = X.values @ beta
    return y - pred  # resíduo em log → ~lift percentual


def placebo_pvalue(res: pd.Series, dias: pd.Series, inicio: pd.Timestamp, janela: int,
                   excluir: list[pd.Timestamp]) -> tuple[float, float, float]:
    """Lift observado, percentil do resíduo na distribuição placebo e p bicaudal.

    O percentil é o que se lê: 95+ = alto atípico, 5- = baixo atípico (para CAC,
    baixo é bom). p bicaudal = 2 × min(cauda), como em MacKinlay (1997).
    """
    idx = dias.searchsorted(inicio)
    obs = res.iloc[idx:idx + janela].mean()
    medias = []
    for i in range(len(res) - janela + 1):
        d0 = dias.iloc[i]
        if any(abs((d0 - e).days) < janela + 3 for e in excluir):
            continue
        m = res.iloc[i:i + janela].mean()
        if np.isfinite(m):
            medias.append(m)
    medias = np.array(medias)
    pct = 100 * (medias < obs).mean()
    p_bicaudal = 2 * min((medias >= obs).mean(), (medias <= obs).mean())
    return obs, pct, min(p_bicaudal, 1.0)


def main():
    df = carregar_painel()
    dias = df.dia

    # máscara de treino: fora das janelas de evento (D-1..D+7 de cada)
    mask = pd.Series(True, index=df.index)
    for d0 in EVENTOS.values():
        mask &= ~df.dia.between(d0 - pd.Timedelta(days=1), d0 + pd.Timedelta(days=7))

    series = {
        # atenção
        "ga4_direct": "Sessões Direct (GA4)",
        "ga4_organic_search": "Sessões Organic Search (GA4)",
        "ga4_organic_video": "Sessões Organic Video/YouTube (GA4)",
        "leads_organicos": "Leads orgânicos",
        # vendas
        "receita_total": "Receita total",
        "tx_total": "Transações totais",
        "receita_digital": "Receita digital",
        "receita_comercial": "Receita Comercial",
        "receita_organico": "Receita canais orgânicos (Portal/Organic)",
        "receita_youtube": "Receita canal YouTube",
        "tx_primeira_compra": "Primeiras compras (novos clientes)",
        # resistência (esforço constante)
        "conv_por_abordagem": "Conversão por abordagem Comercial",
        "conv_por_sessao": "Tx digitais por 1k sessões",
        "cac_ads": "CAC ads (spend/tx ads) — negativo é bom",
        "ticket_medio": "Ticket médio",
    }

    linhas = []
    excluir = list(EVENTOS.values())
    for col, nome in series.items():
        res = residuos(df, col, mask)
        for ev, d0 in EVENTOS.items():
            obs, pct, pval = placebo_pvalue(res, dias, d0, JANELA, excluir)
            linhas.append({
                "serie": nome, "evento": ev,
                "lift_pct": 100 * (np.exp(obs) - 1),
                "percentil": pct, "p_bicaudal": pval,
                "sig": "***" if pval <= 0.05 else ("*" if pval <= 0.10 else ""),
            })

    out = pd.DataFrame(linhas)
    out.to_csv(BASE / "resultado_event_study.csv", index=False)
    for ev in EVENTOS:
        print(f"\n=== {ev} (D0..D+{JANELA-1}) — lift vs contrafactual, percentil na dist. placebo ===")
        sub = out[out.evento == ev][["serie", "lift_pct", "percentil", "p_bicaudal", "sig"]]
        print(sub.to_string(index=False, float_format=lambda x: f"{x:8.2f}"))

    # níveis observados nas janelas (para leitura absoluta)
    print("\n=== Níveis observados (média da janela vs média mesma DOW últimas 4 sem. pré-evento) ===")
    for ev, d0 in EVENTOS.items():
        jan = df[df.dia.between(d0, d0 + pd.Timedelta(days=JANELA - 1))]
        pre = df[df.dia.between(d0 - pd.Timedelta(days=28), d0 - pd.Timedelta(days=1))]
        pre = pre[pre.dia.dt.dayofweek.isin(jan.dia.dt.dayofweek.unique())]
        cols = ["receita_total", "receita_comercial", "receita_digital", "tx_total",
                "ga4_direct", "conv_por_abordagem", "spend_total"]
        print(f"\n{ev}:")
        for c in cols:
            print(f"  {c:22s} janela={jan[c].mean():12,.1f}  pré(4sem DOW)={pre[c].mean():12,.1f}  razão={jan[c].mean()/pre[c].mean():6.2f}")


if __name__ == "__main__":
    main()
