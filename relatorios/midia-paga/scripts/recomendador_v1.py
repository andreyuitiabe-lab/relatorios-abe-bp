#!/usr/bin/env python3
"""
Recomendador de budget Meta [VENDA] — v1 (desenho final pós-validações de jul/2026,
parâmetros revisados em 10/09/2026).

Uso:
  python recomendador_v1.py              # recomendação de hoje (dados D-2)
  python recomendador_v1.py --backtest   # gate: ROAS D+1..D+3 por bucket de ação

Desenho (VALIDACOES.md + revisão 10/09):
  teto_dia(campanha) = MARGEM × ticket_30d(campanha) × demand_index(ontem)
  LAN em ramp (MA3 spend subindo)  -> SEM recomendação; ALERTA se ROAS_3d<0,7 e CPA_3d>teto
  LAN pós-pico                     -> Abordagem C (CPA_3d / CPA rolling 21d) OU absoluta
  PPT                              -> absoluta (CPA_3d vs teto, com ROAS_3d)
  reduzir se (C>1,30) OU (CPA_3d>teto E ROAS_3d<1) ; aumentar se C<0,85 E CPA_3d<teto
  step-limit ±20%/dia ; stop-loss por idade: D5 ROAS_acum<0,7 | D7 <0,7 | D10 <0,9 -> PIVOTAR
  Nível estratégico: I* = (b·β_t·m)^(1/(1-b)), b=0,70, β EWMA meia-vida 7d (recalcular semanal)

Fonte: dtm_analytics_facebook_ads_funnel via bqq (~/bin). Janela de decisão D-2 (H2).
Margem: MARGEM=0,75 digital (MARGEM.md — cenário central; refinar com financeiro).
"""
import argparse
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent.parent
DADOS = HERE / "dados_recomendador"
DADOS.mkdir(exist_ok=True)

MARGEM = 0.75          # cenário central digital (MARGEM.md)
B = 0.70               # concavidade revisada 10/09
HL_BETA = 7            # meia-vida do beta estratégico (revisão 10/09)
C_REDUZIR, C_AUMENTAR = 1.30, 0.85
STEP = 0.20
MIN_SPEND_DIA = 500.0

def bqq(sql: str) -> pd.DataFrame:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        out = f.name
    r = subprocess.run([str(Path.home() / "bin" / "bqq"), sql, "-o", out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"bqq falhou: {r.stderr[-500:]}")
    return pd.read_csv(out)

def carregar(dt_ini: str, dt_fim: str) -> pd.DataFrame:
    df = bqq(f"""
      SELECT reference_date d, nm_campaign_name camp,
             ROUND(SUM(vl_amount_spent),2) spend,
             ROUND(SUM(vl_total_revenue),2) receita,
             SUM(qt_total_sales) vendas
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
      WHERE reference_date BETWEEN '{dt_ini}' AND '{dt_fim}'
        AND UPPER(nm_campaign_name) LIKE '%[VENDA]%'
      GROUP BY 1,2""")
    df["d"] = pd.to_datetime(df["d"])
    df["tipo"] = np.where(df["camp"].str.upper().str.contains(r"\[PPT\]"), "PPT",
                 np.where(df["camp"].str.upper().str.contains(r"\[LAN\]"), "LAN", "OUTRO"))
    return df.sort_values(["camp", "d"])

def demand_index(dt_ini: str, dt_fim: str) -> pd.Series:
    """Vendas novas não-Meta normalizadas (média 1) — validação H3: usar o de ontem."""
    tot = bqq(f"""
      SELECT DATE(dt_ordered_at) d, COUNT(*) v
      FROM `bp-datawarehouse.masterdata.fct_transactions`
      WHERE nm_status='approved' AND bl_is_renovation=FALSE
        AND DATE(dt_ordered_at) BETWEEN '{dt_ini}' AND '{dt_fim}' GROUP BY 1""")
    meta = bqq(f"""
      SELECT reference_date d, SUM(qt_total_sales) v
      FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
      WHERE reference_date BETWEEN '{dt_ini}' AND '{dt_fim}' GROUP BY 1""")
    for x in (tot, meta):
        x["d"] = pd.to_datetime(x["d"])
    m = tot.merge(meta, on="d", how="left", suffixes=("_tot", "_meta")).fillna(0)
    m["nm"] = (m["v_tot"] - m["v_meta"]).clip(lower=0)
    s = m.set_index("d")["nm"]
    return s / s.mean()

def sinais_do_dia(g: pd.DataFrame, asof: pd.Timestamp, di: float) -> dict | None:
    """Recomendação para uma campanha com dados <= asof (asof já é D-2 na prática)."""
    g = g[g["d"] <= asof]
    if len(g) < 3 or g["spend"].tail(3).sum() < 3 * MIN_SPEND_DIA:
        return None
    ult3, ult21 = g.tail(3), g.tail(21)
    spend3, vendas3, rec3 = ult3["spend"].sum(), ult3["vendas"].sum(), ult3["receita"].sum()
    cpa3 = spend3 / vendas3 if vendas3 > 0 else np.inf
    roas3 = rec3 / spend3 if spend3 > 0 else 0.0
    cpa21 = ult21["spend"].sum() / max(ult21["vendas"].sum(), 1)
    ticket30 = (g.tail(30)["receita"].sum() / max(g.tail(30)["vendas"].sum(), 1))
    teto = MARGEM * ticket30 * di
    c_ratio = cpa3 / cpa21 if np.isfinite(cpa3) and cpa21 > 0 else np.nan

    idade = len(g)
    roas_acum = g["receita"].sum() / max(g["spend"].sum(), 1)
    stop = None
    if idade >= 10 and roas_acum < 0.9: stop = "PIVOTAR (D10: ROAS acum < 0,9)"
    elif idade >= 7 and roas_acum < 0.7: stop = "PIVOTAR (D7: ROAS acum < 0,7)"
    elif idade >= 5 and roas_acum < 0.7: stop = "PIVOTAR (D5: ROAS acum < 0,7)"
    elif idade <= 3 and roas3 < 0.7: stop = "CONGELAR (learning, ROAS<0,7)"

    ma3 = g["spend"].rolling(3).mean()
    ramp = len(ma3.dropna()) >= 3 and ma3.iloc[-1] > 1.05 * ma3.iloc[-3]
    tipo = g["tipo"].iloc[-1]

    if stop:
        acao, motivo = "REDUZIR", stop
    elif tipo == "LAN" and ramp:
        if roas3 < 0.7 and cpa3 > teto:
            acao, motivo = "ALERTA", f"ramp com ROAS_3d {roas3:.2f} e CPA {cpa3:.0f}>teto {teto:.0f}"
        else:
            acao, motivo = "SEM REC.", "LAN em ramp — plano de lançamento manda"
    else:
        reduzir = (not np.isnan(c_ratio) and c_ratio > C_REDUZIR) or (cpa3 > teto and roas3 < 1)
        aumentar = (not np.isnan(c_ratio) and c_ratio < C_AUMENTAR) and cpa3 < teto and roas3 > 1
        if reduzir:
            acao, motivo = "REDUZIR", f"C={c_ratio:.2f} | CPA_3d R${cpa3:.0f} vs teto R${teto:.0f} | ROAS_3d {roas3:.2f}"
        elif aumentar:
            acao, motivo = "AUMENTAR", f"C={c_ratio:.2f} | CPA_3d R${cpa3:.0f} < teto R${teto:.0f} | ROAS_3d {roas3:.2f}"
        else:
            acao, motivo = "MANTER", f"C={c_ratio:.2f} | CPA_3d R${cpa3:.0f} vs teto R${teto:.0f}"
    return {"acao": acao, "motivo": motivo, "tipo": tipo, "spend_3d_med": spend3 / 3,
            "cpa3": cpa3, "roas3": roas3, "teto": teto, "idade_d": idade,
            "roas_acum": roas_acum, "ramp": ramp}

def portfolio_istar(df: pd.DataFrame) -> str:
    p = df.groupby("d")[["spend", "receita"]].sum()
    p = p[p["spend"] > 5000]
    beta = (p["receita"] / p["spend"] ** B).ewm(halflife=HL_BETA).mean().iloc[-1]
    atual = p["spend"].tail(7).mean()
    mroas = B * beta * atual ** (B - 1)
    istar = lambda m: (B * beta * m) ** (1 / (1 - B))
    return (f"[estratégico] spend MA7 R${atual:,.0f}/dia | ROAS marginal {mroas:.2f} | "
            f"I*(m=0,75)=R${istar(0.75):,.0f} | I*(m=1,0 teto receita)=R${istar(1.0):,.0f}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: hoje-2, regra H2)")
    args = ap.parse_args()

    hoje = date.today()
    asof = pd.Timestamp(args.asof) if args.asof else pd.Timestamp(hoje - timedelta(days=2))
    dt_ini = (asof - pd.Timedelta(days=200)).date().isoformat()
    df = carregar(dt_ini, asof.date().isoformat())
    di_serie = demand_index(dt_ini, asof.date().isoformat())

    if args.backtest:
        rows = []
        dias = sorted(df["d"].unique())
        for dcut in dias[45:-3]:
            dcut = pd.Timestamp(dcut)
            di = float(di_serie.reindex([dcut - pd.Timedelta(days=1)]).fillna(1.0).iloc[0])
            fut = df[(df["d"] > dcut) & (df["d"] <= dcut + pd.Timedelta(days=3))]
            for camp, g in df.groupby("camp"):
                s = sinais_do_dia(g, dcut, di)
                if not s: continue
                f = fut[fut["camp"] == camp]
                if f["spend"].sum() < 1000: continue
                rows.append({"acao": s["acao"], "roas_fut": f["receita"].sum() / f["spend"].sum()})
        bt = pd.DataFrame(rows)
        print("\n=== GATE: ROAS mediano D+1..D+3 por bucket (monotônico = passa) ===")
        print(bt.groupby("acao")["roas_fut"].agg(["median", "count"]).round(2).to_string())
        return

    di = float(di_serie.iloc[-1])
    recs = []
    for camp, g in df.groupby("camp"):
        if g["d"].max() < asof - pd.Timedelta(days=5): continue  # só ativas
        s = sinais_do_dia(g, asof, di)
        if s: recs.append({"campanha": camp[:60], **s})
    out = pd.DataFrame(recs).sort_values(["acao", "spend_3d_med"], ascending=[True, False])
    csv = DADOS / f"recomendacao_{asof.date()}.csv"
    out.to_csv(csv, index=False)
    print(f"Recomendador v1 — as-of {asof.date()} (D-2) | demand_index(ontem)={di:.2f} | margem={MARGEM}")
    print(portfolio_istar(df))
    print(f"\n{len(out)} campanhas ativas | step-limit: qualquer mudança ±{STEP:.0%}/dia\n")
    for acao in ["REDUZIR", "ALERTA", "AUMENTAR", "MANTER", "SEM REC."]:
        sub = out[out["acao"] == acao]
        if len(sub) == 0: continue
        print(f"── {acao} ({len(sub)}) ──")
        for _, r in sub.head(12).iterrows():
            print(f"  {r['campanha']:<60} R${r['spend_3d_med']:>9,.0f}/d  {r['motivo']}")
    print(f"\nCSV: {csv}")

if __name__ == "__main__":
    main()
