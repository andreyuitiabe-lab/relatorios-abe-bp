-- Bolsas VENDIDAS × assinaturas DISTRIBUÍDAS por produto entregue ao beneficiário.
-- Venda: produto derivado do plano da transação (mecenas_<certificação> ou padrão = Premium).
-- Distribuição: produto derivado do plano da assinatura do beneficiário.
-- "Assinatura Premium" agrega os planos de assinatura (best/GBB, legados patriota/núcleo/
-- bp-select/fraterno/better/good/black, teller, bolsa-mecenas-*); "Outras certificações"
-- agrega cursos distribuídos que nunca foram vendidos como bolsa (Bitcoin, Rússia etc.).
WITH vendas AS (
  SELECT
    CASE t.nm_gateway_plan
      WHEN 'mecenas_ciencia-politica'  THEN 'Certificação Ciência Política'
      WHEN 'mecenas_travessia'         THEN 'Certificação Travessia'
      WHEN 'mecenas_metodo-bp'         THEN 'Certificação Método BP'
      WHEN 'mecenas_travessia-familia' THEN 'Certificação Travessia da Família'
      ELSE 'Assinatura Premium'
    END AS produto,
    CASE
      WHEN LOWER(t.nm_gateway_offer) LIKE '%r$ 1188%' OR LOWER(t.nm_gateway_offer) LIKE '%r$ 1668%' THEN 1
      ELSE CAST(REGEXP_EXTRACT(LOWER(t.nm_gateway_offer), r'(\d+)\s*-?\s*bolsas?') AS INT64)
    END AS qt_bolsas,
    t.vl_payment_gross
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status = 'approved'
    AND LOWER(COALESCE(t.nm_gateway_product, '')) NOT LIKE '%solid%'
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%solid%'
    AND t.nm_gateway_plan <> 'mecenas_mecenas-solidario-premium'
    AND COALESCE(t.nm_gateway_product, '') NOT LIKE '%Mecenas Patrono%'
    AND COALESCE(t.nm_gateway_product, '') NOT LIKE '%Mecenas Apoiador%'
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
    AND LOWER(COALESCE(t.nm_gateway_product, '')) NOT LIKE '%order bump%'
    AND ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
      OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
    AND t.vl_payment_gross >= 1000
),

vendas_agg AS (
  SELECT
    produto,
    SUM(qt_bolsas)                  AS qt_bolsas_vendidas,
    ROUND(SUM(vl_payment_gross), 2) AS vl_receita
  FROM vendas
  GROUP BY produto
),

dist AS (
  SELECT
    CASE nm_plan
      WHEN 'ciencia-politica'  THEN 'Certificação Ciência Política'
      WHEN 'travessia'         THEN 'Certificação Travessia'
      WHEN 'metodo-bp'         THEN 'Certificação Método BP'
      WHEN 'travessia-familia' THEN 'Certificação Travessia da Família'
      WHEN 'bitcoin'           THEN 'Outras certificações'
      WHEN 'funil-bitcoin'     THEN 'Outras certificações'
      WHEN 'russia'            THEN 'Outras certificações'
      WHEN 'anjos-demonios'    THEN 'Outras certificações'
      ELSE 'Assinatura Premium'
    END AS produto,
    (nm_status IN ('active', 'wo renewal')
      AND dt_started_at <= CURRENT_DATETIME()
      AND dt_expires_in >= CURRENT_DATETIME()) AS bl_vigente
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_create_reason_type = 'mecenas'
     OR nm_type = 'donator'
     OR nm_plan LIKE 'bolsa-mecenas%'
),

dist_agg AS (
  SELECT
    produto,
    COUNT(*)            AS qt_assinaturas_distribuidas,
    COUNTIF(bl_vigente) AS qt_vigentes
  FROM dist
  GROUP BY produto
)

SELECT
  COALESCE(v.produto, d.produto)               AS produto,
  COALESCE(v.qt_bolsas_vendidas, 0)            AS qt_bolsas_vendidas,
  COALESCE(v.vl_receita, 0)                    AS vl_receita,
  COALESCE(d.qt_assinaturas_distribuidas, 0)   AS qt_assinaturas_distribuidas,
  COALESCE(d.qt_vigentes, 0)                   AS qt_vigentes
FROM vendas_agg v
FULL JOIN dist_agg d USING (produto)
ORDER BY qt_bolsas_vendidas DESC, qt_assinaturas_distribuidas DESC
