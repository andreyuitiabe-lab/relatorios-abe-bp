-- Como começou a conversa na Zenvia dos compradores de vitalício da BNO26 (conversas iniciadas nos
-- 30 dias antes da compra). Traz as 4 primeiras interações de cada conversa; o refresh.py classifica
-- a origem pelo texto que a pessoa mandou ao chatbot (Zenvia Flow) e só grava agregados.
-- ⚠️ O texto tem dado pessoal: nunca salvar a saída crua no repo.
-- Parâmetros: {ini_bno26} {fim_bno26}

WITH vit AS (
  SELECT t.id_transaction, t.dt_ordered_at, t.bl_is_commercial_channel, LOWER(TRIM(c.nm_email)) nm_email
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status='approved' AND NOT t.bl_is_renovation AND t.bl_lifetime_offer
    AND DATE(t.dt_ordered_at) BETWEEN '{ini_bno26}' AND '{fim_bno26}'
    AND (t.nm_gateway_plan IN ('good','better','best','black') OR LOWER(t.nm_gateway_product) LIKE '%vital%')
    AND NOT REGEXP_CONTAINS(t.nm_gateway_plan, r'^(livro-odisseia|odisseia-|clube-do-livro|black-clube-do-livro|ebooks-|analises-clube-livro|educacao-literaria|colecao-brasil-a-ultima-cruzada|teller$)')
    AND NOT LOWER(t.nm_gateway_product) LIKE '%membro fundador%'
),
emails AS (
  SELECT DISTINCT v.id_transaction, d2.nm_identifier nm_email
  FROM vit v JOIN `bp-datawarehouse.masterdata.dim_person_identity` d1 ON d1.nm_identifier_type='email' AND d1.nm_identifier=v.nm_email
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` d2 ON d2.id_person=d1.id_person AND d2.nm_identifier_type='email'
  UNION DISTINCT SELECT id_transaction, nm_email FROM vit WHERE nm_email IS NOT NULL
),
ap AS (
  SELECT DISTINCT e.id_transaction, a.id_approach, a.dt_approach_start, a.nm_lead_source, a.nm_lead_comments
  FROM emails e
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_contacts` zc ON LOWER(TRIM(zc.nm_contact_email)) = e.nm_email
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_approaches` a ON a.id_prospect = zc.id_prospect
  JOIN vit v ON v.id_transaction = e.id_transaction
  WHERE a.dt_approach_start BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 30 DAY) AND v.dt_ordered_at
),
msgs AS (
  SELECT ap.id_transaction, ap.id_approach, ap.dt_approach_start, ap.nm_lead_source, ap.nm_lead_comments,
    i.dt_created_interaction_at, i.nm_interaction_type, i.nm_interaction_author, i.id_template, i.bl_seller_interaction, i.bl_prospect_interaction,
    LEFT(REGEXP_REPLACE(COALESCE(i.nm_body_message, i.nm_seller_comment, ''), r'\s+', ' '), 300) AS txt,
    ROW_NUMBER() OVER (PARTITION BY ap.id_approach ORDER BY i.dt_created_interaction_at, i.id_interaction) AS rn
  FROM ap JOIN `bp-datawarehouse.staging.int_zenvia_analytics` i ON i.id_approach = ap.id_approach
)
SELECT v.bl_is_commercial_channel, v.dt_ordered_at, m.* FROM msgs m JOIN vit v USING (id_transaction) WHERE rn <= 4
