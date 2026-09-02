#!/usr/bin/env python3
"""
Refresh — Abordagens do Comercial: o que o time oferece e o que vende (janela ~2 meses).

Usage:
  python refresh.py          # atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Janela dinâmica: da segunda-feira de 8 semanas atrás até ontem (9 semanas, a última parcial).
Método:
  * "O que o time oferece" = menção ao tema na transcrição (masterdata.dim_zenvia_approaches.nm_conversation,
    regex). Uma conversa pode citar vários temas. Validado na análise odisseia-lancamento.
  * "Conversa real" = abordagem com resposta do cliente (qt_prospect_interactions > 0). ~85% das linhas
    são disparo sem resposta (nm_lead_source FLOW/N8N).
  * Conversão real por tema = conversa respondida que menciona o tema → a mesma pessoa (telefone OU e-mail,
    joins separados + UNION DISTINCT) compra no canal Comercial em até 14 dias.
As queries canônicas estão em queries/*.sql — manter em sincronia.
"""

import json, subprocess, sys, datetime, warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HOJE = datetime.date.today()
FIM = HOJE - datetime.timedelta(days=1)                              # último dia completo
INI = HOJE - datetime.timedelta(days=HOJE.weekday() + 7 * 8)        # segunda-feira, 8 semanas atrás
FIM_VENDA = FIM + datetime.timedelta(days=14)                        # janela de compra pós-conversa
OUT = Path(__file__).parent / "data.json"

TEMAS = {
    "vitalicio": r"vital[ií]cio",
    "black": r"black",
    "cdl": r"clube do livro",
    "odisseia": r"odiss[eé]ia",
    "mecenas": r"mecenas",
    "bp10": r"10 anos|dez anos|anivers[aá]rio",
    "cabral": r"imers[aã]o|cabral",
}
# tema → produto-alvo (para "conversão no produto ofertado")
ALVO = {"vitalicio": "vit", "black": "black", "cdl": "cdl", "odisseia": "odi", "mecenas": "mec", "cabral": "evt"}

PRODUTOS = ["CDL físico", "CDL ebook/audio", "Black Vitalício", "Premium Vitalício",
            "Básico/outros Vitalício", "Odisseia", "Mecenas", "Eventos high-ticket",
            "Black/Premium recorrente", "Assinaturas entrada/outros"]

PRODUTO_CASE = """
    CASE
     WHEN t.nm_gateway_plan LIKE '%odisseia%' OR LOWER(t.nm_gateway_product) LIKE '%odis%' THEN 'Odisseia'
     WHEN t.nm_gateway_plan='clube-do-livro' THEN 'CDL físico'
     WHEN t.nm_gateway_plan LIKE 'ebooks%clube%' THEN 'CDL ebook/audio'
     WHEN t.nm_gateway_plan='mecenas' OR LOWER(t.nm_gateway_product) LIKE '%mecenas%' THEN 'Mecenas'
     WHEN t.nm_gateway_plan='imersao-cabral' OR LOWER(t.nm_gateway_product) LIKE '%retiro%'
       OR LOWER(t.nm_gateway_product) LIKE '%comitê%' THEN 'Eventos high-ticket'
     WHEN t.nm_gateway_plan='black' AND (t.bl_lifetime_offer OR LOWER(t.nm_gateway_product) LIKE '%vital%') THEN 'Black Vitalício'
     WHEN t.nm_gateway_plan='best' AND (t.bl_lifetime_offer OR LOWER(t.nm_gateway_product) LIKE '%vital%') THEN 'Premium Vitalício'
     WHEN (t.nm_gateway_plan IN ('good','better','supporter') OR t.nm_gateway_plan LIKE 'bp-essencial-combo%')
       AND (t.bl_lifetime_offer OR LOWER(t.nm_gateway_product) LIKE '%vital%') THEN 'Básico/outros Vitalício'
     WHEN t.nm_gateway_plan IN ('black','best') THEN 'Black/Premium recorrente'
     ELSE 'Assinaturas entrada/outros'
    END"""

VENDAS_CTE = f"""
vendas AS (
  SELECT t.id_transaction, t.dt_ordered_at, t.vl_payment_gross vl, t.nm_salesman_email,
    {PRODUTO_CASE} produto,
    REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]','') fone, LOWER(c.nm_email) email
  FROM masterdata.fct_transactions t JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status='approved' AND t.bl_is_renovation=FALSE AND t.bl_is_commercial_channel=TRUE
    AND DATE(t.dt_ordered_at) BETWEEN '{INI}' AND '{{fim_venda}}')"""

CONV_CTE = f"""
conv AS (
  SELECT a.id_approach, a.id_prospect, DATETIME(a.dt_approach_start) dt_ini, LOWER(a.nm_conversation) c,
         REGEXP_REPLACE(z.cd_cleaned_phone_number, r'[^0-9]','') fone, LOWER(z.nm_contact_email) email
  FROM masterdata.dim_zenvia_approaches a JOIN masterdata.dim_zenvia_contacts z USING (id_prospect)
  WHERE DATE(a.dt_approach_start) BETWEEN '{{ini_conv}}' AND '{FIM}' AND a.qt_prospect_interactions > 0)"""

TEMA_FLAGS = ", ".join(f"REGEXP_CONTAINS(c, r'{rx}') t_{k}" for k, rx in TEMAS.items())
TEMA_COUNTIF = ",\n ".join(
    f"COUNTIF(REGEXP_CONTAINS(c, r'{rx}')) {k}, COUNTIF(REGEXP_CONTAINS(c, r'{rx}') AND resp) {k}_r"
    for k, rx in TEMAS.items())


def bq(sql: str) -> list[dict]:
    from google.cloud import bigquery
    df = bigquery.Client(project="bp-datawarehouse").query(sql).to_dataframe()
    return json.loads(df.to_json(orient="records", date_format="iso"))


def ii(v):
    try: return int(float(v)) if v not in (None, "", "null") else 0
    except Exception: return 0

def ff(v):
    try: return round(float(v), 1) if v not in (None, "", "null") else None
    except Exception: return None


Q_SEMANA = f"""
WITH a AS (
  SELECT DATE_TRUNC(DATE(dt_approach_start), WEEK(MONDAY)) semana, id_prospect, id_seller,
         LOWER(nm_conversation) c, qt_prospect_interactions > 0 resp
  FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN '{INI}' AND '{FIM}')
SELECT semana, COUNT(*) abordagens, COUNT(DISTINCT id_prospect) contatos, COUNT(DISTINCT id_seller) vendedores,
 COUNTIF(resp) respondidas,
 {TEMA_COUNTIF}
FROM a GROUP BY 1 ORDER BY 1"""

Q_VENDAS_SEMANA = f"""
SELECT DATE_TRUNC(DATE(t.dt_ordered_at), WEEK(MONDAY)) semana, {PRODUTO_CASE} produto,
       COUNT(*) vendas, ROUND(SUM(t.vl_payment_gross)) receita
FROM masterdata.fct_transactions t
WHERE t.nm_status='approved' AND t.bl_is_renovation=FALSE AND t.bl_is_commercial_channel=TRUE
  AND DATE(t.dt_ordered_at) BETWEEN '{INI}' AND '{FIM}'
GROUP BY 1,2 ORDER BY 1,2"""

# conversa respondida (tema) → compra em 14d
Q_CONVERSAO = f"""
WITH {CONV_CTE.format(ini_conv=INI)},
tema AS (SELECT *, {TEMA_FLAGS} FROM conv),
{VENDAS_CTE.format(fim_venda=FIM_VENDA)},
m AS (
  SELECT tm.id_approach, v.id_transaction, v.produto, v.vl FROM tema tm JOIN vendas v ON tm.fone = v.fone AND LENGTH(tm.fone) >= 10
  WHERE v.dt_ordered_at BETWEEN tm.dt_ini AND DATETIME_ADD(tm.dt_ini, INTERVAL 14 DAY)
  UNION DISTINCT
  SELECT tm.id_approach, v.id_transaction, v.produto, v.vl FROM tema tm JOIN vendas v ON tm.email = v.email AND tm.email LIKE '%@%'
  WHERE v.dt_ordered_at BETWEEN tm.dt_ini AND DATETIME_ADD(tm.dt_ini, INTERVAL 14 DAY)),
por_conv AS (
  SELECT id_approach, COUNT(id_transaction) n_tx, SUM(vl) rec,
         LOGICAL_OR(produto='Odisseia') odi, LOGICAL_OR(produto LIKE 'CDL%') cdl,
         LOGICAL_OR(produto LIKE '%Vitalício') vit, LOGICAL_OR(produto='Black Vitalício') black,
         LOGICAL_OR(produto='Mecenas') mec, LOGICAL_OR(produto='Eventos high-ticket') evt
  FROM m GROUP BY 1),
u AS (
  { " UNION ALL ".join(
      f"SELECT '{k}' tema, tm.id_prospect, p.n_tx, p.rec, p.{ALVO.get(k,'n_tx>0') if k in ALVO else 'n_tx>0'} alvo FROM tema tm LEFT JOIN por_conv p USING(id_approach) WHERE t_{k}"
      if k in ALVO else
      f"SELECT '{k}' tema, tm.id_prospect, p.n_tx, p.rec, p.n_tx>0 alvo FROM tema tm LEFT JOIN por_conv p USING(id_approach) WHERE t_{k}"
      for k in TEMAS) }
  UNION ALL
  SELECT 'todas' tema, tm.id_prospect, p.n_tx, p.rec, p.n_tx>0 alvo FROM tema tm LEFT JOIN por_conv p USING(id_approach))
SELECT tema, COUNT(*) conversas, COUNT(DISTINCT id_prospect) pessoas,
       COUNTIF(n_tx>0) com_venda, ROUND(100*COUNTIF(n_tx>0)/COUNT(*),1) pct_venda,
       COUNTIF(alvo) com_venda_alvo, ROUND(100*COUNTIF(alvo)/COUNT(*),1) pct_venda_alvo,
       ROUND(SUM(rec)) receita_14d
FROM u GROUP BY 1"""

# venda ← teve conversa respondida nos 14 dias anteriores? qual tema?
Q_VENDA_CONVERSA = f"""
WITH {CONV_CTE.format(ini_conv=INI - datetime.timedelta(days=14))},
{VENDAS_CTE.format(fim_venda=FIM)},
m AS (
  SELECT v.id_transaction, cv.c FROM vendas v JOIN conv cv ON v.fone = cv.fone AND LENGTH(v.fone) >= 10
  WHERE cv.dt_ini BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 14 DAY) AND DATETIME_ADD(v.dt_ordered_at, INTERVAL 1 DAY)
  UNION DISTINCT
  SELECT v.id_transaction, cv.c FROM vendas v JOIN conv cv ON v.email = cv.email AND cv.email LIKE '%@%'
  WHERE cv.dt_ini BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 14 DAY) AND DATETIME_ADD(v.dt_ordered_at, INTERVAL 1 DAY)),
por_tx AS (
  SELECT id_transaction, {", ".join(f"LOGICAL_OR(REGEXP_CONTAINS(c, r'{rx}')) {k}" for k, rx in TEMAS.items())}
  FROM m GROUP BY 1)
SELECT v.produto, COUNT(*) vendas, ROUND(SUM(v.vl)) receita,
  COUNTIF(p.id_transaction IS NOT NULL) com_conversa,
  COUNTIF(v.nm_salesman_email='gustavo.koetz@brasilparalelo.com.br') lambda,
  {", ".join(f"COUNTIF(p.{k}) m_{k}" for k in TEMAS)}
FROM vendas v LEFT JOIN por_tx p USING (id_transaction)
GROUP BY 1"""

# matriz tema ofertado → produto comprado (14d)
Q_TEMA_PRODUTO = f"""
WITH {CONV_CTE.format(ini_conv=INI)},
{VENDAS_CTE.format(fim_venda=FIM_VENDA)},
m AS (
  SELECT cv.c, v.id_transaction, v.produto, v.vl FROM conv cv JOIN vendas v ON cv.fone=v.fone AND LENGTH(cv.fone)>=10
  WHERE v.dt_ordered_at BETWEEN cv.dt_ini AND DATETIME_ADD(cv.dt_ini, INTERVAL 14 DAY)
  UNION DISTINCT
  SELECT cv.c, v.id_transaction, v.produto, v.vl FROM conv cv JOIN vendas v ON cv.email=v.email AND cv.email LIKE '%@%'
  WHERE v.dt_ordered_at BETWEEN cv.dt_ini AND DATETIME_ADD(cv.dt_ini, INTERVAL 14 DAY)),
x AS (
  SELECT DISTINCT tema, produto, id_transaction, vl FROM m, UNNEST([
    {", ".join(f"IF(REGEXP_CONTAINS(c, r'{rx}'), '{k}', NULL)" for k, rx in TEMAS.items() if k in ALVO)}]) tema
  WHERE tema IS NOT NULL)
SELECT tema, produto, COUNT(*) vendas, ROUND(SUM(vl)) receita FROM x GROUP BY 1,2"""

Q_STAGES = f"""
WITH a AS (SELECT COALESCE(nm_stage,'(sem etapa)') stage, LOWER(nm_conversation) c
  FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN '{INI}' AND '{FIM}' AND qt_prospect_interactions > 0)
SELECT stage, COUNT(*) conversas, {", ".join(f"COUNTIF(REGEXP_CONTAINS(c, r'{rx}')) {k}" for k, rx in TEMAS.items())}
FROM a GROUP BY 1 ORDER BY 2 DESC LIMIT 8"""

Q_MOTIVOS = f"""
WITH a AS (SELECT COALESCE(nm_closing_reason,'(sem motivo)') motivo, LOWER(nm_conversation) c
  FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN '{INI}' AND '{FIM}' AND qt_prospect_interactions > 0)
SELECT motivo, COUNT(*) conversas, {", ".join(f"COUNTIF(REGEXP_CONTAINS(c, r'{rx}')) {k}" for k, rx in TEMAS.items())}
FROM a GROUP BY 1 ORDER BY 2 DESC LIMIT 8"""

Q_ODI_CO = f"""
WITH a AS (SELECT LOWER(nm_conversation) c FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN '{INI}' AND '{FIM}' AND REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia'))
SELECT COUNT(*) total, COUNTIF(REGEXP_CONTAINS(c,r'clube do livro')) com_cdl, COUNTIF(REGEXP_CONTAINS(c,r'black')) com_black,
  COUNTIF(REGEXP_CONTAINS(c,r'vital[ií]cio')) com_vit, COUNTIF(REGEXP_CONTAINS(c,r'mecenas')) com_mec,
  COUNTIF(NOT REGEXP_CONTAINS(c,r'clube do livro|black|vital[ií]cio|mecenas')) sozinha FROM a"""

Q_ODI_OFERTAS = f"""
SELECT FORMAT_DATE('%Y-%m', DATE(t.dt_ordered_at)) mes, t.nm_gateway_offer oferta, COUNT(*) vendas, ROUND(SUM(t.vl_payment_gross)) receita
FROM masterdata.fct_transactions t
WHERE t.nm_status='approved' AND t.bl_is_renovation=FALSE AND t.bl_is_commercial_channel=TRUE
  AND DATE(t.dt_ordered_at) BETWEEN '{INI}' AND '{FIM}'
  AND (LOWER(t.nm_gateway_product) LIKE '%odis%' OR t.nm_gateway_plan LIKE '%odisseia%')
GROUP BY 1,2 ORDER BY 1, 3 DESC"""

# concentração por vendedor — sem nomes (repo público)
Q_VENDEDORES = f"""
WITH s AS (SELECT nm_salesman_email v, COUNT(*) n, SUM(vl_payment_gross) r FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
    AND DATE(dt_ordered_at) BETWEEN '{INI}' AND '{FIM}' GROUP BY 1),
h AS (SELECT * FROM s WHERE v IS NOT NULL AND v != 'gustavo.koetz@brasilparalelo.com.br')
SELECT (SELECT COUNT(*) FROM h) vendedores, (SELECT ROUND(SUM(r)) FROM h) receita_humanos,
  (SELECT ROUND(SUM(r)) FROM (SELECT r FROM h ORDER BY r DESC LIMIT 10)) top10,
  (SELECT ROUND(APPROX_QUANTILES(r, 2)[OFFSET(1)]) FROM h) mediana_vendedor,
  (SELECT n FROM s WHERE v='gustavo.koetz@brasilparalelo.com.br') lambda_vendas,
  (SELECT ROUND(r) FROM s WHERE v='gustavo.koetz@brasilparalelo.com.br') lambda_receita,
  (SELECT ROUND(SUM(r)) FROM s WHERE v IS NULL) sem_vendedor"""


def build() -> dict:
    print("  série semanal (abordagens + temas)...", flush=True)
    semanas = []
    for r in bq(Q_SEMANA):
        row = {"semana": r["semana"][:10], "abordagens": ii(r["abordagens"]), "contatos": ii(r["contatos"]),
               "vendedores": ii(r["vendedores"]), "respondidas": ii(r["respondidas"]),
               "temas": {k: ii(r[k]) for k in TEMAS}, "temas_resp": {k: ii(r[f"{k}_r"]) for k in TEMAS}}
        semanas.append(row)
    idx = {s["semana"]: s for s in semanas}
    for s in semanas:
        s["vendas"] = {p: {"vendas": 0, "receita": 0.0} for p in PRODUTOS}

    print("  vendas por semana/produto...", flush=True)
    for r in bq(Q_VENDAS_SEMANA):
        s = idx.get(r["semana"][:10])
        if s and r["produto"] in s["vendas"]:
            s["vendas"][r["produto"]] = {"vendas": ii(r["vendas"]), "receita": float(r["receita"] or 0)}

    print("  conversão real por tema (conversa → compra 14d)...", flush=True)
    conversao = {r["tema"]: {"conversas": ii(r["conversas"]), "pessoas": ii(r["pessoas"]),
                             "com_venda": ii(r["com_venda"]), "pct_venda": ff(r["pct_venda"]),
                             "com_venda_alvo": ii(r["com_venda_alvo"]), "pct_venda_alvo": ff(r["pct_venda_alvo"]),
                             "receita_14d": float(r["receita_14d"] or 0)} for r in bq(Q_CONVERSAO)}

    print("  vendas ← conversa prévia...", flush=True)
    venda_conversa = {r["produto"]: {"vendas": ii(r["vendas"]), "receita": float(r["receita"] or 0),
                                     "com_conversa": ii(r["com_conversa"]), "lambda": ii(r["lambda"]),
                                     "mencoes": {k: ii(r[f"m_{k}"]) for k in TEMAS}} for r in bq(Q_VENDA_CONVERSA)}

    print("  matriz tema → produto...", flush=True)
    tema_produto = {}
    for r in bq(Q_TEMA_PRODUTO):
        tema_produto.setdefault(r["tema"], {})[r["produto"]] = {"vendas": ii(r["vendas"]), "receita": float(r["receita"] or 0)}

    print("  etapas, motivos, Odisseia...", flush=True)
    stages = [{"stage": r["stage"], "conversas": ii(r["conversas"]), **{k: ii(r[k]) for k in TEMAS}} for r in bq(Q_STAGES)]
    motivos = [{"motivo": r["motivo"], "conversas": ii(r["conversas"]), **{k: ii(r[k]) for k in TEMAS}} for r in bq(Q_MOTIVOS)]
    odi_co = {k: ii(v) for k, v in bq(Q_ODI_CO)[0].items()}
    odi_ofertas = [{"mes": r["mes"], "oferta": r["oferta"], "vendas": ii(r["vendas"]), "receita": float(r["receita"] or 0)}
                   for r in bq(Q_ODI_OFERTAS)]
    vend = {k: (float(v) if v is not None else 0) for k, v in bq(Q_VENDEDORES)[0].items()}

    # agregados: total e por mês-calendário (com base nas semanas; mês pela segunda-feira é impreciso →
    # usa a série semanal só para totais; mensal vem das mesmas linhas agregadas por semana)
    tot = {
        "abordagens": sum(s["abordagens"] for s in semanas),
        "respondidas": sum(s["respondidas"] for s in semanas),
        "vendedores_max": max((s["vendedores"] for s in semanas), default=0),
        "temas": {k: sum(s["temas"][k] for s in semanas) for k in TEMAS},
        "temas_resp": {k: sum(s["temas_resp"][k] for s in semanas) for k in TEMAS},
        "vendas": {p: sum(s["vendas"][p]["vendas"] for s in semanas) for p in PRODUTOS},
        "receita": {p: sum(s["vendas"][p]["receita"] for s in semanas) for p in PRODUTOS},
    }
    tot["vendas_total"] = sum(tot["vendas"].values())
    tot["receita_total"] = sum(tot["receita"].values())

    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "config": {"ini": INI.isoformat(), "fim": FIM.isoformat(), "produtos": PRODUTOS, "temas": list(TEMAS)},
        "semanas": semanas,
        "total": tot,
        "conversao": conversao,
        "venda_conversa": venda_conversa,
        "tema_produto": tema_produto,
        "stages": stages,
        "motivos": motivos,
        "odisseia": {"coocorrencia": odi_co, "ofertas": odi_ofertas},
        "vendedores": vend,
    }


if __name__ == "__main__":
    push = "--push" in sys.argv
    print(f"Refreshing comercial-abordagens ({INI} → {FIM})...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']}")
        if push:
            subprocess.run(["git", "add", str(OUT)], check=True)
            subprocess.run(["git", "commit", "-m", f"data: comercial-abordagens refresh {HOJE}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✓ pushed to GitHub Pages")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
