-- Tentativas de compra ENE que falharam (todas as transações, não só aprovadas)
CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_ene_tentativas` AS
SELECT
  t.id_transaction,
  t.id_gateway_customer,
  t.dt_ordered_at,
  t.nm_status,
  t.vl_payment_gross,
  t.nm_plan_label,
  t.nm_payment_method,
  t.nm_error_category,
  t.qt_installments,
  UPPER(COALESCE(t.nm_pptc_tracking_name, '')) LIKE '%C0113%' AS bl_lambda,
  STARTS_WITH(COALESCE(t.nm_pptc_tracking_name, ''), 'Comercial_')
    OR t.bl_is_commercial_channel AS bl_comercial,
  LOWER(c.nm_email) AS nm_email
FROM `bp-datawarehouse.masterdata.fct_transactions` t
LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
WHERE t.dt_ordered_at >= '2026-07-28'
  AND t.bl_is_renovation = FALSE
  AND (
    REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_tracking_name, '')), r'\[ene\]|eneas')
    OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_utm_campaign, '')), r'\[ene\]|(^|_)ene(_|$)|eneas')
    OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_utm_content, '')), r'\[ene\]|eneas')
    OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_lead_last_tracking, '')), r'\[ene\]|eneas')
  );
