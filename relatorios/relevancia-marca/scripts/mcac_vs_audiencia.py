#!/usr/bin/env python3
"""mCAC (custo da venda adicional) × audiência orgânica.

Replica o método validado em midia-paga/VALIDACOES.md: cada salto natural de budget
(|Δspend| ≥ 25% sobre base de 3 dias estável) é um evento; o contrafactual é a mediana
do ratio de vendas das campanhas ESTÁVEIS do mesmo dia (absorve choque de demanda comum);
mCAC = Δspend / Δvendas_ajustado.

Depois cruza cada salto com o nível de audiência do dia para responder:
o custo da próxima venda é menor quando a marca está em evidência?

A fonte de audiência é parametrizável (--audiencia): hoje roda com o proxy do GA4
(Organic Video); troca para a série real do YouTube Analytics quando disponível.
"""
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

BASE = Path(__file__).resolve().parent.parent / "data"
rng = np.random.default_rng(20260825)

JANELA = 3        # dias de base pré e de janela pós
LIMIAR = 0.25     # |Δspend| mínimo para contar como salto
CV_MAX = 0.35     # coeficiente de variação máximo da base pré (exige base estável)
ESTAVEL = 0.10    # |Δspend| máximo para a campanha entrar no grupo de controle


def carregar_paineis(audiencia_csv=None, audiencia_col=None):
    cd = pd.read_csv(BASE / "spend_vendas_campanha.csv", parse_dates=["dia"])
    if audiencia_csv:
        aud = pd.read_csv(BASE / audiencia_csv, parse_dates=["dia"])[["dia", audiencia_col]]
        aud.columns = ["dia", "audiencia"]
    else:  # proxy: GA4 Organic Video
        ga4 = pd.read_csv(BASE / "ga4_sessions_canal.csv", parse_dates=["dia"])
        w = ga4.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)
        aud = w[["Organic Video"]].rename(columns={"Organic Video": "audiencia"}).reset_index()
    return cd, aud


def montar_eventos(cd: pd.DataFrame) -> pd.DataFrame:
    """Para cada campanha-dia, mede spend/vendas pré (t-3..t-1) e pós (t..t+2)."""
    linhas = []
    for camp, g in cd.groupby("campanha"):
        g = g.set_index("dia").sort_index()
        # grade diária contínua (dias sem spend viram 0 — pausa é informação)
        idx = pd.date_range(g.index.min(), g.index.max(), freq="D")
        g = g.reindex(idx)
        g[["spend", "vendas", "receita"]] = g[["spend", "vendas", "receita"]].fillna(0)
        s, v = g.spend.values, g.vendas.values
        for i in range(JANELA, len(g) - JANELA + 1):
            pre_s, pos_s = s[i - JANELA:i], s[i:i + JANELA]
            pre_v, pos_v = v[i - JANELA:i], v[i:i + JANELA]
            if pre_s.mean() <= 0:
                continue
            cv = pre_s.std() / pre_s.mean() if pre_s.mean() else np.inf
            linhas.append({
                "campanha": camp, "dia": g.index[i],
                "sigla": g.sigla.iloc[i] if pd.notna(g.sigla.iloc[i]) else None,
                "fase": g.fase.iloc[i] if pd.notna(g.fase.iloc[i]) else None,
                "spend_pre": pre_s.mean(), "spend_pos": pos_s.mean(),
                "vendas_pre": pre_v.mean(), "vendas_pos": pos_v.mean(),
                "cv_pre": cv,
            })
    e = pd.DataFrame(linhas)
    e["d_spend_pct"] = e.spend_pos / e.spend_pre - 1
    return e


def calcular_mcac(e: pd.DataFrame) -> pd.DataFrame:
    """Contrafactual = mediana do ratio de vendas das campanhas estáveis do mesmo dia."""
    est = e[(e.d_spend_pct.abs() <= ESTAVEL) & (e.vendas_pre > 0)].copy()
    est["ratio"] = est.vendas_pos / est.vendas_pre
    ctrl = (est.groupby("dia")
               .agg(ratio_ctrl=("ratio", "median"), n_ctrl=("ratio", "size"))
               .reset_index())

    ev = e[(e.d_spend_pct.abs() >= LIMIAR) & (e.cv_pre <= CV_MAX) & (e.vendas_pre > 0)].copy()
    ev = ev.merge(ctrl, on="dia", how="left")
    ev = ev[ev.n_ctrl >= 5]                      # exige donor pool mínimo
    ev["vendas_esp"] = ev.vendas_pre * ev.ratio_ctrl
    ev["d_vendas_adj"] = ev.vendas_pos - ev.vendas_esp
    ev["d_spend"] = (ev.spend_pos - ev.spend_pre) * JANELA   # R$ no bloco de 3 dias
    ev["d_vendas_bloco"] = ev.d_vendas_adj * JANELA
    ev["direcao"] = np.where(ev.d_spend_pct > 0, "up", "down")
    # mCAC só é interpretável quando spend e vendas se movem no mesmo sentido
    ok = (np.sign(ev.d_spend) == np.sign(ev.d_vendas_bloco)) & (ev.d_vendas_bloco.abs() > 0.5)
    ev["mcac"] = np.where(ok, ev.d_spend / ev.d_vendas_bloco, np.nan)
    return ev


def comparar(ev: pd.DataFrame, label: str):
    """mCAC dos saltos em dias de audiência alta vs baixa (mediana, bootstrap)."""
    print(f"\n{'=' * 88}\n{label}\n{'=' * 88}")
    for direcao in ("up", "down"):
        d = ev[(ev.direcao == direcao) & ev.mcac.notna() & ev.audiencia.notna()]
        d = d[(d.mcac > 0) & (d.mcac < 5000)]     # apara caudas absurdas
        if len(d) < 30:
            print(f"  {direcao}: n={len(d)} — insuficiente")
            continue
        corte = d.audiencia.median()
        alta, baixa = d[d.audiencia > corte].mcac, d[d.audiencia <= corte].mcac
        ma, mb = alta.median(), baixa.median()
        _, p = stats.mannwhitneyu(alta, baixa, alternative="two-sided")
        boots = [rng.choice(alta, len(alta), True).mean() / rng.choice(baixa, len(baixa), True).mean()
                 for _ in range(2000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        rho, prho = stats.spearmanr(d.audiencia, d.mcac)
        print(f"  saltos {direcao}  (n={len(d)}: {len(alta)} alta / {len(baixa)} baixa)")
        print(f"    mCAC mediano  audiência BAIXA R$ {mb:,.0f}   |   ALTA R$ {ma:,.0f}   "
              f"→ {100*(ma/mb-1):+.1f}%  p={p:.3f}")
        print(f"    IC95 da razão de médias [{100*(lo-1):+.0f}%, {100*(hi-1):+.0f}%]   "
              f"| Spearman audiência×mCAC rho={rho:+.3f} (p={prho:.3f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audiencia", default=None, help="CSV em data/ com coluna dia + métrica")
    ap.add_argument("--coluna", default="views", help="coluna de audiência no CSV")
    a = ap.parse_args()

    cd, aud = carregar_paineis(a.audiencia, a.coluna)
    fonte = f"{a.audiencia}:{a.coluna}" if a.audiencia else "PROXY GA4 Organic Video"
    print(f"Fonte de audiência: {fonte}")

    e = montar_eventos(cd)
    ev = calcular_mcac(e)

    # audiência do dia, residualizada do calendário (DOW) para não confundir com sazonalidade
    aud = aud.sort_values("dia").copy()
    aud["dow"] = aud.dia.dt.dayofweek
    aud["aud_rel"] = aud.audiencia / aud.groupby("dow").audiencia.transform(
        lambda s: s.rolling(8, min_periods=3, center=True).median())
    ev = ev.merge(aud[["dia", "aud_rel"]].rename(columns={"aud_rel": "audiencia"}), on="dia", how="left")

    print(f"\nEventos detectados: {len(ev)} saltos (|Δspend| ≥ {LIMIAR:.0%}, base 3d com CV ≤ {CV_MAX})")
    print(f"  com mCAC interpretável: {ev.mcac.notna().sum()}")
    v = ev[ev.mcac.notna() & (ev.mcac > 0) & (ev.mcac < 5000)]
    print(f"  mCAC mediano geral: R$ {v.mcac.median():,.0f}  "
          f"(up R$ {v[v.direcao=='up'].mcac.median():,.0f} · down R$ {v[v.direcao=='down'].mcac.median():,.0f})")
    print("  ↳ referência da wiki (pooling jul/2026): LAN-up R$145 · PPT-up R$188")

    comparar(ev, "mCAC × AUDIÊNCIA ORGÂNICA — todos os saltos")
    for fase in ("VENDA", "LEAD"):
        sub = ev[ev.fase == fase]
        if len(sub) > 60:
            comparar(sub, f"mCAC × AUDIÊNCIA — só campanhas [{fase}]")

    ev.to_csv(BASE / "mcac_eventos.csv", index=False)
    print(f"\n→ {len(ev)} eventos salvos em data/mcac_eventos.csv")


if __name__ == "__main__":
    main()
