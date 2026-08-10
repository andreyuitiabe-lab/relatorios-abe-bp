-- Lista para abordagem Mecenas: Membros Fundadores + plano Black
-- Exclusões pedidas: Mecenas ativo, CEC, Retiro (triple-check email/telefone/CPF)
-- Gerado em 2026-08-10

WITH fundador AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND nm_gateway_product LIKE '%Membro Fundador%'
),

black_ativo AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_gateway_plan = 'black'
    AND nm_status IN ('active', 'wo renewal')
    AND nm_type = 'paid'
    AND dt_started_at <= CURRENT_DATETIME()
    AND dt_expires_in >= CURRENT_DATETIME()
),

black_vitalicio AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND nm_gateway_plan = 'black'
    AND bl_lifetime_offer = TRUE
),

publico AS (
  SELECT
    id_gateway_customer,
    MAX(bl_fundador)        AS bl_fundador,
    MAX(bl_black_ativo)     AS bl_black_ativo,
    MAX(bl_black_vitalicio) AS bl_black_vitalicio
  FROM (
    SELECT id_gateway_customer, TRUE AS bl_fundador, FALSE AS bl_black_ativo, FALSE AS bl_black_vitalicio FROM fundador
    UNION ALL
    SELECT id_gateway_customer, FALSE, TRUE, FALSE FROM black_ativo
    UNION ALL
    SELECT id_gateway_customer, FALSE, FALSE, TRUE FROM black_vitalicio
  )
  GROUP BY id_gateway_customer
),

-- ===== Exclusões =====

mecenas_ativo AS (
  SELECT DISTINCT c.nm_email, c.cd_cleaned_phone_number, c.cd_cpf
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE s.nm_plan LIKE '%mecenas%'
    AND s.nm_status IN ('active', 'wo renewal')
    AND s.dt_started_at <= CURRENT_DATETIME()
    AND s.dt_expires_in >= CURRENT_DATETIME()
),

cec_retiro AS (
  SELECT DISTINCT c.nm_email, c.cd_cleaned_phone_number, c.cd_cpf
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND (
      t.nm_gateway_product LIKE '%Conselho Editorial%'
      OR LOWER(t.nm_gateway_product) LIKE '%retiro%'
    )
),

-- ===== Enriquecimento =====

gasto AS (
  SELECT
    id_gateway_customer,
    ROUND(SUM(vl_payment_gross))  AS vl_gasto_total,
    ROUND(MAX(vl_payment_gross))  AS vl_maior_ticket,
    MIN(DATE(dt_ordered_at))      AS dt_primeira_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
  GROUP BY id_gateway_customer
)

SELECT
  CASE
    WHEN p.bl_fundador AND (p.bl_black_ativo OR p.bl_black_vitalicio) THEN 'FUNDADOR + BLACK'
    WHEN p.bl_fundador                                                THEN 'FUNDADOR'
    WHEN p.bl_black_vitalicio                                         THEN 'BLACK VITALICIO'
    ELSE 'BLACK ATIVO'
  END                                   AS nm_segmento,
  c.nm_name                             AS nome,
  c.nm_email                            AS email,
  c.cd_cleaned_phone_number             AS telefone,
  c.cd_cpf                              AS cpf,
  c.cd_address_state                    AS uf,
  c.nm_address_city                     AS cidade,
  pp.cd_income_decile                   AS decil_renda,
  g.vl_gasto_total,
  g.vl_maior_ticket,
  g.dt_primeira_compra,
  DATE_DIFF(CURRENT_DATE(), g.dt_primeira_compra, DAY) / 365.25 AS anos_de_casa
FROM publico p
JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
LEFT JOIN gasto g USING (id_gateway_customer)
LEFT JOIN `bp-datawarehouse.datamart.dtm_purchasing_power` pp ON pp.nm_email = c.nm_email

-- triple-check Mecenas ativo
LEFT JOIN mecenas_ativo m1 ON m1.nm_email                = c.nm_email                AND c.nm_email IS NOT NULL
LEFT JOIN mecenas_ativo m2 ON m2.cd_cleaned_phone_number = c.cd_cleaned_phone_number AND c.cd_cleaned_phone_number IS NOT NULL
LEFT JOIN mecenas_ativo m3 ON m3.cd_cpf                  = c.cd_cpf                  AND c.cd_cpf IS NOT NULL
-- triple-check CEC / Retiro
LEFT JOIN cec_retiro    r1 ON r1.nm_email                = c.nm_email                AND c.nm_email IS NOT NULL
LEFT JOIN cec_retiro    r2 ON r2.cd_cleaned_phone_number = c.cd_cleaned_phone_number AND c.cd_cleaned_phone_number IS NOT NULL
LEFT JOIN cec_retiro    r3 ON r3.cd_cpf                  = c.cd_cpf                  AND c.cd_cpf IS NOT NULL

WHERE m1.nm_email IS NULL AND m2.cd_cleaned_phone_number IS NULL AND m3.cd_cpf IS NULL
  AND r1.nm_email IS NULL AND r2.cd_cleaned_phone_number IS NULL AND r3.cd_cpf IS NULL
QUALIFY ROW_NUMBER() OVER (PARTITION BY c.nm_email ORDER BY g.vl_gasto_total DESC) = 1
ORDER BY g.vl_gasto_total DESC
