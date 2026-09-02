#!/usr/bin/env python3
"""Teste decisivo: o efeito do YouTube orgânico sobrevive a pareamento por spend?

A residualização usa log(spend) linear; se a relação real for curva, sobra spend no
resíduo e o "efeito de relevância" é mídia disfarçada. Aqui comparo dias de alta vs
baixa audiência orgânica DENTRO de quintis de spend (pareamento não-paramétrico).
"""
import numpy as np
import pandas as pd
from scipy import stats  # noqa: F401
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE

rng = np.random.default_rng(20260821)


def teste_pareado(df: pd.DataFrame, xcol: str, xnome: str, ycols: dict, n_bins=5):
    """Dentro de cada quintil de spend, divide por mediana de x e compara y."""
    d = df.copy()
    d["bin_spend"] = pd.qcut(d.spend_total, n_bins, labels=False, duplicates="drop")
    # estrato de calendário: fim de semana × campanha em fase de venda
    d["bin_dow"] = (d.dia.dt.dayofweek.isin([5, 6]).astype(int).astype(str)
                    + "_" + d.em_venda.astype(int).astype(str))

    print(f"\n{'=' * 96}\n{xnome} — alta vs baixa DENTRO de quintil de spend × fim-de-semana × fase de venda\n{'=' * 96}")
    print(f"{'métrica':<30}{'baixa':>13}{'alta':>13}{'variação':>11}{'p':>9}   IC95 bootstrap")

    for yc, yn in ycols.items():
        difs, pesos, amostras_a, amostras_b = [], [], [], []
        for _, g in d.groupby(["bin_spend", "bin_dow"]):
            g = g.dropna(subset=[xcol, yc])
            if len(g) < 10:
                continue
            med = g[xcol].median()
            a, b = g[g[xcol] > med][yc], g[g[xcol] <= med][yc]
            if len(a) < 4 or len(b) < 4 or b.mean() == 0:
                continue
            difs.append(a.mean() / b.mean())
            pesos.append(len(g))
            amostras_a.append(a.values)
            amostras_b.append(b.values)
        if not difs:
            continue
        pesos = np.array(pesos, dtype=float)
        razao = np.average(difs, weights=pesos)
        # bootstrap dentro dos estratos
        boots = []
        for _ in range(2000):
            rs = [rng.choice(a, len(a), True).mean() / rng.choice(b, len(b), True).mean()
                  for a, b in zip(amostras_a, amostras_b)]
            boots.append(np.average(rs, weights=pesos))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        p = 2 * min((np.array(boots) <= 1).mean(), (np.array(boots) >= 1).mean())
        star = "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))
        media_b = np.average([b.mean() for b in amostras_b], weights=pesos)
        media_a = np.average([a.mean() for a in amostras_a], weights=pesos)
        print(f"{yn:<30}{media_b:>13,.1f}{media_a:>13,.1f}{100 * (razao - 1):>10.1f}%{p:>9.3f}   "
              f"[{100 * (lo - 1):+.1f}%, {100 * (hi - 1):+.1f}%] {star}")


def main():
    df = carregar_painel()
    ga4 = pd.read_csv(BASE / "ga4_sessions_canal.csv", parse_dates=["dia"])
    w = ga4.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
    df = df.merge(w[["Referral"]].rename(columns={"Referral": "ga4_referral"}).reset_index(), on="dia")
    df["roas_dia"] = df.receita_total / df.spend_total.replace(0, np.nan)

    ycols = {"tx_total": "Transações/dia", "receita_total": "Receita/dia (R$)",
             "tx_organico": "Tx canais orgânicos", "tx_digital": "Tx digitais",
             "cac_ads": "CAC de ads (R$)", "roas_dia": "ROAS",
             "conv_por_sessao": "Tx digitais/1k sessões", "ticket_medio": "Ticket médio (R$)",
             "spend_total": "Spend/dia (R$) [checagem]"}

    for col, nome in [("ga4_organic_video", "YOUTUBE ORGÂNICO (GA4 Organic Video)"),
                      ("ga4_organic_search", "BUSCA ORGÂNICA (GA4)"),
                      ("ga4_direct", "TRÁFEGO DIRETO (GA4)"),
                      ("ga4_organic_social", "SOCIAL ORGÂNICO (GA4)"),
                      ("ga4_referral", "REFERRAL (GA4)")]:
        teste_pareado(df, col, nome, ycols)


if __name__ == "__main__":
    main()
