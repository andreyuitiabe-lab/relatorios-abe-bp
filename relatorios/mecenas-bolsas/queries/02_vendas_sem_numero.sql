-- Vendas Mecenas SEM número de bolsas no nome da oferta (não entram na contagem principal).
-- Estimativa por preço unitário: R$ 1.668 (cheia) a R$ 1.188 (desconto).
-- Grupos conhecidos: Funding BP TV (R$ 500k, abr/2024), plano mecenas original 2020-21
-- (R$ 5.880 / R$ 2.940 c/ 50% off), Comercial - Mecenas - Genérico (negociado caso a caso).
WITH tx AS (
  SELECT
    COALESCE(t.nm_gateway_offer, '(oferta NULL)') AS oferta,
    t.vl_payment_gross,
    CASE
      WHEN LOWER(t.nm_gateway_offer) LIKE '%r$ 1188%' OR LOWER(t.nm_gateway_offer) LIKE '%r$ 1668%' THEN 1
      ELSE CAST(REGEXP_EXTRACT(LOWER(t.nm_gateway_offer), r'(\d+)\s*-?\s*bolsas?') AS INT64)
    END AS qt_bolsas
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
)

SELECT
  oferta,
  COUNT(*)                        AS qt_tx,
  ROUND(SUM(vl_payment_gross), 2) AS vl_receita,
  SUM(CAST(FLOOR(vl_payment_gross / 1668) AS INT64)) AS qt_bolsas_est_min,
  SUM(CAST(FLOOR(vl_payment_gross / 1188) AS INT64)) AS qt_bolsas_est_max
FROM tx
WHERE qt_bolsas IS NULL
GROUP BY oferta
ORDER BY vl_receita DESC
