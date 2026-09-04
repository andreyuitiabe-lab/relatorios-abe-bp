#!/usr/bin/env python3
"""
Refresh: Coleção Brasil: A Última Cruzada (CBR) — perfil do comprador e abordagem

Duas etapas:
  1. Executa os .sql canônicos de `queries/` que materializam as tabelas de trabalho
     (`bp-staging.dbt_abe.tb_uc_compradores` e `tb_uc_abordagens`).
  2. Roda as agregações e escreve data.json.

Os .sql em queries/ são a fonte canônica — corrigir lá, nunca duplicar aqui.

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push
"""

import json, subprocess, sys, datetime
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data.json"
Q = HERE / "queries"

TB_COMP = "`bp-staging.dbt_abe.tb_uc_compradores`"
TB_AB = "`bp-staging.dbt_abe.tb_uc_abordagens`"

# Benchmark da base de membros ativos — recalculado pelo próprio refresh (queries/benchmark_base.sql)


def client():
    from google.cloud import bigquery
    return bigquery.Client(project="bp-datawarehouse")


def run(sql: str) -> None:
    """Executa DDL/DML sem retorno."""
    client().query(sql).result()


def q(sql: str, max_rows: int = 5000) -> list[dict]:
    rows = client().query(sql).result(max_results=max_rows)
    return [
        {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in dict(r).items()}
        for r in rows
    ]


def one(sql: str) -> dict:
    r = q(sql, max_rows=1)
    if not r:
        raise RuntimeError(f"query sem linhas:\n{sql[:200]}")
    return r[0]


def fi(v) -> float:
    try:
        return round(float(v), 2) if v not in (None, "", "null") else 0.0
    except (TypeError, ValueError):
        return 0.0


def ii(v) -> int:
    try:
        return int(float(v)) if v not in (None, "", "null") else 0
    except (TypeError, ValueError):
        return 0


# ── etapa 1: materializar tabelas de trabalho ────────────────────────────────

def rebuild_tables() -> None:
    for name in ("base_compradores.sql", "funil_abordagem.sql"):
        sql = (Q / name).read_text(encoding="utf-8")
        print(f"  · {name}")
        run(sql)


# ── etapa 2: agregações ──────────────────────────────────────────────────────

def build() -> dict:
    # -- cabeçalho / totais -----------------------------------------------------
    tot = one(f"""
      SELECT
        COUNT(*) AS compradores,
        SUM(vl_uc) AS receita,
        AVG(vl_uc) AS ticket,
        COUNTIF(bl_comercial) AS comercial,
        COUNTIF(NOT bl_comercial) AS digital,
        SUM(IF(bl_comercial, vl_uc, 0)) AS receita_comercial,
        SUM(IF(NOT bl_comercial, vl_uc, 0)) AS receita_digital,
        COUNTIF(qt_compras_ant > 0) AS ja_era_cliente,
        COUNTIF(qt_compras_ant IS NULL) AS primeira_compra,
        MIN(DATE(dt_compra_uc)) AS dt_min,
        MAX(DATE(dt_compra_uc)) AS dt_max
      FROM {TB_COMP}
    """)

    dia = q(f"""
      SELECT DATE(dt_compra_uc) AS dia,
             COUNTIF(bl_comercial) AS comercial,
             COUNTIF(NOT bl_comercial) AS digital,
             SUM(vl_uc) AS receita
      FROM {TB_COMP} GROUP BY 1 ORDER BY 1
    """)

    # -- vínculo com a base ------------------------------------------------------
    vinc = one(f"""
      SELECT
        COUNT(*) AS n,
        COUNTIF(bl_membro_ativo) AS membro_ativo,
        COUNTIF(bl_vitalicio) AS vitalicio,
        COUNTIF(bl_mecenas) AS mecenas,
        COUNTIF(bl_cdl) AS cdl,
        COUNTIF(bl_odisseia) AS odisseia,
        COUNTIF(bl_certificacao) AS certificacao,
        COUNTIF(bl_teller) AS teller
      FROM {TB_COMP}
    """)

    consumo = one(f"""
      SELECT
        APPROX_QUANTILES(vl_ltv_ant, 2)[OFFSET(1)] AS ltv_mediana,
        AVG(vl_ltv_ant) AS ltv_medio,
        APPROX_QUANTILES(qt_compras_ant, 2)[OFFSET(1)] AS compras_mediana,
        AVG(qt_dias_de_casa) / 365.0 AS anos_casa_medio,
        APPROX_QUANTILES(qt_dias_de_casa, 2)[OFFSET(1)] / 365.0 AS anos_casa_mediana,
        COUNTIF(vl_ltv_ant >= 4000) AS ltv_4k_mais,
        COUNTIF(vl_ltv_ant IS NOT NULL) AS com_historico
      FROM {TB_COMP}
    """)

    casa = q(f"""
      SELECT CASE
               WHEN qt_dias_de_casa IS NULL THEN 'Novo'
               WHEN qt_dias_de_casa < 365  THEN '< 1 ano'
               WHEN qt_dias_de_casa < 730  THEN '1–2 anos'
               WHEN qt_dias_de_casa < 1460 THEN '2–4 anos'
               WHEN qt_dias_de_casa < 2190 THEN '4–6 anos'
               ELSE '6+ anos' END AS faixa,
             CASE
               WHEN qt_dias_de_casa IS NULL THEN 0
               WHEN qt_dias_de_casa < 365  THEN 1
               WHEN qt_dias_de_casa < 730  THEN 2
               WHEN qt_dias_de_casa < 1460 THEN 3
               WHEN qt_dias_de_casa < 2190 THEN 4
               ELSE 5 END AS ord,
             COUNT(*) AS n,
             APPROX_QUANTILES(vl_ltv_ant, 2)[OFFSET(1)] AS ltv_mediana
      FROM {TB_COMP} GROUP BY 1, 2 ORDER BY ord
    """)

    # -- perfil socioeconômico + benchmark --------------------------------------
    perfil = one(f"""
      SELECT
        COUNTIF(nivel_cartao IS NOT NULL) AS base_cartao,
        COUNTIF(nivel_cartao IN ('6_black','5_amex','4_platinum')) AS cartao_premium,
        COUNTIF(nivel_cartao = '6_black') AS cartao_black,
        COUNTIF(cd_income_decile > 0) AS base_renda,
        COUNTIF(cd_income_decile >= 8) AS decil_8mais,
        COUNTIF(nm_gender_inferred = 'Masculino') AS masculino,
        COUNTIF(nm_gender_inferred = 'Feminino') AS feminino,
        COUNTIF(dt_birthday IS NOT NULL) AS base_idade,
        COUNTIF(dt_birthday IS NOT NULL
                AND DATE_DIFF(CURRENT_DATE(), DATE(dt_birthday), YEAR) >= 45) AS idade_45mais,
        COUNTIF(nm_payment_method = 'credit_card') AS pg_cartao,
        COUNTIF(nm_payment_method = 'pix') AS pg_pix
      FROM {TB_COMP}
    """)

    bench = one((Q / "benchmark_base.sql").read_text(encoding="utf-8"))

    renda = q(f"""
      SELECT cd_income_decile AS decil, COUNT(*) AS n
      FROM {TB_COMP} WHERE cd_income_decile > 0 GROUP BY 1 ORDER BY 1
    """)

    cartao = q(f"""
      SELECT nivel_cartao AS nivel, COUNT(*) AS n
      FROM {TB_COMP} WHERE nivel_cartao IS NOT NULL GROUP BY 1 ORDER BY 1 DESC
    """)

    uf = q(f"""
      SELECT COALESCE(uf_contato, '—') AS uf, COUNT(*) AS n
      FROM {TB_COMP} GROUP BY 1 ORDER BY n DESC LIMIT 8
    """)

    # -- engajamento -------------------------------------------------------------
    eng = q(f"""
      SELECT CASE
               WHEN COALESCE(qt_dias_ativos_90d, 0) = 0 THEN 'Nenhuma sessão'
               WHEN qt_dias_ativos_90d <= 3  THEN '1–3 dias'
               WHEN qt_dias_ativos_90d <= 10 THEN '4–10 dias'
               WHEN qt_dias_ativos_90d <= 30 THEN '11–30 dias'
               ELSE '30+ dias' END AS faixa,
             CASE
               WHEN COALESCE(qt_dias_ativos_90d, 0) = 0 THEN 0
               WHEN qt_dias_ativos_90d <= 3  THEN 1
               WHEN qt_dias_ativos_90d <= 10 THEN 2
               WHEN qt_dias_ativos_90d <= 30 THEN 3
               ELSE 4 END AS ord,
             COUNT(*) AS n,
             AVG(hr_assistidas_90d) AS hr_90d,
             100 * COUNTIF(bl_comercial) / COUNT(*) AS pc_comercial
      FROM {TB_COMP} GROUP BY 1, 2 ORDER BY ord
    """)

    # -- produto e preço ---------------------------------------------------------
    produto = q(f"""
      SELECT CASE
               WHEN planos_uc LIKE '%completo%' THEN 'Completo (livro + cursos)'
               WHEN planos_uc LIKE '%digital%'  THEN 'Digital'
               WHEN planos_uc LIKE '%fisico%' AND planos_uc LIKE '%black%' THEN 'Bundle Black'
               WHEN planos_uc LIKE '%black%'    THEN 'Bundle Black'
               WHEN planos_uc LIKE '%fisico%'   THEN 'Físico'
               ELSE 'Outro' END AS produto,
             COUNT(*) AS n, AVG(vl_uc) AS ticket, SUM(vl_uc) AS receita,
             COUNTIF(bl_comercial) AS comercial
      FROM {TB_COMP} GROUP BY 1 ORDER BY n DESC
    """)

    preco = q(f"""
      SELECT CASE WHEN planos_uc LIKE '%completo%' THEN 'Completo'
                  WHEN planos_uc LIKE '%fisico%'   THEN 'Físico'
                  ELSE 'Outro' END AS produto,
             CASE WHEN bl_comercial THEN 'Comercial' ELSE 'Digital' END AS canal,
             COUNT(*) AS n, AVG(vl_uc) AS ticket
      FROM {TB_COMP}
      WHERE planos_uc LIKE '%completo%' OR planos_uc LIKE '%fisico%'
      GROUP BY 1, 2 ORDER BY 1, 2
    """)

    faixas_preco = q(f"""
      SELECT ROUND(vl_uc) AS valor, COUNT(*) AS n,
             COUNTIF(bl_comercial) AS comercial, COUNTIF(NOT bl_comercial) AS digital
      FROM {TB_COMP}
      WHERE planos_uc LIKE '%fisico%' AND planos_uc NOT LIKE '%black%'
      GROUP BY 1 HAVING n >= 3 ORDER BY valor
    """)

    # -- abordagem ---------------------------------------------------------------
    ab_tpl = q(f"""
      SELECT bucket,
             COUNT(*) AS prospects,
             COUNTIF(max_resposta_cliente > 0) AS respondeu,
             COUNTIF(bl_comprou_apos_abordagem) AS comprou,
             SUM(IF(bl_comprou_apos_abordagem, vl_uc, 0)) AS receita,
             100 * COUNTIF(bl_abertura_scriptada) / COUNT(*) AS pc_scriptado,
             100 * COUNTIF(max_resposta_cliente > 0 AND bl_comprou_apos_abordagem)
                   / NULLIF(COUNTIF(max_resposta_cliente > 0), 0) AS pc_conv_respondeu
      FROM {TB_AB} GROUP BY 1 ORDER BY 1
    """)

    # M2 — mesma etapa do CRM, para isolar o efeito do disparo da composição da lista.
    # `carteiraMecenas` concentra a operação, então é o único estrato com n suficiente.
    ab_carteira = q(f"""
      SELECT bucket, COUNT(*) AS prospects,
             COUNTIF(bl_comprou_apos_abordagem) AS comprou,
             100 * COUNTIF(bl_comprou_apos_abordagem) / COUNT(*) AS pc
      FROM {TB_AB} WHERE etapa_atual = 'carteiraMecenas' GROUP BY 1 ORDER BY 1
    """)

    ab_etapa = q(f"""
      SELECT etapa_atual AS etapa, COUNT(*) AS prospects,
             COUNTIF(bl_comprou_apos_abordagem) AS comprou
      FROM {TB_AB}
      WHERE etapa_atual IS NOT NULL
      GROUP BY 1 HAVING prospects >= 50
      ORDER BY comprou / prospects DESC LIMIT 8
    """)

    ab_tot = one(f"""
      SELECT COUNT(*) AS prospects, COUNTIF(max_resposta_cliente > 0) AS respondeu,
             COUNTIF(bl_comprou_apos_abordagem) AS comprou,
             COUNTIF(bl_comprou AND NOT bl_comprou_apos_abordagem) AS comprou_antes_da_abordagem
      FROM {TB_AB}
    """)

    vendedores = one(f"""
      SELECT COUNT(DISTINCT nm_salesman) AS n_vendedores,
             MAX(vendas) AS top_vendas
      FROM (SELECT nm_salesman, COUNT(*) AS vendas FROM {TB_COMP}
            WHERE bl_comercial AND nm_salesman IS NOT NULL GROUP BY 1)
    """)

    # -- atribuição --------------------------------------------------------------
    # ⚠️ M4 — "abordado" exige abordagem ANTES da compra. Sem a guarda, metade das vendas
    # "abordado → digital" era de gente abordada DEPOIS de já ter comprado (o Comercial
    # correndo atrás da lista), o que sustentava indevidamente a tese de crédito ambíguo.
    atrib = q(f"""
      WITH comp AS (
        SELECT b.*, c.cd_cleaned_phone_number AS fone
        FROM {TB_COMP} b
        LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
      ),
      ab AS (
        SELECT fone, MIN(dt_primeira_abordagem) AS dt_primeira_abordagem
        FROM {TB_AB} WHERE fone IS NOT NULL GROUP BY 1
      ),
      j AS (
        SELECT comp.*,
               ab.fone IS NOT NULL
                 AND comp.dt_compra_uc >= ab.dt_primeira_abordagem AS bl_abordado_antes
        FROM comp LEFT JOIN ab USING (fone)
      )
      SELECT
        CASE WHEN bl_abordado_antes AND bl_comercial THEN 'Abordado → Comercial'
             WHEN bl_abordado_antes THEN 'Abordado → Digital'
             WHEN bl_comercial THEN 'Comercial sem abordagem prévia'
             ELSE 'Digital sem abordagem prévia' END AS origem,
        CASE WHEN bl_abordado_antes AND bl_comercial THEN 1
             WHEN bl_abordado_antes THEN 2
             WHEN bl_comercial THEN 3 ELSE 4 END AS ord,
        COUNT(*) AS n, SUM(vl_uc) AS receita, AVG(vl_uc) AS ticket,
        100 * COUNTIF(bl_membro_ativo) / COUNT(*) AS pc_membro,
        100 * COUNTIF(bl_vitalicio) / COUNT(*) AS pc_vitalicio,
        APPROX_QUANTILES(vl_ltv_ant, 2)[OFFSET(1)] AS ltv_mediana,
        100 * COUNTIF(nivel_cartao IN ('6_black','5_amex','4_platinum'))
              / NULLIF(COUNTIF(nivel_cartao IS NOT NULL), 0) AS pc_cartao_premium
      FROM j
      GROUP BY 1, 2 ORDER BY ord
    """)

    # -- recusas -----------------------------------------------------------------
    recusa = one("""
      SELECT COUNT(DISTINCT id_gateway_customer) AS pessoas, COUNT(*) AS tx
      FROM `bp-datawarehouse.masterdata.fct_transactions`
      WHERE DATE(dt_ordered_at) >= '2026-09-01'
        AND nm_gateway_plan LIKE 'colecao-brasil%'
        AND nm_status IN ('canceled', 'abandoned')
    """)

    # -- penetração no CDL --------------------------------------------------------
    pen = one(f"""
      WITH cdl AS (
        SELECT DISTINCT LOWER(TRIM(c.nm_email)) AS email
        FROM `bp-datawarehouse.masterdata.fct_transactions` t
        JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
        WHERE t.nm_status = 'approved'
          AND t.nm_gateway_plan IN ('clube-do-livro', 'clube-do-livro-basico')
      )
      SELECT (SELECT COUNT(*) FROM cdl) AS base_cdl,
             (SELECT COUNT(*) FROM {TB_COMP} WHERE email IN (SELECT email FROM cdl)) AS converteu
    """)

    n = ii(tot["compradores"])

    def pc(part, whole):
        whole = ii(whole)
        return round(100.0 * ii(part) / whole, 1) if whole else 0.0

    return {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "periodo": {"inicio": tot["dt_min"], "fim": tot["dt_max"]},
        "totais": {
            "compradores": n,
            "receita": ii(tot["receita"]),
            "ticket": ii(tot["ticket"]),
            "comercial": ii(tot["comercial"]),
            "digital": ii(tot["digital"]),
            "receita_comercial": ii(tot["receita_comercial"]),
            "receita_digital": ii(tot["receita_digital"]),
            "pc_comercial": pc(tot["comercial"], n),
            "ja_era_cliente": ii(tot["ja_era_cliente"]),
            "pc_ja_era_cliente": pc(tot["ja_era_cliente"], n),
            "primeira_compra": ii(tot["primeira_compra"]),
            "recusa_pessoas": ii(recusa["pessoas"]),
            "recusa_tx": ii(recusa["tx"]),
        },
        "dia": [
            {"dia": r["dia"], "comercial": ii(r["comercial"]),
             "digital": ii(r["digital"]), "receita": ii(r["receita"])}
            for r in dia
        ],
        "vinculo": [
            {"label": "Membro ativo hoje", "n": ii(vinc["membro_ativo"]), "pc": pc(vinc["membro_ativo"], n)},
            {"label": "Vitalício", "n": ii(vinc["vitalicio"]), "pc": pc(vinc["vitalicio"], n)},
            {"label": "Comprou o Clube do Livro", "n": ii(vinc["cdl"]), "pc": pc(vinc["cdl"], n)},
            {"label": "Mecenas (atual ou ex)", "n": ii(vinc["mecenas"]), "pc": pc(vinc["mecenas"], n)},
            {"label": "Comprou a Odisseia", "n": ii(vinc["odisseia"]), "pc": pc(vinc["odisseia"], n)},
            {"label": "Tem certificação", "n": ii(vinc["certificacao"]), "pc": pc(vinc["certificacao"], n)},
            {"label": "Assinante Teller", "n": ii(vinc["teller"]), "pc": pc(vinc["teller"], n)},
        ],
        "consumo": {
            "ltv_mediana": ii(consumo["ltv_mediana"]),
            "ltv_medio": ii(consumo["ltv_medio"]),
            "compras_mediana": ii(consumo["compras_mediana"]),
            "anos_casa_medio": fi(consumo["anos_casa_medio"]),
            "anos_casa_mediana": fi(consumo["anos_casa_mediana"]),
            "pc_ltv_4k_mais": pc(consumo["ltv_4k_mais"], consumo["com_historico"]),
        },
        "casa": [
            {"faixa": r["faixa"], "n": ii(r["n"]), "pc": pc(r["n"], n),
             "ltv_mediana": ii(r["ltv_mediana"])} for r in casa
        ],
        "perfil": {
            "pc_cartao_premium": pc(perfil["cartao_premium"], perfil["base_cartao"]),
            "pc_cartao_black": pc(perfil["cartao_black"], perfil["base_cartao"]),
            "pc_decil_8mais": pc(perfil["decil_8mais"], perfil["base_renda"]),
            "base_cartao": ii(perfil["base_cartao"]),
            "base_renda": ii(perfil["base_renda"]),
            "pc_masculino": pc(perfil["masculino"], ii(perfil["masculino"]) + ii(perfil["feminino"])),
            "pc_idade_45mais": pc(perfil["idade_45mais"], perfil["base_idade"]),
            "base_idade": ii(perfil["base_idade"]),
            "pc_pg_cartao": pc(perfil["pg_cartao"], n),
            "pc_pg_pix": pc(perfil["pg_pix"], n),
        },
        "benchmark": {
            "n": ii(bench["n"]),
            "pc_cartao_premium": fi(bench["pc_cartao_premium"]),
            "pc_cartao_black": fi(bench["pc_black"]),
            "pc_decil_8mais": fi(bench["pc_decil_8mais"]),
        },
        "renda": [{"decil": ii(r["decil"]), "n": ii(r["n"])} for r in renda],
        "cartao": [{"nivel": r["nivel"], "n": ii(r["n"])} for r in cartao],
        "uf": [{"uf": r["uf"], "n": ii(r["n"]), "pc": pc(r["n"], n)} for r in uf],
        "engajamento": [
            {"faixa": r["faixa"], "n": ii(r["n"]), "pc": pc(r["n"], n),
             "hr_90d": fi(r["hr_90d"]), "pc_comercial": fi(r["pc_comercial"])} for r in eng
        ],
        "produto": [
            {"produto": r["produto"], "n": ii(r["n"]), "ticket": ii(r["ticket"]),
             "receita": ii(r["receita"]), "comercial": ii(r["comercial"])} for r in produto
        ],
        "preco": [
            {"produto": r["produto"], "canal": r["canal"], "n": ii(r["n"]),
             "ticket": ii(r["ticket"])} for r in preco
        ],
        "faixas_preco": [
            {"valor": ii(r["valor"]), "n": ii(r["n"]), "comercial": ii(r["comercial"]),
             "digital": ii(r["digital"])} for r in faixas_preco
        ],
        "abordagem": {
            "total_prospects": ii(ab_tot["prospects"]),
            "total_respondeu": ii(ab_tot["respondeu"]),
            "total_comprou": ii(ab_tot["comprou"]),
            "comprou_antes_da_abordagem": ii(ab_tot["comprou_antes_da_abordagem"]),
            "pc_resposta_geral": pc(ab_tot["respondeu"], ab_tot["prospects"]),
            "n_vendedores": ii(vendedores["n_vendedores"]),
            "top_vendas": ii(vendedores["top_vendas"]),
            "buckets": [
                {"bucket": r["bucket"][3:],
                 "prospects": ii(r["prospects"]),
                 "respondeu": ii(r["respondeu"]),
                 "comprou": ii(r["comprou"]),
                 "receita": ii(r["receita"]),
                 "pc_resposta": round(100.0 * ii(r["respondeu"]) / ii(r["prospects"]), 2)
                 if ii(r["prospects"]) else 0.0,
                 "pc_conversao": round(100.0 * ii(r["comprou"]) / ii(r["prospects"]), 3)
                 if ii(r["prospects"]) else 0.0,
                 "pc_conv_respondeu": fi(r["pc_conv_respondeu"]),
                 "pc_scriptado": fi(r["pc_scriptado"])}
                for r in ab_tpl
            ],
            "carteira": [
                {"bucket": r["bucket"][3:], "prospects": ii(r["prospects"]),
                 "comprou": ii(r["comprou"]), "pc": fi(r["pc"])}
                for r in ab_carteira
            ],
            "etapas": [
                {"etapa": r["etapa"], "prospects": ii(r["prospects"]), "comprou": ii(r["comprou"]),
                 "pc": round(100.0 * ii(r["comprou"]) / ii(r["prospects"]), 2)
                 if ii(r["prospects"]) else 0.0}
                for r in ab_etapa
            ],
        },
        "atribuicao": [
            {"origem": r["origem"], "n": ii(r["n"]), "pc": pc(r["n"], n),
             "receita": ii(r["receita"]), "ticket": ii(r["ticket"]),
             "pc_membro": fi(r["pc_membro"]), "pc_vitalicio": fi(r["pc_vitalicio"]),
             "ltv_mediana": ii(r["ltv_mediana"]),
             "pc_cartao_premium": fi(r["pc_cartao_premium"])}
            for r in atrib
        ],
        "penetracao_cdl": {
            "base": ii(pen["base_cdl"]),
            "converteu": ii(pen["converteu"]),
            "pc": round(100.0 * ii(pen["converteu"]) / ii(pen["base_cdl"]), 2)
            if ii(pen["base_cdl"]) else 0.0,
        },
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    skip = "--skip-rebuild" in sys.argv
    print("Refreshing relatório Coleção Brasil: A Última Cruzada...")
    try:
        if not skip:
            print("→ materializando tabelas de trabalho")
            rebuild_tables()
        print("→ agregando")
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']} — "
              f"{data['totais']['compradores']} compradores / R$ {data['totais']['receita']:,}")
        if push:
            repo = Path(__file__).parent.parent.parent
            subprocess.run(["git", "add", str(OUT)], check=True, cwd=repo)
            subprocess.run(
                ["git", "commit", "-m", f"data: ultima-cruzada-perfil refresh {datetime.date.today()}"],
                check=True, cwd=repo)
            subprocess.run(["git", "push", "origin", "main"], check=True, cwd=repo)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
