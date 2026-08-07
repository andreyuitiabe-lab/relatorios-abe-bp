#!/usr/bin/env python3
"""
Perfil de quem compra o Mecenas — gera data.json a partir do BigQuery.

Uso:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Depende da tabela `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`, recriada por
queries/00_base_qualificacao.sql. Rodar aquela query primeiro se a base mudar.

⚠️ Definição de doador Mecenas (ver queries/00_base_qualificacao.sql): exclui os DOIS
order bumps. O de R$180 ("Mecenas Order Bump") não tem "order bump" no nome da oferta —
só o corte vl_payment_gross >= 300 pega. Sem isso entram 2.726 pessoas que marcaram um
checkbox no checkout de assinatura barata e o perfil todo se contamina.
"""

import json, subprocess, sys, datetime, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
from google.cloud import bigquery

BASE = "bp-staging.dbt_abe.tb_mecenas_qualificacao_base"
QDIR = Path(__file__).parent / "queries"
OUT = Path(__file__).parent / "data.json"

_client = None


def bq(sql: str) -> list[dict]:
    """Executa query e devolve lista de dicts. Usa ADC (o bq CLI perde token com frequência)."""
    global _client
    if _client is None:
        _client = bigquery.Client(project="bp-datawarehouse")
    return [dict(r) for r in _client.query(sql).result()]


def bq_file(name: str) -> list[dict]:
    """Roda um .sql da pasta queries/ — o arquivo é a versão canônica."""
    return bq((QDIR / name).read_text())


def fi(v) -> float:
    try:
        return float(v) if v is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def ii(v) -> int:
    try:
        return int(v) if v is not None else 0
    except (TypeError, ValueError):
        return 0


# ─── queries ─────────────────────────────────────────────────────────────────

Q_RESUMO = f"""
SELECT
  COUNT(*)                                             AS universo,
  COUNTIF(bl_is_mecenas)                               AS doadores,
  100 * COUNTIF(bl_is_mecenas) / COUNT(*)              AS taxa_base,
  SUM(vl_total_mecenas)                                AS receita,
  COUNTIF(bl_is_mecenas AND vl_maior_tx_mecenas > 10000) AS n_topo,
  SUM(IF(vl_maior_tx_mecenas > 10000, vl_total_mecenas, 0)) AS receita_topo,
  COUNTIF(bl_membro_ativo = 1 AND NOT bl_is_mecenas)   AS membros_controle
FROM `{BASE}`
"""

Q_TIERS = f"""
SELECT
  CASE WHEN vl_maior_tx_mecenas > 10000 THEN 'Alto (acima de R$ 10 mil)'
       WHEN vl_maior_tx_mecenas >= 1188 THEN 'Bolsas (R$ 1.188 a R$ 10 mil)'
       ELSE 'Solidário (R$ 359 a R$ 1.188)' END AS tier,
  COUNT(*)                  AS pessoas,
  SUM(vl_total_mecenas)     AS receita,
  AVG(vl_total_mecenas)     AS por_pessoa
FROM `{BASE}`
WHERE bl_is_mecenas
GROUP BY 1
"""

# Perfil comparado: controle vs cada tier, em % — alimenta o gráfico de barras agrupadas
Q_PERFIL = f"""
SELECT
  CASE WHEN NOT bl_is_mecenas THEN 'Membro ativo'
       WHEN vl_maior_tx_mecenas > 10000 THEN 'Doador alto'
       ELSE 'Doador bolsas' END AS grupo,
  COUNT(*)                                                        AS pessoas,
  100 * AVG(IF(cd_income_decile >= 9, 1, 0))                      AS renda_top,
  100 * AVG(IF(nm_credit_card_level_max IN ('6_black','5_amex'), 1, 0)) AS cartao_top,
  100 * AVG(IF(pc_similaridade >= 0.95, 1, 0))                    AS socio,
  100 * AVG(IF(vl_capital_social >= 1000000, 1, 0))               AS capital_1m,
  100 * AVG(bl_vitalicio)                                         AS vitalicio,
  100 * AVG(bl_certificacao)                                      AS certificacao,
  100 * AVG(bl_cdl)                                               AS cdl,
  100 * AVG(IF(nm_gender_inferred = 'Feminino', 1, 0))            AS feminino,
  AVG(qt_idade)                                                   AS idade,
  AVG(qt_dias_casa) / 365                                         AS anos_casa,
  AVG(vl_total_outras)                                            AS gasto_previo
FROM `{BASE}`
WHERE bl_is_mecenas OR bl_membro_ativo = 1
GROUP BY 1
"""


def build() -> dict:
    print("  resumo...", flush=True)
    r = bq(Q_RESUMO)[0]

    print("  tiers...", flush=True)
    tiers = bq(Q_TIERS)

    print("  perfil comparado...", flush=True)
    perfil = bq(Q_PERFIL)

    print("  lift univariado...", flush=True)
    lift = bq_file("02_lift_univariado.sql")

    print("  cnpj: capital e setor...", flush=True)
    cnpj = bq_file("09_cnpj_capital_setor.sql")

    print("  safras...", flush=True)
    safras = bq_file("07_perfil_por_safra.sql")

    print("  segmentos...", flush=True)
    seg = bq_file("06_segmentos_bolsoes.sql")

    ordem = {"Membro ativo": 0, "Doador bolsas": 1, "Doador alto": 2}

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "resumo": {
            "universo": ii(r["universo"]),
            "doadores": ii(r["doadores"]),
            "taxa_base": fi(r["taxa_base"]),
            "receita": fi(r["receita"]),
            "n_topo": ii(r["n_topo"]),
            "receita_topo": fi(r["receita_topo"]),
            "pc_receita_topo": 100 * fi(r["receita_topo"]) / fi(r["receita"]),
            "membros_controle": ii(r["membros_controle"]),
        },
        "tiers": sorted(
            [
                {
                    "tier": t["tier"],
                    "pessoas": ii(t["pessoas"]),
                    "receita": fi(t["receita"]),
                    "por_pessoa": fi(t["por_pessoa"]),
                }
                for t in tiers
            ],
            key=lambda x: x["receita"],
        ),
        "perfil": sorted(
            [
                {
                    "grupo": p["grupo"],
                    "pessoas": ii(p["pessoas"]),
                    "renda_top": fi(p["renda_top"]),
                    "cartao_top": fi(p["cartao_top"]),
                    "socio": fi(p["socio"]),
                    "capital_1m": fi(p["capital_1m"]),
                    "vitalicio": fi(p["vitalicio"]),
                    "certificacao": fi(p["certificacao"]),
                    "cdl": fi(p["cdl"]),
                    "feminino": fi(p["feminino"]),
                    "idade": fi(p["idade"]),
                    "anos_casa": fi(p["anos_casa"]),
                    "gasto_previo": fi(p["gasto_previo"]),
                }
                for p in perfil
            ],
            key=lambda x: ordem.get(x["grupo"], 9),
        ),
        "lift": [
            {
                "dim": l["dim"],
                "val": l["val"],
                "pessoas": ii(l["pessoas"]),
                "mecenas": ii(l["mecenas"]),
                "conv": fi(l["pc_conv"]),
                "lift": fi(l["lift"]),
            }
            for l in lift
        ],
        "cnpj": [
            {
                "dim": c["dim"],
                "val": c["valor"],
                "pessoas": ii(c["pessoas"]),
                "mecenas": ii(c["mecenas"]),
                "conv": fi(c["pc_conv"]),
                "lift": fi(c["lift"]),
                "ticket": fi(c["ticket"]),
            }
            for c in cnpj
        ],
        "safras": [
            {
                "safra": s["safra"],
                "pessoas": ii(s["pessoas"]),
                "ticket": fi(s["ticket_medio"]),
                "comercial": fi(s["pc_comercial"]),
                "renda_top": fi(s["pc_decil9mais"]),
                "cartao_top": fi(s["pc_black_amex"]),
                "capital_1m": fi(s["pc_cap1m"]),
                "vitalicio": fi(s["pc_vitalicio"]),
                "gasto_previo": fi(s["gasto_previo_medio"]),
            }
            for s in safras
        ],
        "segmentos": [
            {
                "segmento": g["segmento"],
                "bolsao": ii(g["bolsao_abordavel"]),
                "bolsao_ativo": ii(g["bolsao_membro_ativo"]),
                "convertido": fi(g["pc_ja_convertido"]),
                "lift": fi(g["lift_vs_base"]),
                "ticket": fi(g["ticket_medio_esperado"]),
            }
            for g in seg
        ],
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    print("Refreshing perfil Mecenas from BigQuery...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        print(f"  {data['resumo']['doadores']:,} doadores · "
              f"R$ {data['resumo']['receita']/1e6:.1f}M · "
              f"taxa base {data['resumo']['taxa_base']:.3f}%")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m",
                            f"data: perfil mecenas refresh {datetime.date.today()}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
