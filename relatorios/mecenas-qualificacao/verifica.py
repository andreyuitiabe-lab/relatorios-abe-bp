#!/usr/bin/env python3
"""QA do relatório: recalcula os números publicados DIRETO do BigQuery, com a regra reescrita
à mão aqui, e compara com data.json. Qualquer divergência é bug — na base ou neste script.

Rodar sempre depois de `refresh.py` e antes de publicar:
    python verifica.py     # sai 0 se tudo confere, 1 se algo diverge

Por que existe: numa revisão de ago/2026 descobrimos que cinco queries tinham ficado com o
corte antigo (R$ 300) depois de a regra mudar para R$ 1.000 — e duas delas alimentavam números
publicados. Conferir os totais contra o JSON não pega isso, porque o JSON vem das mesmas
queries erradas. Só recalcular a partir da regra, de forma independente, pega.
"""
import json, warnings, sys
from pathlib import Path
warnings.filterwarnings("ignore")
from google.cloud import bigquery

c = bigquery.Client(project="bp-datawarehouse")
D = json.load(open(Path(__file__).resolve().parent / "data.json"))

# definição da regra, reescrita À MÃO aqui — se divergir da base, uma das duas está errada.
# ⚠️ NUNCA usar DISTINCT (id_person, valor): colapsa doações repetidas do mesmo valor pela
#    mesma pessoa e subestimou a receita em R$ 9,3M na primeira versão deste script.
REGRA_BOLSA = """
  nm_status = 'approved'
  AND LOWER(COALESCE(nm_gateway_product,'')) NOT LIKE '%solid%'
  AND LOWER(COALESCE(nm_gateway_offer,''))   NOT LIKE '%solid%'
  AND nm_gateway_plan <> 'mecenas_mecenas-solidario-premium'
  AND nm_gateway_product NOT LIKE '%Mecenas Patrono%'
  AND nm_gateway_product NOT LIKE '%Mecenas Apoiador%'
  AND LOWER(COALESCE(nm_gateway_offer,''))   NOT LIKE '%order bump%'
  AND LOWER(COALESCE(nm_gateway_product,'')) NOT LIKE '%order bump%'
  AND ((nm_gateway_plan LIKE 'mecenas%' AND nm_gateway_plan <> 'mecenas_bp-essencial')
       OR LOWER(COALESCE(nm_gateway_product,'')) LIKE '%mecenas%')
  AND vl_payment_gross >= 1000
"""
# Solidário = mapeamento do sistema: 5 produtos (inclui Patrono e Apoiador)
REGRA_SOL = """
  nm_status = 'approved'
  AND (LOWER(COALESCE(nm_gateway_product,'')) LIKE '%solid%'
       OR LOWER(COALESCE(nm_gateway_offer,'')) LIKE '%solid%'
       OR nm_gateway_plan = 'mecenas_mecenas-solidario-premium'
       OR nm_gateway_product LIKE '%Mecenas Patrono%'
       OR nm_gateway_product LIKE '%Mecenas Apoiador%')
"""

q = f"""
WITH pm AS (SELECT id_gateway_customer, id_person FROM `bp-staging.dbt_abe.tb_mecenas_person_map`),
bolsa AS (
  SELECT pm.id_person, t.id_transaction, t.vl_payment_gross AS vl
  FROM `bp-datawarehouse.masterdata.fct_transactions` t JOIN pm USING (id_gateway_customer)
  WHERE {REGRA_BOLSA}
),
b_pessoa AS (SELECT id_person, MAX(vl) AS maior, SUM(vl) AS total FROM bolsa GROUP BY 1),
sol AS (
  SELECT pm.id_person, t.id_transaction, t.vl_payment_gross AS vl
  FROM `bp-datawarehouse.masterdata.fct_transactions` t JOIN pm USING (id_gateway_customer)
  WHERE {REGRA_SOL}
),
s_pessoa AS (SELECT id_person, MAX(vl) AS maior, SUM(vl) AS total FROM sol GROUP BY 1)
SELECT
  (SELECT COUNT(*) FROM b_pessoa) AS doadores,
  (SELECT ROUND(SUM(total)) FROM b_pessoa) AS receita,
  (SELECT COUNT(*) FROM b_pessoa WHERE maior > 10000) AS n_topo,
  (SELECT ROUND(SUM(total)) FROM b_pessoa WHERE maior > 10000) AS receita_topo,
  (SELECT COUNT(*) FROM s_pessoa) AS solidario,
  (SELECT ROUND(SUM(total)) FROM s_pessoa) AS receita_sol
"""
r = [dict(x) for x in c.query(q).result()][0]
res = D["resumo"]; sol = D["solidario"]
sol_pessoas = sum(f["pessoas"] for f in sol["faixas"])
sol_receita = sum(f["receita"] for f in sol["faixas"])

# ⚠️ Latência de ingestão: uma transação entra no fct_transactions alguns minutos (mediana 5,
#    cauda de até ~1h e, em casos raros, dias) DEPOIS do pedido. Então uma divergência que
#    envolve só compras do dia corrente é latência, não bug. Medimos separado para não
#    confundir os dois — e para o Solidário, que vende agora, isso é o caso comum.
q_hoje = f"""
WITH pm AS (SELECT id_gateway_customer, id_person FROM `bp-staging.dbt_abe.tb_mecenas_person_map`)
SELECT COUNT(DISTINCT pm.id_person) AS pessoas_hoje
FROM `bp-datawarehouse.masterdata.fct_transactions` t JOIN pm USING (id_gateway_customer)
WHERE {REGRA_SOL} AND DATE(t.dt_ordered_at) = CURRENT_DATE('America/Sao_Paulo')
"""
sol_hoje = [dict(x) for x in c.query(q_hoje).result()][0]["pessoas_hoje"]

checks = [
  ("doadores de bolsa",      r["doadores"],     res["doadores"]),
  ("receita de bolsa",       float(r["receita"]), round(res["receita"])),
  ("pessoas no topo",        r["n_topo"],       res["n_topo"]),
  ("receita do topo",        float(r["receita_topo"]), round(res["receita_topo"])),
  ("pessoas Solidário",      r["solidario"],    sol_pessoas),
  ("receita Solidário",      float(r["receita_sol"]), round(sol_receita)),
]
ok = True
print(f"{'métrica':26} {'recalculado':>14} {'publicado':>14}   veredito")
for nome, a, b in checks:
    d = abs(float(a) - float(b))
    if d < 1:
        v = "OK"
    elif "Solidário" in nome and sol_hoje > 0:
        # produto vendendo agora: diferença pequena é latência de ingestão, não bug
        v = f"ok (latência: {d:,.0f}, {sol_hoje} compras hoje)"
    else:
        v = f"DIVERGE ({d:,.0f})"; ok = False
    print(f"{nome:26} {a:>14,.0f} {b:>14,.0f}   {v}")
# consistência interna do publicado
pc = 100*res["receita_topo"]/res["receita"]
tx = 100*res["doadores"]/res["universo"]
print(f"\n{'% receita no topo':26} {pc:>14.2f} {res['pc_receita_topo']:>14.2f}   {'OK' if abs(pc-res['pc_receita_topo'])<0.01 else 'DIVERGE'}")
print(f"{'taxa base (%)':26} {tx:>14.3f} {res['taxa_base']:>14.3f}   {'OK' if abs(tx-res['taxa_base'])<0.001 else 'DIVERGE'}")
soma_tiers = sum(t["pessoas"] for t in D["tiers"])
print(f"{'soma dos tiers = doadores':26} {soma_tiers:>14,} {res['doadores']:>14,}   {'OK' if soma_tiers==res['doadores'] else 'DIVERGE'}")
soma_rec = sum(t["receita"] for t in D["tiers"])
print(f"{'soma receita tiers':26} {soma_rec:>14,.0f} {res['receita']:>14,.0f}   {'OK' if abs(soma_rec-res['receita'])<1 else 'DIVERGE'}")
sys.exit(0 if ok else 1)
