-- ELS: vendas por canal e produto
-- Canal inferido de nm_pptc_utm_source / bl_is_commercial_channel

SELECT
  CASE
    WHEN t.bl_is_commercial_channel = TRUE                        THEN 'Comercial'
    WHEN LOWER(t.nm_pptc_utm_source) LIKE '%facebook%'
      OR LOWER(t.nm_pptc_utm_source) LIKE '%instagram%'           THEN 'Meta Ads'
    WHEN t.nm_pptc_utm_source IS NULL
      OR LOWER(t.nm_pptc_utm_source) IN ('', 'direct', 'youtube') THEN 'Orgânico/Live'
    WHEN LOWER(t.nm_pptc_utm_source) LIKE '%crm%'
      OR LOWER(t.nm_pptc_utm_source) LIKE '%insider%'             THEN 'CRM'
    ELSE 'Outros'
  END                                AS canal,
  t.nm_gateway_plan                  AS plano,
  COUNT(*)                           AS transacoes,
  SUM(t.vl_payment_gross)            AS receita,
  ROUND(AVG(t.vl_payment_gross), 0)  AS ticket_medio
FROM `bp-datawarehouse.masterdata.fct_transactions` t
WHERE t.nm_status = 'approved'
  AND t.bl_is_renovation = FALSE
  AND t.dt_ordered_at >= '2025-11-19'
  AND (
    LOWER(t.nm_pptc_utm_campaign) LIKE '%els%'
    OR LOWER(t.nm_pptc_utm_campaign) LIKE '%el_salvador%'
    OR LOWER(t.nm_pptc_utm_campaign) LIKE '%el-salvador%'
  )
GROUP BY canal, plano
ORDER BY receita DESC
