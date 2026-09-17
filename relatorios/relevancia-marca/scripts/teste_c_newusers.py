#!/usr/bin/env python3
"""Teste C — GA4 newUsers como indicador diário de relevância.

newUsers mede gente NOVA chegando (não membro voltando) — conceitualmente melhor
que sessões. Passa no crivo da rodada 4? Supera YouTube orgânico / busca / Wikipedia?

Dois estágios (venvs diferentes):
  1) fetch (cliente GA4 do MCP, sem pandas):
     /Users/andre.abe/meu_projeto/BigQuery/mcp-ga4/.venv/bin/python teste_c_newusers.py --fetch
  2) crivo (pandas/scipy — mesma especificação do avaliar_fontes.py):
     python3 teste_c_newusers.py

Saídas: data/teste_c_ga4_newusers.csv · data/teste_c_avaliacao.csv ·
        data/teste_c_pareado_resultado.txt
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "data"
MCP_GA4 = Path("/Users/andre.abe/meu_projeto/BigQuery/mcp-ga4")
PROPERTY = "properties/378996649"
START, END = "2025-08-01", "yesterday"
CANAIS = ["Organic Video", "Organic Search", "Direct", "Organic Social", "Referral"]


# ---------------------------------------------------------------- estágio 1: fetch
def fetch():
    """Puxa newUsers diário (total + por canal) via GA4 Data API (mesma credencial do MCP)."""
    import csv
    sys.path.insert(0, str(MCP_GA4))
    from auth import get_credentials
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest

    client = BetaAnalyticsDataClient(credentials=get_credentials())

    def report(dims, mets):
        req = RunReportRequest(
            property=PROPERTY,
            dimensions=[Dimension(name=d) for d in dims],
            metrics=[Metric(name=m) for m in mets],
            date_ranges=[DateRange(start_date=START, end_date=END)],
            limit=100000,
        )
        r = client.run_report(req)
        return [[dv.value for dv in row.dimension_values] + [mv.value for mv in row.metric_values]
                for row in r.rows]

    dados = {}  # dia -> dict de colunas

    def slug(c): return c.lower().replace(" ", "_")

    for d, nu, tu in report(["date"], ["newUsers", "totalUsers"]):
        dia = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        dados[dia] = {"newusers_total": int(nu), "totalusers_total": int(tu)}

    # recorte (a): sessionDefaultChannelGroup — canal da SESSÃO em que o usuário foi novo
    # recorte (b): firstUserDefaultChannelGroup — canal de AQUISIÇÃO do usuário (semanticamente
    #   mais correto para newUsers). Puxo os dois; se o session-scoped não combinar, fica só o first.
    for dim, pref in [("sessionDefaultChannelGroup", "nu_sess"),
                      ("firstUserDefaultChannelGroup", "nu_first")]:
        try:
            rows = report(["date", dim], ["newUsers"])
        except Exception as e:  # dimensão incompatível com newUsers
            print(f"AVISO: {dim} × newUsers falhou: {e}")
            continue
        for d, canal, nu in rows:
            dia = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            if canal in CANAIS and dia in dados:
                dados[dia][f"{pref}_{slug(canal)}"] = int(nu)
        print(f"{dim}: OK ({len(rows)} linhas)")

    cols = ["dia", "newusers_total", "totalusers_total"] + \
        [f"{p}_{slug(c)}" for p in ("nu_sess", "nu_first") for c in CANAIS]
    out = BASE / "teste_c_ga4_newusers.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for dia in sorted(dados):
            w.writerow([dia] + [dados[dia].get(c, 0) for c in cols[1:]])
    print(f"salvo: {out} ({len(dados)} dias, {sorted(dados)[0]} → {sorted(dados)[-1]})")


# ---------------------------------------------------------------- estágio 2: crivo
def crivo():
    """Aplica o crivo da rodada 4 (especificação idêntica ao avaliar_fontes.py)."""
    import numpy as np
    import pandas as pd
    from scipy import stats
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from event_study import carregar_painel

    df = carregar_painel()
    nu = pd.read_csv(BASE / "teste_c_ga4_newusers.csv", parse_dates=["dia"])
    df = df.merge(nu, on="dia", how="inner")  # janela = interseção com painel (385+ dias c/ spend)
    df["cac_ads"] = df.spend_total / df.tx_ads.replace(0, np.nan)

    CANDIDATOS = {
        "newusers_total":         "newUsers TOTAL (GA4)",
        "nu_sess_organic_video":  "newUsers Organic Video (sess.)",
        "nu_sess_organic_search": "newUsers Organic Search (sess.)",
        "nu_sess_direct":         "newUsers Direct (sess.)",
        "nu_sess_organic_social": "newUsers Organic Social (sess.)",
        "nu_sess_referral":       "newUsers Referral (sess.)",
        "nu_first_organic_video": "newUsers Organic Video (1st-user)",
        "nu_first_organic_search": "newUsers Organic Search (1st-user)",
        "nu_first_direct":        "newUsers Direct (1st-user)",
        "nu_first_organic_social": "newUsers Organic Social (1st-user)",
        "nu_first_referral":      "newUsers Referral (1st-user)",
    }
    CANDIDATOS = {c: n for c, n in CANDIDATOS.items() if c in df.columns and df[c].sum() > 0}

    # === especificação exata do avaliar_fontes.py ===
    def resid(y, X):
        yl = np.log1p(y.astype(float).clip(lower=0))
        ok = yl.notna() & np.isfinite(yl) & X.notna().all(axis=1)
        b, *_ = np.linalg.lstsq(X[ok].values, yl[ok].values, rcond=None)
        r = yl - X.values @ b
        r[~ok] = np.nan
        return r

    X = pd.get_dummies(df.dia.dt.dayofweek, prefix="d", drop_first=True).astype(float)
    X = pd.concat([X, pd.get_dummies(df.dia.dt.month, prefix="m", drop_first=True).astype(float)], axis=1)
    X["log_spend"] = np.log1p(df.spend_total)
    X["venda"] = df.em_venda
    X["aq"] = df.em_aquecimento
    X["t"] = (df.dia - df.dia.min()).dt.days / 365
    X.insert(0, "const", 1.0)

    r_tx = resid(df.tx_total, X)
    r_cac = resid(df.cac_ads, X)

    print(f"janela do crivo: {df.dia.min():%Y-%m-%d} → {df.dia.max():%Y-%m-%d} ({len(df)} dias)\n")
    print("medianas/dia dos recortes:")
    for c, nome in CANDIDATOS.items():
        print(f"  {nome:<36}{df[c].median():>10,.0f}")

    print(f"\n{'indicador':<42}{'dias':>6}{'ρ c/ spend':>12}{'indep?':>9}{'ρ→vendas':>11}{'ρ→CAC':>9}{'veredito':>26}")
    print("-" * 116)
    linhas = []
    for c, nome in CANDIDATOS.items():
        s = df[c]
        n = int(s.notna().sum())
        rho_sp, _ = stats.spearmanr(s, df.spend_total, nan_policy="omit")
        rc = resid(s, X)
        m1 = rc.notna() & r_tx.notna()
        rho_tx, p_tx = stats.spearmanr(rc[m1], r_tx[m1])
        m2 = rc.notna() & r_cac.notna()
        rho_cac, p_cac = stats.spearmanr(rc[m2], r_cac[m2])
        indep = "SIM" if abs(rho_sp) < 0.30 else ("meio" if abs(rho_sp) < 0.55 else "NÃO")
        if indep == "NÃO":
            ver = "mede orçamento"
        elif p_tx < 0.05 and p_cac < 0.05 and rho_tx > 0 and rho_cac < 0:
            ver = "★ volume + eficiência"
        elif p_tx < 0.05 and rho_tx > 0:
            ver = "só volume"
        elif p_cac < 0.05 and rho_cac < 0:
            ver = "só eficiência"
        else:
            ver = "sem sinal"
        print(f"{nome:<42}{n:>6}{rho_sp:>12.3f}{indep:>9}{rho_tx:>10.3f}{'*' if p_tx < 0.05 else ' '}"
              f"{rho_cac:>8.3f}{'*' if p_cac < 0.05 else ' '}{ver:>26}")
        linhas.append(dict(indicador=nome, dias=n, rho_spend=rho_sp, indep=indep,
                           rho_vendas=rho_tx, p_vendas=p_tx, rho_cac=rho_cac, p_cac=p_cac, veredito=ver))

    # tabela combinada: 11 indicadores da rodada 4 + os recortes de newUsers
    antigos = pd.read_csv(BASE / "avaliacao_fontes.csv")
    antigos["origem"] = "rodada 4"
    novos = pd.DataFrame(linhas)
    novos["origem"] = "teste C"
    comb = pd.concat([antigos, novos], ignore_index=True).sort_values("rho_cac")
    comb.to_csv(BASE / "teste_c_avaliacao.csv", index=False)
    print(f"\nsalvo: {BASE / 'teste_c_avaliacao.csv'} (11 da rodada 4 + {len(novos)} newUsers)")
    print("* = p<0,05 | ρ c/ spend: |ρ|<0,30 = independente · >0,55 = mede orçamento")
    print("ρ→CAC negativo é BOM (aquisição mais barata quando o indicador sobe)")

    # consistência total vs soma dos canais (thresholding do GA4 aparece aqui)
    soma_first = df[[c for c in df.columns if c.startswith("nu_first")]].sum(axis=1)
    print(f"\ncanais de interesse (1st-user) cobrem {100 * soma_first.sum() / df.newusers_total.sum():.1f}% "
          f"do newUsers total (resto = Paid Social/Search, Unassigned etc.)")
    return df


def pareado(df, xcol, xnome):
    """Bônus: pareamento por spend (mesmo desenho do teste_pareado_spend.py)."""
    import contextlib
    import io
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from teste_pareado_spend import teste_pareado

    df = df.copy()
    df["roas_dia"] = df.receita_total / df.spend_total.replace(0, np.nan)
    ycols = {"tx_total": "Transações/dia", "receita_total": "Receita/dia (R$)",
             "tx_organico": "Tx canais orgânicos", "tx_digital": "Tx digitais",
             "cac_ads": "CAC de ads (R$)", "roas_dia": "ROAS",
             "conv_por_sessao": "Tx digitais/1k sessões", "ticket_medio": "Ticket médio (R$)",
             "spend_total": "Spend/dia (R$) [checagem]"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        teste_pareado(df, xcol, xnome, ycols)
    txt = buf.getvalue()
    print(txt)
    (BASE / "teste_c_pareado_resultado.txt").write_text(txt)
    print(f"salvo: {BASE / 'teste_c_pareado_resultado.txt'}")


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    else:
        df = crivo()
        # bônus: pareamento por spend do melhor recorte orgânico (definido após o crivo)
        alvo = sys.argv[1] if len(sys.argv) > 1 else "nu_first_organic_video"
        if alvo in df.columns:
            pareado(df, alvo, f"NEWUSERS {alvo} — pareamento por spend")
