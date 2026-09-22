#!/usr/bin/env python3
"""Robustez do teste pareado (rodada 8, pedido da Bárbara 11/09/2026):

1. Quanto dos dias de YouTube orgânico ALTO são dias de lançamento de doc
   (estreia no YouTube ~ abertura de venda) ou de fechamento de lote?
2. O +24,7% de transações sobrevive tirando esses dias?

O campanhas_periodos.csv (tb_campaign_period) não tem DOM/ELS/CDL/EVG/ODI/ENE —
aqui as fases usam o calendário corrigido da wiki (campanhas-calendario.md),
tanto para a dummy em_venda quanto para as janelas de exclusão.
"""
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE

rng = np.random.default_rng(20260911)

# Calendário corrigido (wiki campanhas-calendario.md, datas reais).
# venda_start = abertura de venda ≈ estreia do doc no YouTube.
CAMPANHAS = [
    ("PAP",   "2025-08-14", "2025-08-31"),
    ("BPS",   "2025-09-01", "2025-09-30"),
    ("VIS",   "2025-09-01", "2025-09-30"),
    ("HDF",   "2025-09-02", "2025-09-19"),
    ("TLR",   "2025-09-16", "2025-09-30"),
    ("PIN",   "2025-09-23", "2025-10-12"),
    ("GEO",   "2025-10-04", "2025-10-31"),
    ("GOD",   "2025-10-16", "2025-10-31"),
    ("BNO25", "2025-11-01", "2025-11-30"),
    ("HID",   "2025-12-02", "2025-12-31"),
    ("NTL25", "2025-12-15", "2025-12-31"),
    ("VDS",   "2026-01-26", "2026-02-05"),
    ("BMA",   "2026-02-23", "2026-02-28"),
    ("DBI",   "2026-03-03", "2026-03-31"),
    ("DOM",   "2026-04-09", "2026-05-15"),
    ("CDL",   "2026-05-17", "2026-06-01"),
    ("ELS",   "2026-05-20", "2026-07-12"),
    ("EVG",   "2026-07-08", None),
    ("BP10",  "2026-07-16", "2026-09-15"),   # fim de venda (marketing) — wiki campanhas-calendario 18/09; comercial segue até 30/09
    ("ODI",   "2026-07-17", None),
    ("ENE",   "2026-07-28", None),
]


def janelas(df: pd.DataFrame):
    dias = df.dia
    em_venda = pd.Series(0, index=df.index)
    lancamento = pd.Series(False, index=df.index)   # venda_start −3..+3
    fechamento = pd.Series(False, index=df.index)   # venda_end −2..venda_end
    tags_lanc, tags_fech = {}, {}
    for sigla, ini, fim in CAMPANHAS:
        ini = pd.Timestamp(ini)
        fim_v = pd.Timestamp(fim) if fim else dias.max()
        em_venda |= dias.between(ini, fim_v).astype(int)
        m = dias.between(ini - pd.Timedelta(days=3), ini + pd.Timedelta(days=3))
        lancamento |= m
        for d in dias[m]:
            tags_lanc.setdefault(d, []).append(sigla)
        if fim:
            f = pd.Timestamp(fim)
            m = dias.between(f - pd.Timedelta(days=2), f)
            fechamento |= m
            for d in dias[m]:
                tags_fech.setdefault(d, []).append(sigla)
    return em_venda, lancamento, fechamento, tags_lanc, tags_fech


def teste_pareado(d: pd.DataFrame, xcol: str, ycols: dict, titulo: str, n_bins=5):
    d = d.copy()
    d["bin_spend"] = pd.qcut(d.spend_total, n_bins, labels=False, duplicates="drop")
    d["bin_dow"] = (d.dia.dt.dayofweek.isin([5, 6]).astype(int).astype(str)
                    + "_" + d.em_venda.astype(int).astype(str))
    print(f"\n{'=' * 92}\n{titulo}  (n={len(d)} dias)\n{'=' * 92}")
    print(f"{'métrica':<28}{'baixa':>12}{'alta':>12}{'variação':>11}{'p':>8}   IC95")
    linhas = {}
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
        boots = []
        for _ in range(2000):
            rs = [rng.choice(a, len(a), True).mean() / rng.choice(b, len(b), True).mean()
                  for a, b in zip(amostras_a, amostras_b)]
            boots.append(np.average(rs, weights=pesos))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        p = 2 * min((np.array(boots) <= 1).mean(), (np.array(boots) >= 1).mean())
        star = "***" if p < 0.01 else ("**" if p < 0.05 else ("*" if p < 0.10 else ""))
        mb = np.average([b.mean() for b in amostras_b], weights=pesos)
        ma = np.average([a.mean() for a in amostras_a], weights=pesos)
        print(f"{yn:<28}{mb:>12,.1f}{ma:>12,.1f}{100 * (razao - 1):>10.1f}%{p:>8.3f}   "
              f"[{100 * (lo - 1):+.1f}%, {100 * (hi - 1):+.1f}%] {star}")
        linhas[yc] = dict(baixa=mb, alta=ma, var=100 * (razao - 1), p=p,
                          ic=[100 * (lo - 1), 100 * (hi - 1)])
    return linhas


def marca_alta(d: pd.DataFrame, xcol: str, n_bins=5) -> pd.Series:
    """Marca cada dia como alta/baixa na mesma estratificação do teste."""
    d = d.copy()
    d["bin_spend"] = pd.qcut(d.spend_total, n_bins, labels=False, duplicates="drop")
    d["bin_dow"] = (d.dia.dt.dayofweek.isin([5, 6]).astype(int).astype(str)
                    + "_" + d.em_venda.astype(int).astype(str))
    alta = pd.Series(False, index=d.index)
    for _, g in d.groupby(["bin_spend", "bin_dow"]):
        med = g[xcol].median()
        alta.loc[g.index] = g[xcol] > med
    return alta


def main():
    df = carregar_painel()
    em_venda, lanc, fech, tags_lanc, tags_fech = janelas(df)
    df["em_venda"] = em_venda  # substitui a dummy incompleta do CSV
    df["dia_lancamento"] = lanc
    df["dia_fechamento"] = fech

    xcol = "ga4_organic_video"
    ycols = {"tx_total": "Transações/dia", "receita_total": "Receita/dia (R$)",
             "cac_ads": "CAC de ads (R$)", "conv_por_sessao": "Tx dig./1k sessões",
             "spend_total": "Spend/dia [checagem]"}

    # ---- diagnóstico de sobreposição ----
    df["alta"] = marca_alta(df, xcol)
    print("DIAGNÓSTICO — sobreposição dos dias ALTA de YT orgânico com eventos de campanha")
    for nome, col in [("lançamento (venda_start ±3d)", "dia_lancamento"),
                      ("fechamento de lote (venda_end −2..0)", "dia_fechamento")]:
        pa = df.loc[df.alta, col].mean()
        pb = df.loc[~df.alta, col].mean()
        print(f"  {nome:<40} alta: {100*pa:.1f}%   baixa: {100*pb:.1f}%   ({df[col].sum()} dias no total)")

    top = df.nlargest(15, xcol)[["dia", xcol, "dia_lancamento", "dia_fechamento"]]
    top["campanha"] = top.dia.map(lambda d: ",".join(tags_lanc.get(d, tags_fech.get(d, []))))
    print("\nTop-15 dias de YT orgânico:")
    print(top.to_string(index=False))

    # ---- variantes ----
    res = {}
    res["baseline"] = teste_pareado(df, xcol, ycols,
        "BASELINE — fases corrigidas, todos os dias")
    res["sem_lancamento"] = teste_pareado(df[~df.dia_lancamento], xcol, ycols,
        "SEM DIAS DE LANÇAMENTO (venda_start ±3d de cada campanha)")
    res["sem_fechamento"] = teste_pareado(df[~df.dia_fechamento], xcol, ycols,
        "SEM FECHAMENTO DE LOTE (venda_end −2..0)")
    res["sem_ambos"] = teste_pareado(df[~(df.dia_lancamento | df.dia_fechamento)], xcol, ycols,
        "SEM LANÇAMENTO NEM FECHAMENTO")

    out = BASE / "teste_pareado_sem_lancamento.txt"
    # persistir resumo simples
    with open(out, "w") as f:
        for k, linhas in res.items():
            f.write(f"[{k}]\n")
            for yc, v in linhas.items():
                f.write(f"{yc}: baixa={v['baixa']:.1f} alta={v['alta']:.1f} "
                        f"var={v['var']:+.1f}% p={v['p']:.3f} IC=[{v['ic'][0]:+.1f},{v['ic'][1]:+.1f}]\n")
            f.write("\n")
    print(f"\nsalvo em {out}")


if __name__ == "__main__":
    main()
