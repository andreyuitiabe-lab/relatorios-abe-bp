-- Série diária de vendas por grupo de canal (2025-08-01 →)
-- Grupos via nm_pptc_tracking_publisher; comercial via bl_is_commercial_channel
SELECT
  DATE(dt_ordered_at) AS dia,
  COUNT(*) AS tx_total,
  ROUND(SUM(vl_payment_gross)) AS receita_total,
  COUNTIF(bl_is_commercial_channel) AS tx_comercial,
  ROUND(SUM(IF(bl_is_commercial_channel, vl_payment_gross, 0))) AS receita_comercial,
  COUNTIF(NOT bl_is_commercial_channel) AS tx_digital,
  ROUND(SUM(IF(NOT bl_is_commercial_channel, vl_payment_gross, 0))) AS receita_digital,
  COUNTIF(nm_pptc_tracking_publisher IN ('Facebook Ads', 'Adwords')) AS tx_ads,
  ROUND(SUM(IF(nm_pptc_tracking_publisher IN ('Facebook Ads', 'Adwords'), vl_payment_gross, 0))) AS receita_ads,
  COUNTIF(nm_pptc_tracking_publisher = 'YouTube') AS tx_youtube,
  ROUND(SUM(IF(nm_pptc_tracking_publisher = 'YouTube', vl_payment_gross, 0))) AS receita_youtube,
  COUNTIF(nm_pptc_tracking_publisher IN ('Organic', 'Own Site')) AS tx_organico,
  ROUND(SUM(IF(nm_pptc_tracking_publisher IN ('Organic', 'Own Site'), vl_payment_gross, 0))) AS receita_organico,
  COUNTIF(nm_pptc_tracking_publisher IN ('E-mail', 'Message Service')) AS tx_crm,
  ROUND(SUM(IF(nm_pptc_tracking_publisher IN ('E-mail', 'Message Service'), vl_payment_gross, 0))) AS receita_crm,
  COUNTIF(bl_is_first_subscription_transaction) AS tx_primeira_compra
FROM masterdata.fct_transactions
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND DATE(dt_ordered_at) BETWEEN '2025-08-01' AND '2026-08-20'
GROUP BY 1
ORDER BY 1
