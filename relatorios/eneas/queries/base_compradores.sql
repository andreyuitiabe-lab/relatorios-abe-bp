-- Base de compradores da campanha Enéas (ENE)
-- Atribuição: união tracking_name ∪ utm_campaign ∪ utm_content ∪ lead_last_tracking
-- (método validado na ELS — UTM sozinho subconta; ver els-analise.md)
CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_ene_compradores_tx` AS
SELECT
  t.id_transaction,
  t.id_gateway_customer,
  t.dt_ordered_at,
  t.vl_payment_gross,
  t.nm_plan_label,
  t.nm_gateway_product,
  t.nm_gateway_plan,
  t.bl_lifetime_offer,
  t.nm_payment_method,
  t.qt_installments,
  t.nm_pptc_tracking_name,
  t.nm_pptc_utm_campaign,
  t.bl_is_commercial_channel,
  t.nm_salesman,
  CASE
    WHEN UPPER(COALESCE(t.nm_pptc_tracking_name, '')) LIKE '%C0113%'
      THEN 'Comercial — Lambda (IA)'
    WHEN STARTS_WITH(COALESCE(t.nm_pptc_tracking_name, ''), 'Comercial_')
      OR t.bl_is_commercial_channel
      THEN 'Comercial — humano'
    WHEN t.nm_pptc_tracking_name LIKE '%[FB+IG]%'
      THEN 'Meta Ads'
    WHEN t.nm_pptc_tracking_name LIKE '%[PMAX]%'
      THEN 'Google PMax'
    WHEN t.nm_pptc_tracking_name LIKE '%[REDES SOCIAIS]%'
      THEN 'Redes sociais (orgânico)'
    WHEN t.nm_pptc_tracking_name LIKE '%[PORTAL]%'
      OR t.nm_pptc_tracking_name LIKE '%[PROGRAMAS]%'
      THEN 'Portal / site'
    WHEN t.nm_pptc_tracking_name LIKE '%[E-MAIL]%'
      OR LOWER(COALESCE(t.nm_pptc_utm_campaign, '')) LIKE 'jornada%'
      THEN 'CRM (e-mail/jornada)'
    WHEN t.nm_pptc_tracking_name LIKE '%[IN-APP]%'
      THEN 'In-app'
    WHEN t.nm_pptc_tracking_name LIKE '%[YT]%'
      THEN 'YouTube'
    ELSE COALESCE(t.nm_pptc_tracking_publisher, 'Outros')
  END AS nm_canal,
  REGEXP_CONTAINS(COALESCE(t.nm_pptc_tracking_name, ''), r'\[LEAD\]') AS bl_compra_na_lp_cadastro
FROM `bp-datawarehouse.masterdata.fct_transactions` t
WHERE t.dt_ordered_at >= '2026-07-28'
  AND t.nm_status = 'approved'
  AND t.bl_is_renovation = FALSE
  AND (
    REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_tracking_name, '')), r'\[ene\]|eneas')
    OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_utm_campaign, '')), r'\[ene\]|(^|_)ene(_|$)|eneas')
    OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_utm_content, '')), r'\[ene\]|eneas')
    OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_lead_last_tracking, '')), r'\[ene\]|eneas')
  );
