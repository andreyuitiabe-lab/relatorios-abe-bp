-- ELS: compradores via UTM com/sem histórico anterior ao início da campanha
-- Resultado: já_eram_clientes | novos_clientes | pct_existentes

WITH buyers AS (
  SELECT DISTINCT t.id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at >= '2025-11-19'
    AND (
      LOWER(t.nm_pptc_utm_campaign) LIKE '%els%'
      OR LOWER(t.nm_pptc_utm_campaign) LIKE '%el_salvador%'
      OR LOWER(t.nm_pptc_utm_campaign) LIKE '%el-salvador%'
    )
),

historico AS (
  SELECT t.id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN buyers b ON b.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at < '2025-11-19'
  GROUP BY 1
)

SELECT
  COUNTIF(h.id_gateway_customer IS NOT NULL)                                       AS ja_eram_clientes,
  COUNTIF(h.id_gateway_customer IS NULL)                                            AS novos_clientes,
  ROUND(COUNTIF(h.id_gateway_customer IS NOT NULL) / COUNT(*) * 100, 1)             AS pct_existentes
FROM buyers b
LEFT JOIN historico h USING (id_gateway_customer)
