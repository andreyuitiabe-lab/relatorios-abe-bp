#!/usr/bin/env python3
"""
Perfil de quem compra o Mecenas — gera data.json a partir do BigQuery.

Uso:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Depende da tabela `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`, recriada por
queries/00_base_qualificacao.sql. Rodar aquela query primeiro se a base mudar.

⚠️ TRÊS populações separadas (ver queries/00_base_qualificacao.sql), nunca somar:
  bolsa      = doador clássico, patrocínio de bolsa (>= R$ 1.000). Base do perfil.
  solidário  = campanha atual (jul/2026+), recorrente de ~R$ 30/mês sem teto.
  order bump = R$ 180 no checkout de outro produto. Não é doador.
O Solidário é identificado por PRODUTO, nunca por valor: a oferta de R$ 1.078,80 passa
de R$ 1.000 e cairia em "bolsa" por engano.
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
       WHEN vl_maior_tx_mecenas >= 2000 THEN 'Múltiplas bolsas (R$ 2 a 10 mil)'
       ELSE 'Bolsa única (R$ 1 a 2 mil)' END AS tier,
  COUNT(*)                  AS pessoas,
  SUM(vl_total_mecenas)     AS receita,
  AVG(vl_total_mecenas)     AS por_pessoa
FROM `{BASE}`
WHERE bl_is_mecenas
GROUP BY 1
"""

# Campanha atual: Solidário vs doador de bolsa vs controle
Q_SOLIDARIO = f"""
SELECT
  CASE WHEN bl_is_solidario AND bl_is_mecenas THEN 'solidario_ja_doador'
       WHEN bl_is_solidario                   THEN 'solidario_novo'
       WHEN bl_is_mecenas                     THEN 'bolsa'
       ELSE 'controle' END AS grupo,
  COUNT(*) AS pessoas,
  SUM(vl_total_solidario) AS receita_solidario,
  AVG(IF(bl_is_solidario, vl_maior_tx_solidario, vl_maior_tx_mecenas)) AS doacao_media,
  APPROX_QUANTILES(IF(bl_is_solidario, vl_maior_tx_solidario, vl_maior_tx_mecenas), 2)[OFFSET(1)] AS doacao_mediana,
  100 * AVG(IF(cd_income_decile >= 9, 1, 0)) AS renda_top,
  100 * AVG(IF(nm_credit_card_level_max IN ('6_black','5_amex'), 1, 0)) AS cartao_top,
  100 * AVG(IF(pc_similaridade >= 0.95, 1, 0)) AS socio,
  100 * AVG(IF(vl_capital_social >= 1000000, 1, 0)) AS capital_1m,
  100 * AVG(bl_vitalicio) AS vitalicio,
  100 * AVG(bl_certificacao) AS certificacao,
  100 * AVG(IF(nm_gender_inferred = 'Feminino', 1, 0)) AS feminino,
  AVG(qt_idade) AS idade,
  APPROX_QUANTILES(qt_idade, 2)[OFFSET(1)] AS idade_mediana,
  AVG(qt_dias_casa) / 365 AS anos_casa,
  AVG(vl_total_outras) AS gasto_previo,
  APPROX_QUANTILES(vl_total_outras, 2)[OFFSET(1)] AS gasto_previo_mediana,
  100 * AVG(bl_ja_comprou_comercial) AS via_comercial
FROM `{BASE}`
WHERE bl_is_solidario OR bl_is_mecenas OR bl_membro_ativo = 1
GROUP BY 1
"""

# Distribuição das faixas de contribuição do Solidário
Q_SOLIDARIO_FAIXA = f"""
SELECT
  CASE WHEN vl_maior_tx_solidario < 100 THEN 'Mensal (R$ 27 a 97)'
       WHEN vl_maior_tx_solidario < 500 THEN 'R$ 1/dia (R$ 358,80)'
       WHEN vl_maior_tx_solidario < 900 THEN 'R$ 2/dia (R$ 718,80)'
       WHEN vl_maior_tx_solidario < 2000 THEN 'R$ 3/dia (R$ 1.078,80)'
       ELSE 'Pacote do Comercial (R$ 2 mil+)' END AS faixa,
  COUNT(*) AS pessoas,
  SUM(vl_total_solidario) AS receita
FROM `{BASE}`
WHERE bl_is_solidario
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

    print("  solidário (campanha atual)...", flush=True)
    sol = {x["grupo"]: x for x in bq(Q_SOLIDARIO)}
    sol_faixa = bq(Q_SOLIDARIO_FAIXA)

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
        "solidario": {
            "grupos": {
                g: {
                    "pessoas": ii(v["pessoas"]),
                    "receita": fi(v["receita_solidario"]),
                    "doacao_media": fi(v["doacao_media"]),
                    "doacao_mediana": fi(v["doacao_mediana"]),
                    "renda_top": fi(v["renda_top"]),
                    "cartao_top": fi(v["cartao_top"]),
                    "socio": fi(v["socio"]),
                    "capital_1m": fi(v["capital_1m"]),
                    "vitalicio": fi(v["vitalicio"]),
                    "certificacao": fi(v["certificacao"]),
                    "feminino": fi(v["feminino"]),
                    "idade": fi(v["idade"]),
                    "idade_mediana": fi(v["idade_mediana"]),
                    "anos_casa": fi(v["anos_casa"]),
                    "gasto_previo": fi(v["gasto_previo"]),
                    "gasto_previo_mediana": fi(v["gasto_previo_mediana"]),
                    "via_comercial": fi(v["via_comercial"]),
                }
                for g, v in sol.items()
            },
            "faixas": sorted(
                [{"faixa": f["faixa"], "pessoas": ii(f["pessoas"]), "receita": fi(f["receita"])}
                 for f in sol_faixa],
                key=lambda x: -x["pessoas"],
            ),
        },
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
