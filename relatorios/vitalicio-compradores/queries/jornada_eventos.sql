-- Jornada dos compradores de vitalício da BNO26 na fct_leads_events: eventos dos 30 dias antes da
-- compra até a compra, em qualquer e-mail da pessoa (identity graph).
-- Disparos (*_delivered, blocked, dropped, journey_*) não entram como linha: viram contagem em
-- eventos agregados com nm_event = 'disparos_<canal>'. Sem PII na saída.
-- Parâmetros: {ini_bno26} {fim_bno26} {ini_eventos}

WITH vit AS (
  SELECT
    t.id_transaction,
    t.dt_ordered_at,
    t.bl_is_commercial_channel,
    LOWER(TRIM(c.nm_email)) AS nm_email
  FROM `bp-datawarehouse.masterdata.fct_transactions` AS t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` AS c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.bl_lifetime_offer = TRUE
    AND DATE(t.dt_ordered_at) BETWEEN '{ini_bno26}' AND '{fim_bno26}'
    AND (
      t.nm_gateway_plan IN ('good', 'better', 'best', 'black')
      OR LOWER(t.nm_gateway_product) LIKE '%vital%'
    )
    AND NOT REGEXP_CONTAINS(t.nm_gateway_plan,
      r'^(livro-odisseia|odisseia-|clube-do-livro|black-clube-do-livro|ebooks-|analises-clube-livro|educacao-literaria|colecao-brasil-a-ultima-cruzada|teller$)')
    AND NOT LOWER(t.nm_gateway_product) LIKE '%membro fundador%'
),

emails AS (
  SELECT DISTINCT v.id_transaction, dpi2.nm_identifier AS nm_email
  FROM vit AS v
  INNER JOIN `bp-datawarehouse.masterdata.dim_person_identity` AS dpi
    ON dpi.nm_identifier_type = 'email' AND dpi.nm_identifier = v.nm_email
  INNER JOIN `bp-datawarehouse.masterdata.dim_person_identity` AS dpi2
    ON dpi2.id_person = dpi.id_person AND dpi2.nm_identifier_type = 'email'
  UNION DISTINCT
  SELECT id_transaction, nm_email FROM vit WHERE nm_email IS NOT NULL
),

ev AS (
  SELECT
    e.id_transaction,
    f.*
  FROM `bp-datawarehouse.datamart.fct_leads_events` AS f
  INNER JOIN emails AS e ON LOWER(f.nm_email) = e.nm_email
  WHERE f.dt_event_created_at >= DATETIME '{ini_eventos}'
    AND f.dt_event_created_at < DATETIME_ADD(DATETIME '{fim_bno26}', INTERVAL 1 DAY)
),

janela AS (
  SELECT ev.*, v.dt_ordered_at, v.bl_is_commercial_channel,
    REGEXP_CONTAINS(ev.nm_event, r'_delivered$|^blocked|^dropped|^journey_') AS bl_disparo,
    CONCAT('disparos_', REGEXP_EXTRACT(ev.nm_event, r'^([a-z]+)')) AS nm_disparo
  FROM ev
  INNER JOIN vit AS v USING (id_transaction)
  WHERE ev.dt_event_created_at >= DATETIME_SUB(v.dt_ordered_at, INTERVAL 30 DAY)
    AND ev.dt_event_created_at <= DATETIME_ADD(v.dt_ordered_at, INTERVAL 5 MINUTE)
)

-- eventos de ação / marco (uma linha por evento)
SELECT
  id_transaction,
  bl_is_commercial_channel,
  dt_ordered_at,
  dt_event_created_at,
  DATETIME_DIFF(dt_ordered_at, dt_event_created_at, MINUTE) / 1440 AS vl_dias_antes,
  nm_source,
  nm_event_type,
  nm_event,
  nm_channel,
  arr_crm_properties.nm_campaign AS nm_crm_campaign,
  arr_registration_properties.nm_tag AS nm_reg_tag,
  arr_registration_properties.nm_reg_utm_source AS nm_reg_utm_source,
  arr_zenvia_properties.nm_lead_source AS nm_zenvia_lead_source,
  arr_zenvia_properties.nm_sales_team AS nm_zenvia_team,
  arr_zenvia_properties.nm_latest_lead_product_detail AS nm_zenvia_produto,
  arr_zenvia_properties.qt_seller_messages AS qt_zenvia_msg_vendedor,
  arr_zenvia_properties.qt_prospect_messages AS qt_zenvia_msg_lead,
  arr_pipedrive_properties.nm_lead_type AS nm_pd_lead_type,
  arr_pipedrive_properties.nm_transaction_trigger AS nm_pd_trigger,
  arr_pipedrive_properties.nm_pipeline AS nm_pd_pipeline,
  arr_payment_properties.nm_gateway_product AS nm_pay_produto,
  arr_payment_properties.bl_lifetime_offer AS bl_pay_vitalicio,
  arr_payment_properties.bl_is_commercial_channel AS bl_pay_comercial,
  arr_payment_properties.vl_payment_gross AS vl_pay,
  arr_engagement_properties.nm_playlist AS nm_playlist,
  arr_engagement_properties.vl_watch_time_seconds AS vl_watch_s
FROM janela
WHERE NOT bl_disparo

UNION ALL

-- disparos: só contagem por pessoa × canal × campanha
SELECT
  id_transaction,
  ANY_VALUE(bl_is_commercial_channel),
  ANY_VALUE(dt_ordered_at),
  MAX(dt_event_created_at),
  NULL,
  'crm',
  'disparo',
  nm_disparo,
  NULL,
  nm_campaign,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
  COUNT(*),
  NULL, NULL
FROM (SELECT *, arr_crm_properties.nm_campaign AS nm_campaign FROM janela WHERE bl_disparo)
GROUP BY id_transaction, nm_disparo, nm_campaign
