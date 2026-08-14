#!/usr/bin/env python3
"""
Refresh do relatório "Quem está comprando o Enéas (ENE)".

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Pipeline:
  1. Recria as tabelas scratch (bp-staging.dbt_abe.tb_ene_*) a partir de queries/*.sql
  2. Roda as agregações e escreve data.json
"""

import json, subprocess, sys, datetime
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data.json"
DDL_FILES = ["base_compradores.sql", "perfil_compradores.sql", "checkout_falhas.sql"]

PERFIL = "`bp-staging.dbt_abe.tb_ene_perfil`"
TX = "`bp-staging.dbt_abe.tb_ene_compradores_tx`"
TENT = "`bp-staging.dbt_abe.tb_ene_tentativas`"


def bq(sql: str, max_rows: int = 5000) -> list[dict]:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         f"--max_rows={max_rows}", "--project_id=bp-datawarehouse", sql],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    out = r.stdout.strip()
    # o bq às vezes imprime warnings antes do JSON
    out = out[out.index("["):] if "[" in out else out
    return json.loads(out) if out else []


def bq_file(path: Path) -> None:
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--project_id=bp-datawarehouse"],
        stdin=path.open(), capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"{path.name}: {r.stderr.strip()}")


def fi(v) -> float:
    try:
        return float(v) if v not in (None, "", "null") else 0.0
    except Exception:
        return 0.0


def ii(v) -> int:
    return int(fi(v))


# ─── agregações ──────────────────────────────────────────────────────────────

Q_RESUMO = f"""
SELECT
  COUNT(*) compradores,
  ROUND(SUM(vl_receita)) receita,
  ROUND(SUM(vl_receita)/COUNT(*)) ticket,
  ROUND(100*COUNTIF(bl_ja_era_cliente)/COUNT(*),1) pct_ja_cliente,
  ROUND(100*COUNTIF(nm_gender_inferred='Masculino')
    /NULLIF(COUNTIF(nm_gender_inferred IS NOT NULL),0),1) pct_masc,
  ROUND(AVG(IF(qt_idade BETWEEN 14 AND 100, qt_idade, NULL)),1) idade_media,
  APPROX_QUANTILES(IF(qt_idade BETWEEN 14 AND 100, qt_idade, NULL), 2)[OFFSET(1)] idade_mediana,
  ROUND(AVG(IF(cd_income_decile > 0, cd_income_decile, NULL)),2) decil_medio,
  ROUND(100*COUNTIF(cd_income_decile >= 7)
    /NULLIF(COUNTIF(cd_income_decile > 0),0),1) pct_decil7,
  ROUND(100*COUNTIF(cd_income_decile > 0)/COUNT(*),1) cobertura_renda,
  ROUND(100*COUNTIF(qt_idade BETWEEN 14 AND 100)/COUNT(*),1) cobertura_idade,
  (SELECT COUNT(*) FROM {TX}) qt_tx
FROM {PERFIL}
"""

Q_CANAIS = f"""
SELECT
  nm_canal,
  COUNT(*) compradores,
  ROUND(SUM(vl_receita)) receita,
  ROUND(SUM(vl_receita)/COUNT(*)) ticket,
  ROUND(100*COUNTIF(bl_ja_era_cliente)/COUNT(*),1) pct_ja_cliente,
  ROUND(AVG(IF(qt_idade BETWEEN 14 AND 100, qt_idade, NULL)),1) idade_media,
  COUNTIF(qt_idade BETWEEN 14 AND 100) n_idade,
  ROUND(AVG(IF(cd_income_decile > 0, cd_income_decile, NULL)),2) decil_medio
FROM {PERFIL}
GROUP BY 1 ORDER BY compradores DESC
"""

Q_FAIXAS = f"""
SELECT
  CASE
    WHEN qt_idade BETWEEN 14 AND 24 THEN '14-24'
    WHEN qt_idade BETWEEN 25 AND 34 THEN '25-34'
    WHEN qt_idade BETWEEN 35 AND 44 THEN '35-44'
    WHEN qt_idade BETWEEN 45 AND 54 THEN '45-54'
    WHEN qt_idade BETWEEN 55 AND 64 THEN '55-64'
    WHEN qt_idade BETWEEN 65 AND 100 THEN '65+'
  END faixa,
  COUNT(*) compradores
FROM {PERFIL}
WHERE qt_idade BETWEEN 14 AND 100
GROUP BY 1 ORDER BY 1
"""

Q_UF = f"""
SELECT COALESCE(cd_address_state,'—') uf, COUNT(*) compradores
FROM {PERFIL} GROUP BY 1 ORDER BY 2 DESC LIMIT 12
"""

Q_PRODUTOS = f"""
SELECT nm_canal, nm_plan_label, COUNT(*) qt_tx, ROUND(SUM(vl_payment_gross)) receita
FROM {TX}
WHERE nm_canal IN ('Meta Ads','Redes sociais (orgânico)',
                   'Comercial — humano','Comercial — Lambda (IA)')
GROUP BY 1,2
QUALIFY ROW_NUMBER() OVER (PARTITION BY nm_canal ORDER BY COUNT(*) DESC) <= 4
ORDER BY nm_canal, qt_tx DESC
"""

Q_DIARIO = f"""
SELECT CAST(DATE(dt_ordered_at) AS STRING) dia,
  COUNTIF(nm_canal NOT LIKE 'Comercial%') digital,
  COUNTIF(nm_canal = 'Comercial — humano') humano,
  COUNTIF(nm_canal = 'Comercial — Lambda (IA)') lambda
FROM {TX} GROUP BY 1 ORDER BY 1
"""

Q_STATUS = f"""
SELECT nm_status, COUNT(*) qt_tx, COUNT(DISTINCT nm_email) pessoas
FROM {TENT} GROUP BY 1 ORDER BY 2 DESC
"""

Q_FLUXO = f"""
WITH pessoa AS (
  SELECT nm_email,
    MIN(IF(nm_status IN ('canceled','abandoned','expired'), dt_ordered_at, NULL)) dt_falha,
    MIN(IF(nm_status = 'approved', dt_ordered_at, NULL)) dt_ok,
    ARRAY_AGG(IF(nm_status='approved',
      CASE WHEN bl_lambda THEN 'Lambda' WHEN bl_comercial THEN 'Comercial humano'
           ELSE 'Digital' END, NULL) IGNORE NULLS ORDER BY dt_ordered_at LIMIT 1
    )[SAFE_OFFSET(0)] canal
  FROM {TENT} WHERE nm_email IS NOT NULL GROUP BY 1
)
SELECT
  CASE
    WHEN dt_falha IS NULL THEN 'comprou de primeira'
    WHEN dt_ok IS NULL THEN 'falhou e nunca comprou'
    WHEN dt_ok > dt_falha THEN CONCAT('falhou → comprou via ', canal)
    ELSE 'comprou antes, falhou depois'
  END fluxo,
  COUNT(*) pessoas
FROM pessoa GROUP BY 1 ORDER BY 2 DESC
"""

Q_FALHA_PREVIA = f"""
WITH pessoa AS (
  SELECT nm_email,
    ARRAY_AGG(IF(nm_status='approved',
      CASE WHEN bl_lambda THEN 'Lambda' WHEN bl_comercial THEN 'Comercial humano'
           ELSE 'Digital' END, NULL) IGNORE NULLS ORDER BY dt_ordered_at LIMIT 1
    )[SAFE_OFFSET(0)] canal,
    COUNTIF(nm_status IN ('canceled','abandoned') AND NOT bl_lambda AND NOT bl_comercial)
      qt_falhas_digital
  FROM {TENT} WHERE nm_email IS NOT NULL GROUP BY 1
)
SELECT canal, COUNT(*) compradores,
  COUNTIF(qt_falhas_digital > 0) com_falha,
  ROUND(100*COUNTIF(qt_falhas_digital > 0)/COUNT(*),1) pct_falha
FROM pessoa WHERE canal IS NOT NULL GROUP BY 1 ORDER BY 2 DESC
"""

Q_MOTIVOS = f"""
SELECT COALESCE(t.nm_error_category, t.nm_refuse_reason, '(vazio)') motivo, COUNT(*) qt
FROM `bp-datawarehouse.masterdata.fct_transactions` t
INNER JOIN {TENT} e USING (id_transaction)
WHERE e.nm_status = 'canceled'
GROUP BY 1 ORDER BY 2 DESC LIMIT 10
"""

Q_IDADE_GRUPO = f"""
WITH pessoa AS (
  SELECT nm_email,
    MIN(IF(nm_status IN ('canceled','abandoned','expired'), dt_ordered_at, NULL)) dt_falha,
    MIN(IF(nm_status = 'approved', dt_ordered_at, NULL)) dt_ok
  FROM {TENT} WHERE nm_email IS NOT NULL GROUP BY 1
),
u AS (
  SELECT LOWER(nm_email) nm_email,
    DATE_DIFF(CURRENT_DATE(), DATE(dt_birthday), YEAR) idade
  FROM `bp-datawarehouse.masterdata.dim_user`
  WHERE dt_birthday IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY LOWER(nm_email) ORDER BY id_user) = 1
)
SELECT
  CASE WHEN dt_falha IS NULL THEN 'comprou de primeira'
       WHEN dt_ok IS NULL THEN 'falhou e nunca comprou'
       ELSE 'falhou e comprou depois' END grupo,
  COUNT(*) pessoas,
  COUNTIF(u.idade BETWEEN 14 AND 100) n_idade,
  ROUND(AVG(IF(u.idade BETWEEN 14 AND 100, u.idade, NULL)),1) idade_media
FROM pessoa LEFT JOIN u USING (nm_email)
GROUP BY 1 ORDER BY 2 DESC
"""

# Trechos curados das conversas Zenvia (query: queries/conversas_zenvia.sql).
# Anonimizados manualmente — NUNCA incluir nome/telefone/email (repo público).
CONVERSAS_CURADAS = [
    {"dt": "2026-08-10", "quem": "compradora via Comercial humano",
     "trecho": "Vendedor: “Conseguiu realizar o pagamento?” — Cliente: “Não consegui ainda… é que não estou achando meu cartão.” (compra concluída no dia seguinte, com o vendedor acompanhando)"},
    {"dt": "2026-07-31", "quem": "comprador via Comercial humano",
     "trecho": "Cliente: “Não consigo abrir a página.” Vendedor reenvia o link, cliente conclui e pede o acesso em seguida."},
    {"dt": "2026-08-06", "quem": "cliente em atendimento",
     "trecho": "“Acabei me confundindo e não havia terminado o cadastro, estou tentando aqui agora e não estou conseguindo.”"},
    {"dt": "2026-08-04", "quem": "comprador (migração de plano)",
     "trecho": "“Não consigo, o plano novo de R$ 23 ainda não registrou, vou deixar pra tentar amanhã.” — fricção entre pagamento e liberação de acesso."},
    {"dt": "2026-08-04", "quem": "vendedor (orientação padrão)",
     "trecho": "“Nubank, Santander e Amex não aceitam em 18x — se for, faça em 12x para não perder.” — parcelamento alto recusado pelo emissor é fricção conhecida do próprio time."},
]


def build() -> dict:
    for f in DDL_FILES:
        print(f"[DDL] {f}")
        bq_file(HERE / "queries" / f)

    print("[agg] resumo")
    resumo = bq(Q_RESUMO)[0]
    print("[agg] demais")
    data = {
        "atualizado_em": datetime.date.today().isoformat(),
        "periodo": {"inicio": "2026-07-28", "fim": datetime.date.today().isoformat()},
        "resumo": {k: fi(v) for k, v in resumo.items()},
        "canais": [
            {"canal": r["nm_canal"], "compradores": ii(r["compradores"]),
             "receita": fi(r["receita"]), "ticket": fi(r["ticket"]),
             "pct_ja_cliente": fi(r["pct_ja_cliente"]),
             "idade_media": fi(r["idade_media"]), "n_idade": ii(r["n_idade"]),
             "decil_medio": fi(r["decil_medio"])}
            for r in bq(Q_CANAIS)
        ],
        "faixas_etarias": [
            {"faixa": r["faixa"], "compradores": ii(r["compradores"])}
            for r in bq(Q_FAIXAS)
        ],
        "uf": [{"uf": r["uf"], "compradores": ii(r["compradores"])} for r in bq(Q_UF)],
        "produtos": [
            {"canal": r["nm_canal"], "plano": r["nm_plan_label"],
             "qt_tx": ii(r["qt_tx"]), "receita": fi(r["receita"])}
            for r in bq(Q_PRODUTOS)
        ],
        "diario": [
            {"dia": r["dia"], "digital": ii(r["digital"]),
             "humano": ii(r["humano"]), "lambda": ii(r["lambda"])}
            for r in bq(Q_DIARIO)
        ],
        "status": [
            {"status": r["nm_status"], "qt_tx": ii(r["qt_tx"]),
             "pessoas": ii(r["pessoas"])}
            for r in bq(Q_STATUS)
        ],
        "fluxo": [{"fluxo": r["fluxo"], "pessoas": ii(r["pessoas"])} for r in bq(Q_FLUXO)],
        "falha_previa": [
            {"canal": r["canal"], "compradores": ii(r["compradores"]),
             "com_falha": ii(r["com_falha"]), "pct_falha": fi(r["pct_falha"])}
            for r in bq(Q_FALHA_PREVIA)
        ],
        "motivos_recusa": [{"motivo": r["motivo"], "qt": ii(r["qt"])} for r in bq(Q_MOTIVOS)],
        "idade_grupo": [
            {"grupo": r["grupo"], "pessoas": ii(r["pessoas"]),
             "n_idade": ii(r["n_idade"]), "idade_media": fi(r["idade_media"])}
            for r in bq(Q_IDADE_GRUPO)
        ],
        "conversas": CONVERSAS_CURADAS,
    }
    return data


def main():
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"OK → {OUT}")
    if "--push" in sys.argv:
        subprocess.run(["git", "-C", str(HERE), "add", "-A", "."], check=True)
        subprocess.run(["git", "-C", str(HERE), "commit", "-m",
                        "eneas: refresh data.json"], check=True)
        subprocess.run(["git", "-C", str(HERE), "push"], check=True)


if __name__ == "__main__":
    main()
