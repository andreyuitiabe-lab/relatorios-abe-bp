#!/usr/bin/env python3
"""
Relatório: Aquecimento · Qualidade — acompanhamento da captação por campanha (IQL + RPL).

Página por campanha no formato do mockup aprovado (artifact a3fd60ec): métrica-mestra
retorno esperado = RPL projetado ÷ CPL (meta 1,5× — D52), régua CPL → CPL máximo → RPL,
leads/dia por faixa, retorno/dia, pacing realizado × esperado por coortes, top anúncios,
personas dos qualificados e benchmark entre campanhas.

Fontes (produção): cbo_lead_conversion_iql, cbo_campaign_rpl_estimate, dim_iql_cutoffs,
dtm_analytics_{facebook,google,pmax}_ads_funnel. Nenhum número hardcoded no index.html.

⚠️ Repo público: só agregados — nunca pesos/pontos do scorecard (D20) nem PII.

Uso: python3 refresh.py   (usa o bqq — ver wiki-bp/pages/bq-acesso.md)
"""
import csv
import datetime as dt
import json
import re
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "data.json"
QUERIES = BASE / "queries"
BQQ = Path.home() / "meu_projeto" / "BigQuery" / "bqq"

META_RETORNO = 1.5          # D32/D52
N_MIN_CRIATIVO = 50         # D16
TOP_ADS = 12
FAIXAS = ["A+", "A", "B", "C", "D"]

# Campanhas acompanhadas. dt_inicio protege tags reusadas (JOM existe desde out/2025).
# Períodos: wiki-brasil-paralelo/pages/campanhas-calendario.md.
CAMPANHAS = [
    {"tag": "ENE", "nome": "Enéas", "dt_inicio": "2026-07-27", "tipo": "aberto",
     "aquecimento": ["2026-07-27", "2026-08-23"], "venda": "2026-07-28",
     "nota": "Venda direta desde 28/07 — campanha [VENDA] roda junto com a captação."},
    {"tag": "EVG", "nome": "Brasil Evangélico", "dt_inicio": "2026-05-21",
     "aquecimento": ["2026-05-21", "2026-07-07"], "venda": "2026-07-08",
     "nota": "Primeira campanha com pesquisa in-funnel (cobertura ~69%)."},
    {"tag": "BP10", "nome": "BP 10 Anos", "dt_inicio": "2026-06-11",
     "aquecimento": ["2026-06-11", "2026-07-15"], "venda": "2026-07-16",
     "nota": "Oferta com combos/vitalício — receita concentrada em high-ticket; abertura dentro da janela infla o RPL vs projeção."},
    {"tag": "ELB26", "nome": "Entre Lobos 2026", "dt_inicio": "2026-07-14",
     "aquecimento": ["2026-07-14", "2026-07-31"], "venda": None,
     "nota": "Captação encerrada ~31/07; venda não abriu (produção no ar desde 29/07)."},
    {"tag": "JOM", "nome": "John Money", "dt_inicio": "2026-07-25",
     "aquecimento": ["2026-07-25", None], "venda": None,
     "nota": "Tag reusada desde out/2025 — leads e spend contados a partir de 25/07. "
             "Braços de teste (form nativo etc.) no relatório testes-jom."},
]

# Benchmark: tags sempre-ativas/LP têm spend espalhado por meses e CPL sem sentido.
BENCH_MAX_DIAS_SPEND = 75


def bq(sql_file, **params):
    """Roda um .sql pelo bqq (substituindo DECLAREs) e devolve list[dict]."""
    sql = sql_file.read_text()
    for k, v in params.items():
        sql, n = re.subn(rf"(DECLARE {k} \w+ DEFAULT )'[^']*'", rf"\g<1>'{v}'", sql)
        if n != 1:
            raise RuntimeError(f"{sql_file.name}: parâmetro {k} não encontrado")
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
        f.write(sql)
        sql_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        destino = tmp.name
    r = subprocess.run([str(BQQ), sql_path, "-o", destino], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"bqq falhou em {sql_file.name}: {r.stderr.strip()[-400:]}")
    with open(destino, newline="") as f:
        return list(csv.DictReader(f))


def num(v, default=None):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return default
    return default if x != x else x  # NaN


def integer(v):
    return int(num(v, 0) or 0)


def r2(x):
    return None if x is None else round(x, 2)


def daterange(a, b):
    d = dt.date.fromisoformat(a)
    fim = dt.date.fromisoformat(b)
    while d <= fim:
        yield d
        d += dt.timedelta(days=1)


def pacing(serie, realizado, curva, dt_inicio, dt_fim):
    """Esperado(t) = Σ coortes leads_d × curva(t−d); realizado acumulado por dia de compra."""
    leads_por_dia = {r["dt"]: r["qt_leads"] for r in serie}
    real_acum = {r["dt"]: num(r["vl_receita_acum"], 0) for r in realizado}
    cm = [num(c["rpl_cum_mediana"], 0) for c in curva]
    clo = [num(c["rpl_cum_min"], 0) for c in curva]
    chi = [num(c["rpl_cum_max"], 0) for c in curva]
    cap = len(cm) - 1
    dias = list(daterange(dt_inicio, dt_fim))
    out, ultimo_real = [], 0.0
    for t in dias:
        esp = lo = hi = 0.0
        for d in dias:
            if d > t:
                break
            n = leads_por_dia.get(d.isoformat(), 0)
            if not n:
                continue
            idade = min((t - d).days, cap)
            esp += n * cm[idade]
            lo += n * clo[idade]
            hi += n * chi[idade]
        ultimo_real = real_acum.get(t.isoformat(), ultimo_real)
        out.append({"dt": t.isoformat(), "esperado": r2(esp), "esperado_lo": r2(lo),
                    "esperado_hi": r2(hi), "realizado": r2(ultimo_real)})
    return out


def main():
    print("faixas...", flush=True)
    faixas = [{"faixa": r["nm_band"], "ev": num(r["vl_reference_ev"]), "versao": r["cd_version"]}
              for r in bq(QUERIES / "faixas.sql")]
    print("curva de referência (coortes)...", flush=True)
    curva = bq(QUERIES / "curva_referencia.sql")
    print("benchmark...", flush=True)
    bench_raw = bq(QUERIES / "benchmark.sql")

    hoje = dt.date.today()
    campanhas = []
    for c in CAMPANHAS:
        tag, ini = c["tag"], c["dt_inicio"]
        print(f"[{tag}] resumo / série / ads / pacing / personas...", flush=True)
        res = bq(QUERIES / "resumo_campanha.sql", tag=tag, dt_inicio=ini)[0]
        serie_raw = bq(QUERIES / "serie_diaria.sql", tag=tag, dt_inicio=ini)
        ads_raw = bq(QUERIES / "ads.sql", tag=tag, dt_inicio=ini)
        real_raw = bq(QUERIES / "pacing_realizado.sql", tag=tag, dt_inicio=ini)
        pers_raw = bq(QUERIES / "personas.sql", tag=tag, dt_inicio=ini)

        leads = integer(res["qt_leads"])
        spend = num(res["vl_spend"])
        cpl = num(res["vl_cpl"])
        rpl = num(res["vl_rpl_projected"])
        retorno = r2(rpl / cpl) if (rpl and cpl) else None
        # leitura comparável (só respondentes aplicado a todos) — piso/teto (iql.md)
        ev_resp = num(res["vl_ev_capi_resp"])
        retorno_teto = r2(ev_resp / cpl) if (ev_resp and cpl) else None
        receita = num(res["vl_receita_obs"], 0)

        serie = []
        for r in serie_raw:
            mix = {f: integer(r[k]) for f, k in zip(FAIXAS, ["qt_a_plus", "qt_a", "qt_b", "qt_c", "qt_d"])}
            n = integer(r["qt_leads"])
            serie.append({"dt": r["dt"], "qt_leads": n, "mix": mix,
                          "pc_qual": r2(100 * (mix["A+"] + mix["A"]) / n) if n else None,
                          "pc_survey": r2(100 * integer(r["qt_resp"]) / n) if n else None,
                          "vl_spend": num(r["vl_spend"]), "vl_cpl": num(r["vl_cpl"]),
                          "vl_ev_capi": num(r["vl_ev_capi"]), "vl_retorno_esp": num(r["vl_retorno_esp"])})

        ads = []
        for a in ads_raw:
            n = integer(a["qt_leads"])
            mix = {f: integer(a[k]) for f, k in zip(FAIXAS, ["qt_a_plus", "qt_a", "qt_b", "qt_c", "qt_d"])}
            ads.append({"id": a["id_ad"], "nome": a["nm_ad"], "adset": a["nm_adset"],
                        "vl_spend": num(a["vl_spend"]), "qt_leads": n, "vl_cpl": num(a["vl_cpl"]),
                        "mix_pct": {f: r2(100 * v / n) for f, v in mix.items()},
                        "pc_qual": r2(100 * (mix["A+"] + mix["A"]) / n),
                        "vl_score": num(a["vl_score"]), "vl_ev_capi": num(a["vl_ev_capi"]),
                        "pc_survey": num(a["pc_survey"]), "vl_retorno_esp": num(a["vl_retorno_esp"]),
                        "qt_compradores": integer(a["qt_compradores"]),
                        "vl_receita_obs": num(a["vl_receita_obs"], 0),
                        "bl_amostra_ok": n >= N_MIN_CRIATIVO})

        dt_fim = max([r["dt"] for r in serie] + [hoje.isoformat()])
        pace = pacing(serie, real_raw, curva, ini, dt_fim)
        # a curva esperada é PRÉ-ABERTURA: depois que a venda abre, o realizado descola
        # por desenho. O veredito do pacing é lido no último dia antes da abertura.
        # lançamento "aberto" (venda direta desde o dia 1) não tem corte: a curva vale inteira.
        venda = None if c.get("tipo") == "aberto" else c["venda"]
        corte = [x for x in pace if not venda or x["dt"] < venda]
        pace_ref = corte[-1] if corte else pace[-1]
        pacing_info = {"dt_corte": pace_ref["dt"], "na_abertura": bool(venda and venda <= dt_fim),
                       "esperado": pace_ref["esperado"], "esperado_lo": pace_ref["esperado_lo"],
                       "esperado_hi": pace_ref["esperado_hi"], "realizado": pace_ref["realizado"]}

        campanhas.append({
            **{k: c[k] for k in ("tag", "nome", "dt_inicio", "aquecimento", "venda", "nota")},
            "tipo": c.get("tipo", "fechado"),
            "resumo": {
                "qt_leads": leads, "vl_spend": spend, "vl_cpl": cpl,
                "dt_spend_ini": res["dt_spend_ini"] or None, "dt_spend_fim": res["dt_spend_fim"] or None,
                "pc_qual": num(res["pc_qual"]), "qt_qual": integer(res["qt_qual"]),
                "vl_score": num(res["vl_score"]), "vl_ev_capi": num(res["vl_ev_capi"]),
                "pc_survey": num(res["pc_survey"]), "qt_resp": integer(res["qt_resp"]),
                "pc_qual_resp": num(res["pc_qual_resp"]), "vl_ev_capi_resp": ev_resp,
                "vl_receita_obs": receita, "qt_vendas": integer(res["qt_vendas"]),
                "qt_compradores": integer(res["qt_compradores"]),
                "roas_realizado": r2(receita / spend) if spend else None,
                "rpl_projetado": rpl, "rpl_lo": num(res["vl_rpl_projected_lo"]),
                "rpl_hi": num(res["vl_rpl_projected_hi"]), "estimador": res["nm_estimator"] or None,
                "pc_erro": num(res["pc_error_estimated"]),
                "bl_ancorado": (res["bl_capi_value_eligible"] or "").lower() == "true",
                "retorno_esperado": retorno, "retorno_teto": retorno_teto,
                "cpl_max": r2(rpl / META_RETORNO) if rpl else None,
                "vl_projetado_total": r2(rpl * leads) if rpl else None,
                "dt_referencia": res["dt_reference"] or None,
            },
            "serie": serie,
            "ads": ads[:TOP_ADS],
            "qt_ads_total": len(ads),
            "pacing": pace,
            "pacing_ref": pacing_info,
            "personas": [{"persona": p["persona"], "qt_leads": integer(p["qt_leads"]),
                          "pc_qual": num(p["pc_qual"]), "qt_compradores": integer(p["qt_compradores"]),
                          "pc_conv": num(p["pc_conv"]), "vl_receita": num(p["vl_receita"], 0)}
                         for p in pers_raw],
        })

    bench = []
    for b in bench_raw:
        try:
            dias = (dt.date.fromisoformat(b["dt_spend_fim"]) - dt.date.fromisoformat(b["dt_spend_ini"])).days
        except ValueError:
            dias = None
        if dias is not None and dias > BENCH_MAX_DIAS_SPEND:
            continue  # sempre-ativa / tag reusada — CPL blendado não é comparável
        bench.append({"tag": b["nm_tag"], "qt_leads": integer(b["qt_leads"]), "pc_qual": num(b["pc_qual"]),
                      "pc_survey": num(b["pc_survey"]), "vl_spend": num(b["vl_spend"]), "vl_cpl": num(b["vl_cpl"]),
                      "estimador": b["nm_estimator"] or None, "rpl_projetado": num(b["vl_rpl_projected"]),
                      "retorno_proj": num(b["vl_retorno_proj"]), "dias_spend": dias})

    data = {
        "gerado_em": dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "meta_retorno": META_RETORNO,
        "n_min_criativo": N_MIN_CRIATIVO,
        "faixas": faixas,
        "curva_referencia": {"tags": curva[0]["tags"] if curva else "", "horizonte_dias": len(curva) - 1,
                             "rpl_cum_mediana": [num(c["rpl_cum_mediana"]) for c in curva]},
        "campanhas": campanhas,
        "benchmark": bench,
    }

    # governança D20: nada de pesos/WOE/pontos por nível no repo público
    blob = json.dumps(data, ensure_ascii=False).lower()
    for proibido in ("woe", "qt_points_level", "beta", "iv_contrib"):
        assert proibido not in blob, f"governança: chave proibida no data.json: {proibido}"

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    for c in campanhas:
        r = c["resumo"]
        print(f"{c['tag']}: {r['qt_leads']} leads · CPL {r['vl_cpl']} · RPL proj {r['rpl_projetado']} · "
              f"retorno {r['retorno_esperado']}× (teto {r['retorno_teto']}×) · realizado R$ {r['vl_receita_obs']:.0f}")
    print(f"ok → {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
