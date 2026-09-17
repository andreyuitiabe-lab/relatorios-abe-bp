#!/usr/bin/env python3
"""Performance diária — "de onde veio o dia". Roda as queries (bqq) e monta data.json.

Uso:
  python3 refresh.py             # roda queries + monta data.json
  python3 refresh.py --no-query  # só monta data.json a partir dos CSVs em data/

GA4 (data/ga4_sessions_canal.csv: dia,canal,sessions) vem do MCP ga4 (property 378996649,
dimensões date × sessionDefaultChannelGroup) — atualizar à parte até automatizar o fetch.
Desenho e decisões: DESENHO.md · ANALISE.md.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).parent
DATA = BASE / "data"
INI, FIM = "2026-06-01", "2026-09-13"          # janela exibida (baseline usa 4 semanas antes)
QUERIES = {
    "01_vendas_diarias_canal_campanha": "vendas_diarias_canal_campanha.csv",
    "02_spend_vendas_campanha_fonte": "spend_vendas_campanha_fonte.csv",
    "03_estreias_plataforma": "estreias_plataforma.csv",
    "04_abordagens_comercial": "abordagens_comercial.csv",
}
CANAIS = ["Ads Meta", "Ads Google", "CRM", "Comercial", "Orgânico/Portal", "YouTube", "Influenciadores", "Outros/CS"]
# Calendário (wiki campanhas-calendario.md; tb_campaign_period não tem 2026 completo).
# (sigla, aquecimento_ini, venda_ini, venda_fim) — None = em aberto/desconhecido
CAMPANHAS = [
    ("DOM", None, "2026-04-09", "2026-05-15"), ("CDL", "2026-05-06", "2026-05-17", "2026-06-01"),
    ("ELS", "2025-11-01", "2026-05-20", "2026-07-12"), ("EVG", "2026-05-21", "2026-07-08", None),
    ("BP10", "2026-06-11", "2026-07-16", None), ("ODI", None, "2026-07-17", None),
    ("ELB26", "2026-07-14", None, None), ("ENE", "2026-07-28", "2026-07-28", None),
    ("JOM", "2026-07-25", None, None), ("TEC", "2026-08-10", "2026-08-29", None),
    ("CBR", None, "2026-09-01", None), ("10R", None, "2026-01-01", None), ("FNC", None, "2026-01-01", None),
]
rng = np.random.default_rng(20260915)


def run_queries():
    for q, out in QUERIES.items():
        r = subprocess.run(["bqq", str(BASE / "queries" / f"{q}.sql"), "-o", str(DATA / out)], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-800:])
        print(r.stdout.strip().splitlines()[-1])


def fase_do_dia(dia: pd.Timestamp, sigla: str) -> str:
    for s, aq, vi, vf in CAMPANHAS:
        if s != sigla:
            continue
        vi_ = pd.Timestamp(vi) if vi else None
        vf_ = pd.Timestamp(vf) if vf else None
        if vi_ is not None and abs((dia - vi_).days) <= 3 and vi not in ("2026-01-01",):
            return "abertura"
        if vf_ is not None and 0 <= (vf_ - dia).days <= 2:
            return "fechamento"
        if vi_ is not None and dia >= vi_ and (vf_ is None or dia <= vf_):
            return "venda"
        if aq and pd.Timestamp(aq) <= dia and (vi_ is None or dia < vi_):
            return "aquecimento"
    return "sem calendário"


def esperado_dow(serie: pd.Series, dia: pd.Timestamp) -> float:
    """Mediana do mesmo dia-da-semana nas 4 semanas anteriores (NaN se <2 observações)."""
    vals = [serie.get(dia - pd.Timedelta(weeks=w), np.nan) for w in (1, 2, 3, 4)]
    vals = [v for v in vals if pd.notna(v)]
    return float(np.median(vals)) if len(vals) >= 2 else np.nan


def build() -> dict:
    v = pd.read_csv(DATA / QUERIES["01_vendas_diarias_canal_campanha"], parse_dates=["dia"])
    sp = pd.read_csv(DATA / QUERIES["02_spend_vendas_campanha_fonte"], parse_dates=["dia"]).fillna({"spend": 0, "vendas": 0, "receita": 0})
    est = pd.read_csv(DATA / QUERIES["03_estreias_plataforma"], parse_dates=["dia"])
    ab = pd.read_csv(DATA / QUERIES["04_abordagens_comercial"], parse_dates=["dia"]).set_index("dia")
    ga = pd.read_csv(DATA / "ga4_sessions_canal.csv", parse_dates=["dia"])
    gaw = ga.pivot_table(index="dia", columns="canal", values="sessions", aggfunc="sum").fillna(0)

    dias = pd.date_range(v.dia.min(), FIM)
    tot = v.groupby("dia")[["tx", "receita"]].sum().reindex(dias).fillna(0)
    por_canal = v.groupby(["dia", "canal"])[["tx", "receita"]].sum()
    por_sigla_fct = v[v.sigla != "sem_sigla"].groupby(["dia", "sigla"])[["tx", "receita"]].sum()
    por_prod = v.groupby(["dia", "produto"])[["tx", "receita"]].sum()
    prod_canal = v.groupby(["dia", "produto", "canal"]).receita.sum()
    spend_tot = sp.groupby("dia")[["spend", "vendas", "receita"]].sum().reindex(dias).fillna(0)
    spend_meta = sp[sp.fonte == "meta"].groupby("dia").spend.sum().reindex(dias).fillna(0)
    vendas_meta = sp[sp.fonte == "meta"].groupby("dia").vendas.sum().reindex(dias).fillna(0)
    camp = sp.groupby(["dia", "sigla"])[["spend", "vendas", "receita"]].sum()
    yt = gaw.get("Organic Video", pd.Series(dtype=float)).reindex(dias)
    busca = gaw.get("Organic Search", pd.Series(dtype=float)).reindex(dias)
    mm28 = lambda s, d: s.loc[d - pd.Timedelta(days=28): d - pd.Timedelta(days=1)].mean()
    nao_meta = (tot.tx - vendas_meta).clip(lower=0)

    days_out = []
    for d in pd.date_range(INI, FIM):
        real_tx, real_rec = float(tot.tx[d]), float(tot.receita[d])
        esp_tx, esp_rec = esperado_dow(tot.tx, d), esperado_dow(tot.receita, d)
        if not (pd.notna(esp_tx) and esp_tx > 0):
            continue
        tk_real, tk_esp = real_rec / max(real_tx, 1), esp_rec / esp_tx
        vol = (real_tx - esp_tx) * tk_esp
        tkt = real_tx * (tk_real - tk_esp)
        # canais
        canais = []
        for c in CANAIS:
            s_tx = por_canal.xs(c, level="canal").tx if c in por_canal.index.get_level_values("canal") else pd.Series(dtype=float)
            s_rec = por_canal.xs(c, level="canal").receita if c in por_canal.index.get_level_values("canal") else pd.Series(dtype=float)
            rt, rr = float(s_tx.get(d, 0)), float(s_rec.get(d, 0))
            et, er = esperado_dow(s_tx.reindex(dias).fillna(0), d), esperado_dow(s_rec.reindex(dias).fillna(0), d)
            canais.append(dict(canal=c, tx=rt, tx_esp=round(et, 1), receita=round(rr), receita_esp=round(er), delta=round(rr - er)))
        # campanhas de ads (atribuição da plataforma): gasto × eficiência
        camps = []
        sig_dia = camp.xs(d, level="dia") if d in camp.index.get_level_values("dia") else pd.DataFrame()
        sig_all = set(sig_dia.index) | {s for s in camp.index.get_level_values("sigla")
                                          if any((d - pd.Timedelta(weeks=w), s) in camp.index for w in (1, 2, 3, 4))}
        for s in sig_all:
            ser = camp.xs(s, level="sigla").reindex(dias).fillna(0)
            sr, rr_, vr = float(ser.spend.get(d, 0)), float(ser.receita.get(d, 0)), float(ser.vendas.get(d, 0))
            se, re_ = esperado_dow(ser.spend, d), esperado_dow(ser.receita, d)
            se, re_ = (0.0 if pd.isna(se) else se), (0.0 if pd.isna(re_) else re_)
            if sr < 500 and se < 500:
                continue
            roas_r = rr_ / sr if sr else 0.0
            roas_e = re_ / se if se else roas_r
            gasto = (sr - se) * roas_e
            efic = sr * (roas_r - roas_e)
            fct = por_sigla_fct.xs(s, level="sigla") if s in por_sigla_fct.index.get_level_values("sigla") else None
            camps.append(dict(sigla=s, spend=round(sr), spend_esp=round(se), receita=round(rr_), receita_esp=round(re_),
                              vendas=vr, roas=round(roas_r, 2), roas_esp=round(roas_e, 2), cpa=round(sr / vr) if vr else None,
                              gasto=round(gasto), eficiencia=round(efic),
                              tx_fct=float(fct.tx.get(d, 0)) if fct is not None else None))
        # produtos: o que fez o ticket/mix
        prods = []
        pd_dia = por_prod.xs(d, level="dia") if d in por_prod.index.get_level_values("dia") else pd.DataFrame()
        cand = set(pd_dia.index) | {pr for w in (1, 2, 3, 4) for pr in
                                    (por_prod.xs(d - pd.Timedelta(weeks=w), level="dia").index if (d - pd.Timedelta(weeks=w)) in por_prod.index.get_level_values("dia") else [])}
        for pr in cand:
            ser = por_prod.xs(pr, level="produto").reindex(dias).fillna(0)
            rt, rr = float(ser.tx.get(d, 0)), float(ser.receita.get(d, 0))
            et, er = esperado_dow(ser.tx, d), esperado_dow(ser.receita, d)
            et, er = (0.0 if pd.isna(et) else et), (0.0 if pd.isna(er) else er)
            if abs(rr - er) < 3000:
                continue
            pc = prod_canal.xs((d, pr), level=("dia", "produto")) if (d, pr) in prod_canal.index.droplevel("canal") else pd.Series(dtype=float)
            prods.append(dict(produto=pr, tx=rt, tx_esp=round(et, 1), receita=round(rr), receita_esp=round(er), delta=round(rr - er),
                              ticket=round(rr / rt) if rt else None, canal_principal=(pc.idxmax() if len(pc) else None),
                              share_canal=round(100 * pc.max() / pc.sum()) if len(pc) and pc.sum() else None))
        prods.sort(key=lambda x: -abs(x["delta"]))
        camps.sort(key=lambda x: -abs(x["gasto"] + x["eficiencia"]))
        dom = max(camps, key=lambda x: x["spend"])["sigla"] if camps else None
        fase = fase_do_dia(d, dom) if dom else "sem calendário"
        # contexto
        estreias = est[est.dia == d].sort_values("usuarios_d0", ascending=False)
        ab_real = float(ab.abordagens.get(d, np.nan)); ab_esp = esperado_dow(ab.abordagens.reindex(dias), d)
        ctx = dict(
            yt=None if pd.isna(yt.get(d)) else int(yt[d]), yt_mm28=None if pd.isna(mm28(yt, d)) else round(mm28(yt, d)),
            busca=None if pd.isna(busca.get(d)) else int(busca[d]), busca_mm28=None if pd.isna(mm28(busca, d)) else round(mm28(busca, d)),
            demanda_nao_meta=round(float(nao_meta[d]) / esperado_dow(nao_meta, d), 2) if esperado_dow(nao_meta, d) else None,
            abordagens=None if pd.isna(ab_real) else int(ab_real), abordagens_esp=None if pd.isna(ab_esp) else round(ab_esp),
            estreias=[dict(midia=r.nm_media, playlist=r.nm_playlist, usuarios=int(r.usuarios_d0)) for r in estreias.head(4).itertuples()],
        )
        spend_real, spend_esp = float(spend_tot.spend[d]), esperado_dow(spend_tot.spend, d)
        days_out.append(dict(
            dia=d.strftime("%Y-%m-%d"), dow=int(d.dayofweek), sigla_dom=dom, fase=fase,
            real=dict(tx=real_tx, receita=round(real_rec), ticket=round(tk_real)),
            esperado=dict(tx=round(esp_tx, 1), receita=round(esp_rec), ticket=round(tk_esp)),
            delta=round(real_rec - esp_rec), delta_pct=round(100 * (real_rec / esp_rec - 1), 1),
            decomp=dict(volume=round(vol), ticket=round(tkt)),
            spend=dict(real=round(spend_real), esp=round(spend_esp) if pd.notna(spend_esp) else None,
                       roas=round(real_rec / spend_real, 2) if spend_real else None),
            canais=canais, campanhas=camps[:12], produtos=prods[:10], contexto=ctx,
        ))

    df = pd.DataFrame([dict(dia=x["dia"], resid=x["delta_pct"] / 100, fase=x["fase"], receita=x["real"]["receita"], esp=x["esperado"]["receita"],
                            yt_r=(x["contexto"]["yt"] / x["contexto"]["yt_mm28"]) if x["contexto"]["yt"] and x["contexto"]["yt_mm28"] else np.nan,
                            estreia=max([e["usuarios"] for e in x["contexto"]["estreias"]] or [0]),
                            spend_r=(x["spend"]["real"] / x["spend"]["esp"]) if x["spend"]["esp"] else np.nan,
                            ab_r=(x["contexto"]["abordagens"] / x["contexto"]["abordagens_esp"]) if x["contexto"]["abordagens"] and x["contexto"]["abordagens_esp"] else np.nan,
                            dem=x["contexto"]["demanda_nao_meta"] or np.nan) for x in days_out])
    df["dia"] = pd.to_datetime(df.dia); df["yt_ontem_r"] = df.yt_r.shift(1)

    # fases: resíduo médio por fase
    fases = [dict(fase=f, n=int(g.resid.size), resid_medio=round(100 * g.resid.mean(), 1), resid_mediano=round(100 * g.resid.median(), 1))
             for f, g in df.groupby("fase")]

    # alavancas — últimos 90 dias
    d90 = df[df.dia > df.dia.max() - pd.Timedelta(days=90)].copy()
    lancamento = d90.fase.isin(["abertura"])
    alavancas = []
    defs = [
        ("YT orgânico hoje > 1,3× MM28", d90.yt_r > 1.3, "contexto"),
        ("YT orgânico ontem > 1,3× MM28", d90.yt_ontem_r > 1.3, "contexto"),
        ("Estreia na plataforma ≥ 500 usuários", d90.estreia >= 500, "conteúdo"),
        ("Spend total > 1,2× esperado", d90.spend_r > 1.2, "mídia"),
        ("Abordagens Comercial > 1,2× esperado", d90.ab_r > 1.2, "comercial"),
        ("Demanda não-Meta > 1,1× esperado", d90.dem > 1.1, "contexto"),
        ("Fase: abertura de venda (±3d)", d90.fase == "abertura", "calendário"),
        ("Fase: fechamento (−2..0)", d90.fase == "fechamento", "calendário"),
        ("Fase: aquecimento", d90.fase == "aquecimento", "calendário"),
    ]
    for nome, mask, grupo in defs:
        ok = mask.notna() & d90.resid.notna()
        a, b = d90.resid[ok & mask.fillna(False)], d90.resid[ok & ~mask.fillna(False)]
        if len(a) < 4 or len(b) < 4:
            alavancas.append(dict(alavanca=nome, grupo=grupo, n_com=int(len(a)), n_sem=int(len(b)), veredito="sem dias suficientes")); continue
        diff = a.mean() - b.mean()
        boots = [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(2000)]
        lo, hi = np.percentile(boots, [2.5, 97.5]); se = np.std(boots)
        mde = 2.8 * se
        # robustez: sem dias de abertura
        a2, b2 = d90.resid[ok & mask.fillna(False) & ~lancamento], d90.resid[ok & ~mask.fillna(False) & ~lancamento]
        diff2 = (a2.mean() - b2.mean()) if len(a2) >= 4 and len(b2) >= 4 else np.nan
        if lo > 0 or hi < 0:
            ver = "sinal" if (pd.isna(diff2) or np.sign(diff2) == np.sign(diff)) else "sinal só com lançamentos"
        else:
            ver = "inconclusivo"
        alavancas.append(dict(alavanca=nome, grupo=grupo, n_com=int(len(a)), n_sem=int(len(b)),
                              com=round(100 * a.mean(), 1), sem=round(100 * b.mean(), 1), diff=round(100 * diff, 1),
                              ic=[round(100 * lo, 1), round(100 * hi, 1)], mde=round(100 * mde, 1),
                              diff_sem_lancamento=None if pd.isna(diff2) else round(100 * diff2, 1), veredito=ver))

    # semanas (seg–dom) — agregação simples de real/esperado/decomp/canais/campanhas
    semanas = []
    df_days = {x["dia"]: x for x in days_out}
    wk = pd.Series({pd.Timestamp(k): k for k in df_days}).sort_index()
    for (ano, sem), g in wk.groupby([wk.index.isocalendar().year, wk.index.isocalendar().week]):
        xs = [df_days[k] for k in g.values]
        if len(xs) < 7:
            continue
        rec_r = sum(x["real"]["receita"] for x in xs); rec_e = sum(x["esperado"]["receita"] for x in xs)
        tx_r = sum(x["real"]["tx"] for x in xs); tx_e = sum(x["esperado"]["tx"] for x in xs)
        can = {c: dict(canal=c, receita=0, receita_esp=0) for c in CANAIS}
        for x in xs:
            for c in x["canais"]:
                can[c["canal"]]["receita"] += c["receita"]; can[c["canal"]]["receita_esp"] += c["receita_esp"]
        cam = {}
        for x in xs:
            for c in x["campanhas"]:
                e = cam.setdefault(c["sigla"], dict(sigla=c["sigla"], spend=0, spend_esp=0, receita=0, receita_esp=0, gasto=0, eficiencia=0, vendas=0))
                for k in ("spend", "spend_esp", "receita", "receita_esp", "gasto", "eficiencia", "vendas"):
                    e[k] += c[k]
        cams = sorted(cam.values(), key=lambda c: -c["spend"])[:10]
        for c in cams:
            c["roas"] = round(c["receita"] / c["spend"], 2) if c["spend"] else None
            c["roas_esp"] = round(c["receita_esp"] / c["spend_esp"], 2) if c["spend_esp"] else None
        semanas.append(dict(semana=f"{g.index.min():%d/%m}–{g.index.max():%d/%m}", ini=g.index.min().strftime("%Y-%m-%d"),
                            real=dict(tx=tx_r, receita=rec_r), esperado=dict(tx=round(tx_e), receita=rec_e),
                            delta=rec_r - rec_e, delta_pct=round(100 * (rec_r / rec_e - 1), 1) if rec_e else None,
                            decomp=dict(volume=sum(x["decomp"]["volume"] for x in xs), ticket=sum(x["decomp"]["ticket"] for x in xs)),
                            spend=sum(x["spend"]["real"] for x in xs), spend_esp=sum((x["spend"]["esp"] or 0) for x in xs),
                            canais=[dict(v, delta=v["receita"] - v["receita_esp"]) for v in can.values()], campanhas=cams,
                            fases=sorted({x["fase"] for x in xs})))

    return dict(
        meta=dict(gerado=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"), janela=[INI, FIM], ultimo_dia=days_out[-1]["dia"],
                  baseline="mediana do mesmo dia da semana nas 4 semanas anteriores",
                  fontes=["fct_transactions (publisher/UTM)", "dtm_analytics_facebook/google/pmax_ads_funnel", "GA4 sessions", "obt_kafka__view_sessions", "dtm_sales_by_zenvia"],
                  avisos=["Atribuição não é incrementalidade.", "Receita por campanha em ads é a atribuída pela plataforma (Meta/Google), não a da fct_transactions.",
                          "CPA/ROAS de ads maturam em D+2 — os 2 últimos dias podem mudar.", "Abordagens Comercial de 01–04/09 estão subestimadas (recarga de 08/09)."]),
        canais=CANAIS, dias=days_out, semanas=semanas, fases=fases, alavancas=alavancas,
        alavancas_meta=dict(janela_dias=90, ini=d90.dia.min().strftime("%Y-%m-%d"), fim=d90.dia.max().strftime("%Y-%m-%d"),
                            nota="resíduo = receita real ÷ esperada − 1; IC95 bootstrap de dias (anti-conservador: dias autocorrelacionados); MDE = efeito mínimo detectável com 80% de poder"),
    )


if __name__ == "__main__":
    if "--no-query" not in sys.argv:
        run_queries()
    D = build()
    (BASE / "data.json").write_text(json.dumps(D, ensure_ascii=False))
    print(f"data.json: {len(D['dias'])} dias, {len(D['semanas'])} semanas, {len(D['alavancas'])} alavancas · último dia {D['meta']['ultimo_dia']}")
