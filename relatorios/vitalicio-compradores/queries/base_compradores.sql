-- Quem compra vitalício: uma linha por venda aprovada de vitalício nas janelas comparadas,
-- com o perfil do comprador no momento da compra. Sem PII na saída (id_person é hash interno).
-- Parâmetros (substituídos pelo refresh.py): {ini_bno26} {fim_bno26} {ini_bno25} {fim_bno25} {ini_bp10} {fim_bp10}
-- Vitalício = regra canônica da wiki (bq-planos.md §Vitalícios).

WITH periodos AS (
  SELECT 'BNO26' AS nm_periodo, DATE '{ini_bno26}' AS dt_ini, DATE '{fim_bno26}' AS dt_fim UNION ALL
  SELECT 'BNO25', DATE '{ini_bno25}', DATE '{fim_bno25}' UNION ALL
  SELECT 'BP10',  DATE '{ini_bp10}',  DATE '{fim_bp10}'
),

vit AS (
  SELECT
    p.nm_periodo,
    t.id_transaction,
    t.dt_ordered_at,
    t.id_gateway_customer,
    t.vl_payment_gross,
    t.qt_installments,
    t.nm_payment_method,
    t.nm_plan_label,
    t.nm_gateway_plan,
    t.nm_gateway_product,
    t.bl_is_commercial_channel,
    t.nm_pptc_tracking_publisher,
    t.nm_pptc_utm_campaign,
    t.nm_utm_source,
    LOWER(TRIM(c.nm_email)) AS nm_email,
    c.cd_address_state
  FROM `bp-datawarehouse.masterdata.fct_transactions` AS t
  INNER JOIN periodos AS p ON DATE(t.dt_ordered_at) BETWEEN p.dt_ini AND p.dt_fim
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` AS c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.bl_lifetime_offer = TRUE
    AND (
      t.nm_gateway_plan IN ('good', 'better', 'best', 'black')
      OR LOWER(t.nm_gateway_product) LIKE '%vital%'
      OR LOWER(t.nm_gateway_product) LIKE '%membro fundador%'
    )
    AND NOT REGEXP_CONTAINS(t.nm_gateway_plan,
      r'^(livro-odisseia|odisseia-|clube-do-livro|black-clube-do-livro|ebooks-|analises-clube-livro|educacao-literaria|colecao-brasil-a-ultima-cruzada|teller$)')
),

-- pessoa (identity graph) e todos os e-mails dela; sem pessoa resolvida, cai no próprio e-mail
pessoa AS (
  SELECT
    v.id_transaction,
    COALESCE(dpi.id_person, CONCAT('email:', v.nm_email)) AS id_person
  FROM vit AS v
  LEFT JOIN `bp-datawarehouse.masterdata.dim_person_identity` AS dpi
    ON dpi.nm_identifier_type = 'email' AND dpi.nm_identifier = v.nm_email
),

emails_pessoa AS (
  SELECT DISTINCT p.id_transaction, dpi.nm_identifier AS nm_email
  FROM pessoa AS p
  INNER JOIN `bp-datawarehouse.masterdata.dim_person_identity` AS dpi
    ON dpi.id_person = p.id_person AND dpi.nm_identifier_type = 'email'
  UNION DISTINCT
  SELECT id_transaction, nm_email FROM vit WHERE nm_email IS NOT NULL
),

clientes_pessoa AS (
  SELECT DISTINCT e.id_transaction, c.id_gateway_customer
  FROM emails_pessoa AS e
  INNER JOIN `bp-datawarehouse.masterdata.dim_contact` AS c ON LOWER(TRIM(c.nm_email)) = e.nm_email
),

-- compras aprovadas anteriores da pessoa
historico AS (
  SELECT
    v.id_transaction,
    COUNT(t.id_transaction) AS qt_compras_antes,
    SUM(t.vl_payment_gross) AS vl_gasto_antes,
    MIN(t.dt_ordered_at) AS dt_primeira_compra,
    COUNTIF(
      t.bl_lifetime_offer
      AND (t.nm_gateway_plan IN ('good', 'better', 'best', 'black')
        OR LOWER(t.nm_gateway_product) LIKE '%vital%'
        OR LOWER(t.nm_gateway_product) LIKE '%membro fundador%')
      AND NOT REGEXP_CONTAINS(t.nm_gateway_plan,
        r'^(livro-odisseia|odisseia-|clube-do-livro|black-clube-do-livro|ebooks-|analises-clube-livro|educacao-literaria|colecao-brasil-a-ultima-cruzada|teller$)')
    ) AS qt_vitalicio_antes,
    COUNTIF(t.nm_gateway_plan = 'black' AND t.bl_lifetime_offer) AS qt_black_vit_antes
  FROM vit AS v
  INNER JOIN clientes_pessoa AS cp USING (id_transaction)
  INNER JOIN `bp-datawarehouse.masterdata.fct_transactions` AS t
    ON t.id_gateway_customer = cp.id_gateway_customer
   AND t.nm_status = 'approved'
   AND t.dt_ordered_at < v.dt_ordered_at
   AND t.id_transaction != v.id_transaction
  GROUP BY 1
),

-- assinatura de membership paga: ativa no momento da compra ou já encerrada (ex-membro)
assinaturas AS (
  SELECT
    v.id_transaction,
    LOGICAL_OR(s.dt_started_at < DATETIME_SUB(v.dt_ordered_at, INTERVAL 1 HOUR) AND s.dt_expires_in >= v.dt_ordered_at) AS bl_membro_ativo,
    LOGICAL_OR(s.dt_expires_in < v.dt_ordered_at) AS bl_ex_membro
  FROM vit AS v
  INNER JOIN clientes_pessoa AS cp USING (id_transaction)
  INNER JOIN `bp-datawarehouse.masterdata.dim_subscriptions` AS s
    ON s.id_gateway_customer = cp.id_gateway_customer
   AND s.nm_type = 'paid'
   AND REGEXP_CONTAINS(LOWER(COALESCE(s.nm_gateway_plan, s.nm_plan)),
       r'good|better|best|black|supporter|mecenas|intermediario|premium|essencial|economico|basico|apoiador|originais')
   AND s.dt_started_at < DATETIME_SUB(v.dt_ordered_at, INTERVAL 1 HOUR)
  GROUP BY 1
),

-- último cadastro de lead antes da compra (HUB é criação de conta, não lead)
ult_lead AS (
  SELECT
    v.id_transaction,
    l.nm_tag AS nm_tag_ult_lead,
    DATE_DIFF(DATE(v.dt_ordered_at), DATE(l.dt_registered_at_br), DAY) AS qt_dias_ult_lead
  FROM vit AS v
  INNER JOIN emails_pessoa AS e USING (id_transaction)
  INNER JOIN `bp-datawarehouse.datamart.dtm_analytics_lead_conversion` AS l
    ON LOWER(TRIM(l.nm_email)) = e.nm_email
   AND l.dt_registered_at_br <= v.dt_ordered_at
   AND NOT STARTS_WITH(l.nm_tag, 'HUB')
  QUALIFY ROW_NUMBER() OVER (PARTITION BY v.id_transaction ORDER BY l.dt_registered_at_br DESC) = 1
),

-- consumo na plataforma nos 90 dias antes da compra (D-90..D-1; sessões > 4h são bug de tracking)
consumo AS (
  SELECT
    v.id_transaction,
    SUM(vs.vl_watch_time_seconds) / 3600 AS vl_horas_90d
  FROM vit AS v
  INNER JOIN emails_pessoa AS e USING (id_transaction)
  INNER JOIN `bp-datawarehouse.datamart.obt_kafka__view_sessions` AS vs
    ON LOWER(vs.nm_email) = e.nm_email
   AND vs.dt_created_at >= DATETIME_SUB(DATETIME_TRUNC(v.dt_ordered_at, DAY), INTERVAL 90 DAY)
   AND vs.dt_created_at < DATETIME_TRUNC(v.dt_ordered_at, DAY)
   AND vs.vl_watch_time_seconds BETWEEN 1 AND 4 * 3600
  WHERE vs.dt_created_at >= DATETIME '{ini_consumo}'
  GROUP BY 1
),

renda AS (
  SELECT LOWER(TRIM(nm_email)) AS nm_email, ANY_VALUE(cd_income_decile) AS cd_income_decile
  FROM `bp-datawarehouse.datamart.dtm_purchasing_power`
  GROUP BY 1
),

cartao AS (
  SELECT LOWER(TRIM(nm_email)) AS nm_email, MAX(nm_credit_card_level_max) AS nm_cartao
  FROM `bp-datawarehouse.staging.int_credit_card_level`
  GROUP BY 1
),

genero AS (
  SELECT LOWER(TRIM(nm_email)) AS nm_email, ANY_VALUE(nm_gender_inferred) AS nm_genero
  FROM `bp-datawarehouse.masterdata.dim_user`
  GROUP BY 1
)

SELECT
  v.nm_periodo,
  v.id_transaction,
  p.id_person,
  DATE(v.dt_ordered_at) AS dt_venda,
  v.vl_payment_gross,
  v.qt_installments,
  v.nm_payment_method,
  v.nm_plan_label,
  v.nm_gateway_plan,
  v.nm_gateway_product,
  v.bl_is_commercial_channel,
  v.nm_pptc_tracking_publisher,
  v.nm_pptc_utm_campaign,
  v.nm_utm_source,
  v.cd_address_state,
  COALESCE(h.qt_compras_antes, 0) AS qt_compras_antes,
  COALESCE(h.vl_gasto_antes, 0) AS vl_gasto_antes,
  DATE_DIFF(DATE(v.dt_ordered_at), DATE(h.dt_primeira_compra), DAY) AS qt_dias_cliente,
  COALESCE(h.qt_vitalicio_antes, 0) AS qt_vitalicio_antes,
  COALESCE(h.qt_black_vit_antes, 0) AS qt_black_vit_antes,
  COALESCE(a.bl_membro_ativo, FALSE) AS bl_membro_ativo,
  COALESCE(a.bl_ex_membro, FALSE) AS bl_ex_membro,
  ul.nm_tag_ult_lead,
  ul.qt_dias_ult_lead,
  COALESCE(co.vl_horas_90d, 0) AS vl_horas_90d,
  r.cd_income_decile,
  ca.nm_cartao,
  g.nm_genero
FROM vit AS v
LEFT JOIN pessoa AS p USING (id_transaction)
LEFT JOIN historico AS h USING (id_transaction)
LEFT JOIN assinaturas AS a USING (id_transaction)
LEFT JOIN ult_lead AS ul USING (id_transaction)
LEFT JOIN consumo AS co USING (id_transaction)
LEFT JOIN renda AS r ON r.nm_email = v.nm_email
LEFT JOIN cartao AS ca ON ca.nm_email = v.nm_email
LEFT JOIN genero AS g ON g.nm_email = v.nm_email
