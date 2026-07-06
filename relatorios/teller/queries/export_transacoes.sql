WITH base AS (
  SELECT DATE(dt_ordered_at) dt_pedido, FORMAT_DATE('%Y-%m', DATE(dt_ordered_at)) mes,
    id_gateway_customer, dt_ordered_at, nm_gateway_plan, nm_gateway_product, nm_plan_label,
    vl_payment_gross, nm_pptc_utm_campaign, bl_is_commercial_channel,
    (nm_gateway_plan='teller') AS bl_produto_teller,
    REGEXP_CONTAINS(LOWER(nm_pptc_utm_campaign), r'(^|[^a-z])tlr([^a-z]|$)|tlr12') AS bl_campanha_teller
  FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='2026-01-01'
    AND (nm_gateway_plan='teller'
         OR REGEXP_CONTAINS(LOWER(nm_pptc_utm_campaign), r'(^|[^a-z])tlr([^a-z]|$)|tlr12'))
),
subs AS (SELECT id_gateway_customer,dt_started_at,dt_expires_in FROM masterdata.dim_subscriptions
         WHERE nm_type='paid' AND (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%')),
vital AS (SELECT DISTINCT id_gateway_customer,dt_ordered_at dt_vital FROM masterdata.fct_transactions
          WHERE nm_status='approved' AND bl_lifetime_offer AND LOWER(nm_gateway_product) NOT LIKE '%teller%')
SELECT b.dt_pedido, b.mes, b.id_gateway_customer,
  CASE WHEN b.bl_produto_teller AND b.bl_campanha_teller THEN 'produto+campanha'
       WHEN b.bl_produto_teller THEN 'produto' ELSE 'campanha' END lente,
  b.nm_gateway_plan, b.nm_gateway_product, b.nm_plan_label,
  CASE WHEN b.bl_is_commercial_channel THEN 'comercial' ELSE 'digital' END canal,
  ROUND(b.vl_payment_gross,2) valor, b.nm_pptc_utm_campaign utm_campaign,
  CASE WHEN LOWER(b.nm_pptc_utm_campaign) LIKE '%membro%' OR LOWER(b.nm_pptc_utm_campaign) LIKE '%cross%' THEN 'membros_crosssell'
       WHEN LOWER(b.nm_pptc_utm_campaign) LIKE '%recupera%' THEN 'recuperacao'
       WHEN b.bl_campanha_teller THEN 'aquisicao_geral' ELSE '' END intencao_campanha,
  CASE WHEN (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=b.id_gateway_customer AND s.dt_started_at<b.dt_ordered_at AND s.dt_expires_in>=b.dt_ordered_at)>0
            OR (SELECT COUNT(1) FROM vital v WHERE v.id_gateway_customer=b.id_gateway_customer AND v.dt_vital<b.dt_ordered_at)>0 THEN 'membro'
       WHEN (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=b.id_gateway_customer AND s.dt_started_at<b.dt_ordered_at)>0 THEN 'ex_membro'
       ELSE 'nao_membro' END perfil_comprador
FROM base b ORDER BY b.dt_pedido, b.id_gateway_customer
