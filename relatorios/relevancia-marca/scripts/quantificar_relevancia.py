#!/usr/bin/env python3
"""Quantifica o efeito da relevância em termos de negócio.

Compara semanas/dias no quartil alto vs baixo de relevância (resíduo, líquido de
mídia e calendário) em volume e eficiência. Inclui bootstrap para intervalo.
"""
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import BASE

rng = np.random.default_rng(20260821)


def compara_quartis(res: pd.DataFrame, nivel: pd.DataFrame, xcol: str, ycols: dict, label: str):
    """Q4 vs Q1 do resíduo de x; reporta a média em NÍVEL (interpretável) de cada y."""
    d = res[[xcol]].join(nivel[list(ycols)]).dropna(subset=[xcol])
    q1, q4 = d[xcol].quantile(0.25), d[xcol].quantile(0.75)
    baixo, alto = d[d[xcol] <= q1], d[d[xcol] >= q4]
    print(f"\n{'=' * 92}\n{label} — Q4 (relevância alta, n={len(alto)}) vs Q1 (baixa, n={len(baixo)})\n{'=' * 92}")
    print(f"{'métrica':<34}{'Q1 baixa':>13}{'Q4 alta':>13}{'variação':>12}{'p':>9}   IC95 bootstrap")
    for yc, yn in ycols.items():
        a, b = alto[yc].dropna(), baixo[yc].dropna()
        if len(a) < 5 or len(b) < 5:
            continue
        ma, mb = a.mean(), b.mean()
        _, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        boots = [rng.choice(a, len(a), True).mean() / rng.choice(b, len(b), True).mean() for _ in range(2000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        print(f"{yn:<34}{mb:>13,.1f}{ma:>13,.1f}{100 * (ma / mb - 1):>11.1f}%{p:>9.3f}   "
              f"[{100 * (lo - 1):+.0f}%, {100 * (hi - 1):+.0f}%]")


def main():
    # ---------- semanal (onde o Trends existe) ----------
    rs = pd.read_csv(BASE / "residuos_semanais.csv", parse_dates=["dia"]).set_index("dia")
    sem = pd.read_csv(BASE / "painel_semanal.csv", parse_dates=["dia"]).set_index("dia")

    ycols = {"tx_total": "Transações/semana", "receita_total": "Receita/semana (R$)",
             "tx_organico": "Tx canais orgânicos", "spend_total": "Spend/semana (R$)",
             "cac_ads": "CAC de ads (R$)", "roas_dia": "ROAS", "conv_por_sessao": "Tx digitais/1k sessões"}

    compara_quartis(rs, sem, "trends_bp", ycols, "BUSCA DE MARCA (Google Trends, líquida de spend) — semanal")
    compara_quartis(rs, sem, "ga4_organic_video", ycols, "YOUTUBE ORGÂNICO (GA4 Organic Video, líquido de spend) — semanal")

    # ---------- diário ----------
    rd = pd.read_csv(BASE / "residuos_diarios.csv", parse_dates=["dia"]).set_index("dia")
    from event_study import carregar_painel
    df = carregar_painel().set_index("dia")
    ga4 = pd.read_csv(BASE / "ga4_sessions_canal.csv", parse_dates=["dia"])
    w = ga4.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
    df["ga4_referral"] = w["Referral"]
    df["roas_dia"] = df.receita_total / df.spend_total.replace(0, np.nan)

    ycols_d = {"tx_total": "Transações/dia", "receita_total": "Receita/dia (R$)",
               "tx_organico": "Tx canais orgânicos", "spend_total": "Spend/dia (R$)",
               "cac_ads": "CAC de ads (R$)", "roas_dia": "ROAS", "conv_por_sessao": "Tx digitais/1k sessões",
               "conv_por_abordagem": "Conv/abordagem Comercial"}

    compara_quartis(rd, df, "ga4_organic_video", ycols_d, "YOUTUBE ORGÂNICO — diário (385 dias)")
    compara_quartis(rd, df, "ga4_organic_social", ycols_d, "SOCIAL ORGÂNICO — diário (385 dias)")

    # ---------- índice composto: só os componentes com sinal próprio ----------
    z = rs[["trends_bp", "ga4_organic_video"]].apply(lambda s: (s - s.mean()) / s.std())
    rs["IR"] = z.mean(axis=1)
    compara_quartis(rs, sem, "IR", ycols, "ÍNDICE DE RELEVÂNCIA (Trends + YouTube orgânico) — semanal")
    rs[["IR"]].to_csv(BASE / "indice_relevancia_semanal.csv")

    print("\n" + "=" * 92)
    print("Correlação entre os componentes (resíduos semanais) — checa se medem a mesma coisa")
    print("=" * 92)
    cols = ["trends_bp", "ga4_organic_video", "ga4_organic_social", "atencao_organica"]
    print(rs[cols].corr(method="spearman").round(3).to_string())


if __name__ == "__main__":
    main()
