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

# janela do briefing (usada na visão LP x form por mercado)
JANELA_INI, JANELA_FIM = "2026-08-12", "2026-08-23"


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
    print("LP x form por mercado...", flush=True)
    lpform = bq(QUERIES / "lp_vs_form_mercado.sql")

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

    # ── segunda visão: LP x form nativo por mercado (formato do briefing) ──────
    def n_or_none(v):
        f = num(v, None) if v not in (None, "", "NaN") else None
        return f
    # Mídia dos EUA: a conta [BIG] não está no BQ — vem de midia_eua.csv, exportado da
    # planilha "[NOVO] Meta Ads - Big Picture" do time de tráfego. Valores em USD.
    # Atualizar: reexportar a planilha em CSV e regravar o arquivo (ver ANALISE.md).
    # Corte por mercado (início da janela comparável) vem da própria query: a data do 1º lead
    # do form nativo. A mídia dos EUA (CSV) é recortada pelo corte do EUA para casar com a LP.
    corte = {r["nm_mercado"]: r["dt_corte"] for r in lpform if r.get("dt_corte")}
    corte_eua = corte.get("EUA", JANELA_INI)

    eua = {}
    csv_eua = BASE / "midia_eua.csv"
    if csv_eua.exists():
        with open(csv_eua, newline="") as fh:
            for row in csv.DictReader(fh):
                if not (corte_eua <= row["dt"] <= JANELA_FIM):
                    continue
                acc = eua.setdefault(row["nm_tipo"], {"spend": 0.0, "impr": 0.0, "cliques": 0.0, "dias": set()})
                acc["spend"] += num(row["vl_spend_usd"])
                acc["impr"] += num(row["qt_impressoes"])
                acc["cliques"] += num(row["qt_cliques"])
                acc["dias"].add(row["dt"])

    celulas = [{
        "mercado": r["nm_mercado"],
        "tipo": r["nm_tipo"],
        "dt_corte": r.get("dt_corte"),
        "leads": int(num(r["qt_leads"])),
        "spend": n_or_none(r.get("vl_spend")),
        "impressoes": n_or_none(r.get("qt_impressoes")),
        "cpm": n_or_none(r.get("vl_cpm")),
        "ctr": n_or_none(r.get("pc_ctr")),
        "cpl": n_or_none(r.get("vl_cpl")),
        "email_entregue": int(num(r.get("qt_email_entregue"))),
        "email_abertura": n_or_none(r.get("pc_email_abertura")),
        "email_clique": n_or_none(r.get("pc_email_clique")),
        "receita": num(r.get("vl_receita")),
        "vendas": int(num(r.get("qt_vendas"))),
        "retorno_lead": num(r.get("vl_retorno_por_lead")),
    } for r in lpform]

    for c in celulas:  # preenche EUA com a planilha (moeda USD, sinalizada na página)
        if c["mercado"] != "EUA" or c["spend"] is not None:
            continue
        a = eua.get(c["tipo"])
        if not a or not a["impr"]:
            continue
        c["spend"] = round(a["spend"], 2)
        c["impressoes"] = a["impr"]
        c["cpm"] = round(1000 * a["spend"] / a["impr"], 2)
        c["ctr"] = round(100 * a["cliques"] / a["impr"], 2)
        c["cpl"] = round(a["spend"] / c["leads"], 2) if c["leads"] else None
        c["moeda"] = "USD"
        c["dias_midia"] = len(a["dias"])
        c["fonte_midia"] = "planilha [NOVO] Meta Ads - Big Picture"

    # janela comparável: rótulo por mercado (corte → fim) e a janela geral do relatório
    def ddmm(iso):
        return f"{iso[8:10]}/{iso[5:7]}" if iso else None
    for c in celulas:
        c["periodo"] = f"{ddmm(c.get('dt_corte'))} a {ddmm(JANELA_FIM)}" if c.get("dt_corte") else None
    cortes = sorted(c["dt_corte"] for c in celulas if c.get("dt_corte"))
    janela_ini = f"{ddmm(cortes[0])}/2026" if cortes else "12/08/2026"

    (BASE / "lp-vs-form.json").write_text(json.dumps({
        "gerado_em": data["gerado_em"],
        "janela": {"ini": janela_ini, "fim": "23/08/2026",
                   "nota": "Janela comparável: recortada ao período em que LP e form nativo rodaram "
                           "juntos em cada mercado (do 1º lead do form até 23/08). O form começou em "
                           "20/08 — incluir 12–19/08 enviesaria a favor da LP (leads mais velhos têm "
                           "mais tempo para abrir e-mail e converter)."},
        "celulas": celulas,
        # lacunas conhecidas, exibidas na página em vez de célula vazia sem explicação
        "lacunas": {
            "midia_eua": "A conta de anúncios dos EUA ([BIG] / Big Picture Originals) não está no "
                         "BigQuery — verificado: 0 linhas. Gasto, impressões, CPM e CTR dos EUA vêm "
                         "de midia_eua.csv, exportado da planilha do time, e estão em DÓLAR. "
                         "Atualizar o CSV quando a planilha mudar.",
            "conversao_etapa": "LP (visita→lead) exige GA4 — domínios distintos por mercado "
                               "(form.brasilparalelo.com.br e bigpictureoriginals.com). Form "
                               "(abertura→envio) exige as métricas de formulário do Meta, que não "
                               "são exportadas para o BQ.",
            "ctr_form": "No form nativo o usuário não sai do Instagram/Facebook, então 'outbound "
                        "click' não mede a mesma coisa que na LP — os CTRs não são comparáveis.",
        },
    }, ensure_ascii=False, indent=1))
    print(f"✓ lp-vs-form.json — {len(celulas)} células (mercado x tipo)", flush=True)
    print(f"✓ {OUT} — {len(bracos)} braços, {total_leads} leads, "
          f"R$ {total_spend:,.0f} de investimento", flush=True)


if __name__ == "__main__":
    main()
