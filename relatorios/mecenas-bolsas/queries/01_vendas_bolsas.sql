-- Bolsas Mecenas VENDIDAS por ano × tipo (padrão = assinatura Premium / certificação)
-- Filtro canônico BOLSA (wiki mecenas.md): exclui Solidário/Patrono/Apoiador, order bumps, < R$ 1.000.
-- Regex com `-?` obrigatório: pega "10 Bolsas", "01 Bolsa" e "Mecenas 1 - Bolsas" (hífen, ~700 tx antigas).
-- Ofertas de preço unitário sem contagem no nome (R$ 1188 / R$ 1668) = 1 bolsa.
WITH tx AS (
  SELECT
    t.vl_payment_gross,
    t.id_gateway_customer,
    EXTRACT(YEAR FROM t.dt_ordered_at) AS ano,
    CASE
      WHEN LOWER(t.nm_gateway_offer) LIKE '%r$ 1188%' OR LOWER(t.nm_gateway_offer) LIKE '%r$ 1668%' THEN 1
      ELSE CAST(REGEXP_EXTRACT(LOWER(t.nm_gateway_offer), r'(\d+)\s*-?\s*bolsas?') AS INT64)
    END AS qt_bolsas,
    CASE
      WHEN t.nm_gateway_plan IN ('mecenas_ciencia-politica', 'mecenas_travessia',
                                 'mecenas_metodo-bp', 'mecenas_travessia-familia')
        THEN 'certificacao'
      ELSE 'padrao'
    END AS tipo
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
  ano,
  tipo,
  COUNT(*)                            AS qt_tx,
  SUM(qt_bolsas)                      AS qt_bolsas,
  COUNTIF(qt_bolsas IS NULL)          AS qt_tx_sem_numero,
  ROUND(SUM(IF(qt_bolsas IS NULL, vl_payment_gross, 0)), 2) AS vl_receita_sem_numero,
  ROUND(SUM(vl_payment_gross), 2)     AS vl_receita,
  COUNT(DISTINCT id_gateway_customer) AS qt_contas
FROM tx
GROUP BY ano, tipo
ORDER BY ano, tipo
