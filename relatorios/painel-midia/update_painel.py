#!/usr/bin/env python3
"""
Painel de Mídia — atualizador diário (2026-09-10)
Roda o recomendador (dados D-2), calcula o bloco estratégico (I*, ROAS marginal),
lê o status do MMM v32 e escreve data.json + decision log.

Uso:  python3 update_painel.py            # atualiza data.json e decisoes.csv
Agendamento: LaunchAgent com.bp.painel-midia (ver RUNBOOK.md).
Publicação: manual (git push) ou PAINEL_PUSH=1 no ambiente do agent.
"""
import importlib.util
import json
import os
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
MIDIA = HERE.parent / "midia-paga"
MMMP = Path.home() / "meu_projeto" / "mmm_project"

# parâmetros revisados 10/09 (ver midia-paga/ANALISE.md)
B, HL_ISTAR, MARGEM = 0.70, 7, 0.75

spec = importlib.util.spec_from_file_location("rec", MIDIA / "scripts" / "recomendador_v1.py")
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)

asof = pd.Timestamp(date.today() - timedelta(days=2))
dt_ini = (asof - pd.Timedelta(days=200)).date().isoformat()
df = rec.carregar(dt_ini, asof.date().isoformat())
di_serie = rec.demand_index(dt_ini, asof.date().isoformat())
di = float(di_serie.iloc[-1])

# ── recomendações do dia ──────────────────────────────────────────────────────
recs = []
for camp, g in df.groupby("camp"):
    if g["d"].max() < asof - pd.Timedelta(days=5):
        continue
    s = rec.sinais_do_dia(g, asof, di)
    if s:
        recs.append({"campanha": camp, "acao": s["acao"], "motivo": s["motivo"],
                     "spend_dia": round(s["spend_3d_med"]), "cpa3": None if not np.isfinite(s["cpa3"]) else round(s["cpa3"]),
                     "roas3": round(s["roas3"], 2), "teto": round(s["teto"]), "tipo": s["tipo"]})
ordem = {"REDUZIR": 0, "ALERTA": 1, "AUMENTAR": 2, "MANTER": 3, "SEM REC.": 4}
recs.sort(key=lambda r: (ordem.get(r["acao"], 9), -r["spend_dia"]))

# ── bloco estratégico (β EWMA-7, I*) ─────────────────────────────────────────
p = df.groupby("d")[["spend", "receita"]].sum()
p = p[p["spend"] > 5000]
beta_s = (p["receita"] / p["spend"] ** B)
beta = float(beta_s.ewm(halflife=HL_ISTAR).mean().iloc[-1])
b21 = beta_s.tail(21)
spend_ma7 = float(p["spend"].tail(7).mean())
mroas = B * beta * spend_ma7 ** (B - 1)
istar = lambda bb, m: float((B * bb * m) ** (1 / (1 - B)))
estrategico = {
    "spend_ma7": round(spend_ma7), "roas_marginal": round(mroas, 2),
    "breakeven_margem": round(1 / MARGEM, 2),
    "istar_margem": round(istar(beta, MARGEM)),
    "istar_margem_lo": round(istar(float(b21.quantile(.25)), MARGEM)),
    "istar_margem_hi": round(istar(float(b21.quantile(.75)), MARGEM)),
    "teto_receita": round(istar(beta, 1.0)), "margem_usada": MARGEM,
}

# ── status do MMM v32 (calibração mais recente disponível) ───────────────────
v32 = {}
for d32, versao in [(MMMP / "output" / "mmm_v32_2b", "v32.2b"), (MMMP / "output" / "mmm_v32_log", "v32.1")]:
    f = d32 / "summary_oos_2026.csv"
    if f.exists():
        s32 = pd.read_csv(f)
        row = s32.iloc[0]
        v32 = {"versao": versao, "r2_oos": round(float(row["r2"]), 2),
               "mape": round(float(row["mape"]) * 100), "bias": round(float(row["bias_pct"]), 1),
               "calibrado_em": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")}
        break

# ── decision log ──────────────────────────────────────────────────────────────
log_f = HERE / "decisoes.csv"
cols = ["data", "campanha", "acao_recomendada", "spend_dia", "acao_tomada", "resultado"]
log = pd.read_csv(log_f) if log_f.exists() else pd.DataFrame(columns=cols)
hoje = asof.date().isoformat()
if not (log["data"] == hoje).any() if len(log) else True:
    novas = pd.DataFrame([{"data": hoje, "campanha": r["campanha"], "acao_recomendada": r["acao"],
                           "spend_dia": r["spend_dia"], "acao_tomada": "", "resultado": ""}
                          for r in recs if r["acao"] in ("REDUZIR", "AUMENTAR", "ALERTA")])
    log = pd.concat([log, novas], ignore_index=True)
    log.to_csv(log_f, index=False)

data = {
    "atualizado_em": datetime.now().isoformat(timespec="seconds"),
    "asof": asof.date().isoformat(), "demand_index": round(di, 2),
    "estrategico": estrategico, "v32": v32, "recomendacoes": recs,
    "decisoes_recentes": log.tail(25).to_dict(orient="records"),
    "params": {"b": B, "hl_beta": HL_ISTAR, "margem": MARGEM,
               "nota_margem": "margem 0,75 = cenário digital central (MARGEM.md); pendente financeiro"},
}
(HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
print(f"✓ data.json atualizado — asof {hoje} | {len(recs)} campanhas | "
      f"spend R${spend_ma7:,.0f}/d vs I* R${estrategico['istar_margem']:,.0f}")

if os.environ.get("PAINEL_PUSH") == "1":
    repo = HERE.parent.parent
    subprocess.run(["git", "-C", str(repo), "add", str(HERE)], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m",
                    f"painel-midia: atualização automática {hoje}"], check=False)
    subprocess.run(["git", "-C", str(repo), "push"], check=True)
    print("✓ publicado (push)")
