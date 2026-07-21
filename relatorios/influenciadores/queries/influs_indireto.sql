-- Vendas INDIRETAS: lead entrou por página/link de parceiro (last tracking
-- contém PARC/INFLU) mas a compra fechou por outro canal (não-ads).
-- Replica a regra do segmento Insider "Influ: venda direta e indireta"
-- (Include last_tracking ~ PARC, Exclude utm_medium ~ ads, Exclude canal Influ).
SELECT
  COALESCE(nm_lead_last_tracking, '')                  AS lead_tracking,
  FORMAT_DATE('%Y-%m', DATE(dt_ordered_at))            AS ano,  -- mês (alias 'ano' mantido p/ refresh.py)
  COALESCE(nm_plan_label, nm_gateway_product, 'outro') AS produto,
  COUNT(*)                                             AS qt,
  ROUND(SUM(vl_payment_gross), 2)                      AS receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND dt_ordered_at >= '2025-01-01'  -- recorte do relatório: 2025 em diante
  AND COALESCE(nm_pptc_tracking_publisher, '') != 'Influencers'
  AND NOT STARTS_WITH(COALESCE(nm_pptc_tracking_name, ''), 'Afiliado')
  AND REGEXP_CONTAINS(UPPER(COALESCE(nm_lead_last_tracking, '')), r'INFLU|PARC')
  AND NOT REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_medium, '')), r'ads')
GROUP BY 1, 2, 3
ORDER BY receita DESC
