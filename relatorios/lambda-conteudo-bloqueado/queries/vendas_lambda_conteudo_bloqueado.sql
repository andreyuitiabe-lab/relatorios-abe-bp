-- Vendas Lambda (link Gustavo Koetz / C0113) de leads da campanha "Conteúdo bloqueado"
-- e onde cada venda foi parar no modelo dtm_seller_conversion_rate.
--
-- Contexto (jul/2026): leads CB são conduzidos pela Lambda (IA), mas os deals CB no
-- Pipedrive ficam com wellington.santos / stage "9. OUTROS". A venda C0113 entra em
-- OUTRO deal da mesma pessoa (flavio.barretto, gustavo.koetz etc.) — nunca no deal CB.
-- Identificação dos leads CB: nm_label/nm_deal_source = 'Conteúdo bloqueado' (desde
-- 20/07/2026) OU nm_title LIKE 'UPSELL |%' (título padronizado, cobre os sem campanha).

WITH cb_leads AS (
  SELECT
    id_pipedrive_deal AS cb_deal,
    LOWER(nm_person_email) AS email,
    REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]', '') AS tel
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate`
  WHERE nm_label = 'Conteúdo bloqueado'
     OR nm_deal_source = 'Conteúdo bloqueado'
     OR (nm_title LIKE 'UPSELL |%' AND DATE(dt_created_at) >= '2026-07-01')
),

lambda_sales AS (
  -- regra canônica de venda Lambda (ver wiki fluxo-comercial.md)
  SELECT
    t.id_transaction,
    DATE(t.dt_ordered_at) AS dia,
    t.vl_payment_gross AS vl,
    t.nm_gateway_plan AS plano,
    LOWER(c.nm_email) AS email,
    REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]', '') AS tel
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND ( UPPER(t.nm_pptc_tracking_name) LIKE '%C0113%'
       OR LOWER(t.nm_gateway_product) LIKE '%lambda%'
       OR LOWER(t.nm_gateway_offer) LIKE '%lambda%' )
    AND DATE(t.dt_ordered_at) >= '2026-07-15'
),

-- match por email e telefone em joins separados (OR no ON vira cross-join)
matched AS (
  SELECT s.*, l.cb_deal
  FROM lambda_sales s
  JOIN cb_leads l ON s.email = l.email AND s.email IS NOT NULL AND s.email != ''
  UNION DISTINCT
  SELECT s.*, l.cb_deal
  FROM lambda_sales s
  JOIN cb_leads l ON s.tel = l.tel AND s.tel IS NOT NULL AND s.tel != ''
),

-- todas as transações presentes no modelo, com o deal que as carrega
model_flat AS (
  SELECT m.id_pipedrive_deal, m.nm_salesman_email, m.nm_stage, ct.id_transaction
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate` m,
    UNNEST(m.arr_st_commercial_transactions) ct
  UNION DISTINCT
  SELECT m2.id_pipedrive_deal, m2.nm_salesman_email, m2.nm_stage, m2.id_transaction
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate` m2
  WHERE m2.id_transaction IS NOT NULL
  UNION DISTINCT
  SELECT m3.id_pipedrive_deal, m3.nm_salesman_email, m3.nm_stage, m3.id_mkt_transaction
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate` m3
  WHERE m3.id_mkt_transaction IS NOT NULL
)

SELECT
  m.id_transaction,
  m.dia,
  m.vl,
  m.plano,
  m.cb_deal AS deal_conteudo_bloqueado,
  COALESCE(mf.id_pipedrive_deal, '(fora do modelo)') AS deal_atribuido,
  COALESCE(mf.nm_salesman_email, '-') AS vendedor_atribuido,
  COALESCE(mf.nm_stage, '-') AS stage_atribuido
FROM matched m
LEFT JOIN model_flat mf ON m.id_transaction = mf.id_transaction
ORDER BY m.dia, m.id_transaction
