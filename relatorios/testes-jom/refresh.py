#!/usr/bin/env python3
"""
Relatório: Testes de campanha JOM — CPL × qualidade × retorno esperado por braço.

Acompanha os testes de estratégia de campanha da JOM (Advantage, form nativo Meta e,
quando a ponte CAPI estiver no ar, os braços otimizados por IQL/RPL). Cada braço de
teste = uma campanha Meta (ou a tag, no caso do form nativo, cujo utm_content não
carrega id de anúncio).

Lê os modelos em produção (fct_lead_iql, dtm_analytics_lead_conversion,
dtm_analytics_facebook_ads_funnel), agrega server-side e escreve data.json.
Nenhum número hardcoded no index.html.

⚠️ Repo público: só agregados por braço/faixa — nunca pesos do scorecard (D20) nem PII.

Uso: python3 refresh.py   (usa o bqq — ver wiki-bp/pages/bq-acesso.md)
"""
import csv
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "data.json"
QUERIES = BASE / "queries"

# Cliente padrão do projeto (wiki-bp/pages/bq-acesso.md): usa Application Default
# Credentials, que renovam sozinhas — a credencial do `bq` CLI expira ~diariamente e
# não reautentica em sessão não-interativa.
BQQ = Path.home() / "meu_projeto" / "BigQuery" / "bqq"

ORD_FAIXA = ["A+", "A", "B", "C", "D"]


def bq(sql_file):
    """Roda um .sql pelo bqq e devolve list[dict] (via CSV completo)."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        destino = tmp.name
    r = subprocess.run([str(BQQ), str(sql_file), "-o", destino],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"bqq falhou em {sql_file.name}: {r.stderr.strip()[-300:]}")
    with open(destino, newline="") as f:
        return list(csv.DictReader(f))


def num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def main():
    print("resumo por braço...", flush=True)
    resumo = bq(QUERIES / "resumo_bracos.sql")
    print("série diária...", flush=True)
    serie = bq(QUERIES / "serie_diaria.sql")
    print("mix de faixas...", flush=True)
    mix_raw = bq(QUERIES / "mix_faixas.sql")

    # ── braços: normaliza tipos e deriva o que a página precisa ────────────────
    bracos = []
    for r in resumo:
        leads = int(num(r["qt_leads"]))
        spend = num(r.get("vl_spend")) or None
        bracos.append({
            "arm": r["nm_arm"],
            "pago": spend is not None,
            "leads": leads,
            "spend": spend,
            "cpl": num(r.get("vl_cpl")) or None,
            "pc_qual": num(r.get("pc_qual")),
            "score": num(r.get("vl_score")),
            "ev": num(r.get("vl_ev")),
            "pc_survey": num(r.get("pc_survey")),
            "qt_resp": int(num(r.get("qt_resp"))),
            "pc_qual_resp": num(r.get("pc_qual_resp")) or None,
            "score_resp": num(r.get("vl_score_resp")) if r.get("vl_score_resp") else None,
            "ev_resp": num(r.get("vl_ev_resp")) or None,
            "retorno_esp": num(r.get("vl_retorno_esp")) or None,
            "retorno_ajust": num(r.get("vl_retorno_ajust")) or None,
            "receita_obs": num(r.get("vl_receita_obs")),
            "vendas": int(num(r.get("qt_vendas"))),
            "dt_ini": r.get("dt_ini"),
            "dt_fim": r.get("dt_fim"),
            # dias rodando: base para separar aprendizado (2 sem) de regime estável
            "dias": ((datetime.date.fromisoformat(r["dt_fim"]) -
                      datetime.date.fromisoformat(r["dt_ini"])).days + 1)
                    if r.get("dt_ini") and r.get("dt_fim") else None,
        })
    bracos.sort(key=lambda b: (-(b["leads"] or 0)))

    # ── mix de faixas por braço (share dentro do braço) ───────────────────────
    mix = {}
    for r in mix_raw:
        mix.setdefault(r["nm_arm"], {})[r["nm_iql_band"]] = int(num(r["qt_leads"]))
    mix_out = {}
    for arm, faixas in mix.items():
        total = sum(faixas.values()) or 1
        mix_out[arm] = [round(100 * faixas.get(f, 0) / total, 1) for f in ORD_FAIXA]

    # ── série diária ──────────────────────────────────────────────────────────
    serie_out = [{
        "dt": r["dt_label"],
        "arm": r["nm_arm"],
        "leads": int(num(r["qt_leads"])),
        "cpl": num(r.get("vl_cpl")) or None,
        "pc_qual": num(r.get("pc_qual")),
        "retorno_esp": num(r.get("vl_retorno_esp")) or None,
        "pc_survey": num(r.get("pc_survey")),
    } for r in serie]

    pagos = [b for b in bracos if b["pago"]]
    total_leads = sum(b["leads"] for b in bracos)
    total_spend = sum(b["spend"] or 0 for b in pagos)
    total_ev = sum((b["ev"] or 0) * b["leads"] for b in pagos)

    data = {
        "gerado_em": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "faixas": ORD_FAIXA,
        "meta_retorno": 1.5,          # meta oficial de retorno (D32)
        "dias_aprendizado": 14,       # janela de aprendizado do Meta (lição Lead Survey)
        "kpis": {
            "leads": total_leads,
            "spend": round(total_spend, 2),
            "cpl": round(total_spend / sum(b["leads"] for b in pagos), 2) if pagos else None,
            "retorno_esp": round(total_ev / total_spend, 2) if total_spend else None,
            "bracos_pagos": len(pagos),
            "receita_obs": round(sum(b["receita_obs"] for b in bracos), 0),
            "vendas": sum(b["vendas"] for b in bracos),
        },
        "bracos": bracos,
        "mix": mix_out,
        "serie": serie_out,
    }

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"✓ {OUT} — {len(bracos)} braços, {total_leads} leads, "
          f"R$ {total_spend:,.0f} de investimento", flush=True)


if __name__ == "__main__":
    main()
