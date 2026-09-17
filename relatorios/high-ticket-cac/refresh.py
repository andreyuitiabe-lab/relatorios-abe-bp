#!/usr/bin/env python3
"""Gera data.json do relatório high-ticket (CAC e saturação).

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Fontes:
  - queries/*.sql            -> BigQuery (via bqq, nunca `bq query`: a credencial do bq CLI
                                expira ~diariamente e falha em sessão não-interativa)
  - bp-staging.dbt_abe.tb_ht_meta_spend -> spend Meta desde ago/2023, carregado por
                                scripts/carrega_meta_bq.py a partir da Marketing API.
                                Rodar `python scripts/extrai_meta_api.py` + o carregador
                                antes deste script quando quiser atualizar a mídia.
  - MIDIA_PLANILHA           -> a Travessia de 2023 é anterior ao alcance da API (37 meses);
                                o custo dela vem da planilha do time de tráfego e está
                                fixado aqui de propósito, com a fonte marcada no data.json.
"""

import datetime
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
OUT = AQUI / "data.json"

# Travessia 2023: captação 178.970,39 + nutrição 35.845,38 + venda 655.000,00.
# Planilha oficial do time de tráfego (aba matriz, coluna TRA-2023), registrada em
# wiki-brasil-paralelo/campanhas-contexto.md. Ela confirma o faturamento medido aqui
# (planilha R$ 8,10 mi vs warehouse R$ 8,01 mi, 1,2%), o que dá confiança no custo.
MIDIA_PLANILHA = {"TRA": 869_815.77}


def bqq(sql_path: Path) -> pd.DataFrame:
    """Roda um .sql pelo bqq e devolve DataFrame."""
    destino = AQUI / "dados" / f"{sql_path.stem}.csv"
    destino.parent.mkdir(exist_ok=True)
    r = subprocess.run(["bqq", str(sql_path), "-o", str(destino)],
                       capture_output=True, text=True, cwd=AQUI)
    if r.returncode != 0:
        raise RuntimeError(f"{sql_path.name}: {r.stderr.strip()[:400]}")
    return pd.read_csv(destino)


def bqq_inline(sql: str) -> pd.DataFrame:
    tmp = AQUI / "dados" / "_tmp.sql"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(sql)
    try:
        return bqq(tmp)
    finally:
        tmp.unlink(missing_ok=True)


def nn(v):
    """NaN/NaT -> None, para o JSON não virar 'NaN' (que quebra o fetch)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (pd.Timestamp, datetime.date)):
        return str(v)
    return v.item() if hasattr(v, "item") else v


Q_SERIE_ANUAL = """
WITH ht AS (
  SELECT EXTRACT(YEAR FROM dt_ordered_at) AS ano,
         SUM(IF(vl_payment_gross > 1000, vl_payment_gross, 0)) AS vl_ht,
         COUNT(DISTINCT IF(vl_payment_gross > 1000, id_gateway_customer, NULL)) AS qt_compradores
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved' AND bl_is_renovation = FALSE AND dt_ordered_at >= '2022-01-01'
  GROUP BY 1
),
base AS (
  SELECT EXTRACT(YEAR FROM dt_dates) AS ano, AVG(qt_paying_active_members) AS qt_base
  FROM `bp-datawarehouse.datamart.cbo_daily_members` GROUP BY 1
)
SELECT ano, ROUND(vl_ht) AS vl_ht, qt_compradores, ROUND(qt_base) AS qt_base,
       ROUND(vl_ht / qt_base, 2) AS vl_ht_por_membro
FROM ht JOIN base USING (ano) ORDER BY ano
"""

Q_REINCIDENCIA = """
WITH c AS (
  SELECT sigla, ord, id_comprador, vl_receita
  FROM `bp-staging.dbt_abe.tb_ht_compradores` WHERE bl_universo_principal
)
SELECT a.ord, a.sigla,
  COUNT(DISTINCT a.id_comprador) AS qt_compradores,
  ROUND(100 * COUNT(DISTINCT IF(b.id_comprador IS NOT NULL, a.id_comprador, NULL))
        / COUNT(DISTINCT a.id_comprador), 1) AS pct_reincidente
FROM c AS a
LEFT JOIN (SELECT DISTINCT id_comprador, ord FROM c) AS b
  ON b.id_comprador = a.id_comprador AND b.ord < a.ord
GROUP BY 1, 2 ORDER BY a.ord
"""

Q_BNO_MIX = """
SELECT sigla,
  IF(REGEXP_CONTAINS(LOWER(nm_plano_principal), r'vital'), 'Vitalício', 'Assinatura/outros') AS nm_tipo,
  COUNT(*) AS qt, ROUND(SUM(vl_receita)) AS vl
FROM `bp-staging.dbt_abe.tb_ht_compradores`
WHERE bl_universo_principal AND sigla IN ('BNO24', 'BNO25', 'BP10')
GROUP BY 1, 2 ORDER BY 1, 2
"""


def build() -> dict:
    print("  consolidado por campanha...", flush=True)
    cons = bqq(AQUI / "queries" / "06_consolidado.sql")
    cons["nm_fonte_midia"] = "api_meta+warehouse"
    for sigla, valor in MIDIA_PLANILHA.items():
        m = cons["sigla"] == sigla
        cons.loc[m, "vl_midia"] = valor
        cons.loc[m, "nm_fonte_midia"] = "planilha_trafego"
        cons.loc[m, "vl_cac"] = round(valor / cons.loc[m, "qt_compradores"].iloc[0], 2)
        cons.loc[m, "vl_roas"] = round(cons.loc[m, "vl_receita"].iloc[0] / valor, 2)
        # CAC do canal mídia = verba ÷ compradores que chegaram por mídia
        comp_midia = cons.loc[m, "qt_compradores"].iloc[0] * cons.loc[m, "pct_comp_midia"].iloc[0] / 100
        cons.loc[m, "vl_cac_canal_midia"] = round(valor / comp_midia, 2)

    print("  série anual de high-ticket...", flush=True)
    anual = bqq_inline(Q_SERIE_ANUAL)
    print("  reincidência entre campanhas...", flush=True)
    reinc = bqq_inline(Q_REINCIDENCIA)
    print("  mix de produto das promoções...", flush=True)
    mix = bqq_inline(Q_BNO_MIX)

    campanhas = [{k: nn(v) for k, v in linha.items()} for linha in cons.to_dict("records")]
    for c, r in zip(campanhas, reinc.to_dict("records")):
        c["pct_reincidente"] = nn(r["pct_reincidente"])

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "campanhas": campanhas,
        "anual": [{k: nn(v) for k, v in l.items()} for l in anual.to_dict("records")],
        "mix_promocao": [{k: nn(v) for k, v in l.items()} for l in mix.to_dict("records")],
    }


if __name__ == "__main__":
    print("Refreshing high-ticket-cac report data from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']} — {len(data['campanhas'])} campanhas")
        if "--push" in sys.argv:
            subprocess.run(["git", "add", str(OUT)], check=True, cwd=AQUI)
            subprocess.run(["git", "commit", "-m",
                            f"data: high-ticket-cac refresh {datetime.date.today()}"],
                           check=True, cwd=AQUI)
            subprocess.run(["git", "push", "origin", "main"], check=True, cwd=AQUI)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
