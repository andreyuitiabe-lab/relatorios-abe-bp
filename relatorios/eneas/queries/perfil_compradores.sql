-- Perfil por comprador ENE: idade, gênero, renda (decil), UF, novo vs base
CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_ene_perfil` AS
WITH compradores AS (
  SELECT
    id_gateway_customer,
    MIN(dt_ordered_at) AS dt_primeira_compra,
    SUM(vl_payment_gross) AS vl_receita,
    COUNT(*) AS qt_tx,
    ARRAY_AGG(nm_canal ORDER BY dt_ordered_at LIMIT 1)[OFFSET(0)] AS nm_canal,
    ARRAY_AGG(nm_plan_label ORDER BY dt_ordered_at LIMIT 1)[OFFSET(0)] AS nm_plano
  FROM `bp-staging.dbt_abe.tb_ene_compradores_tx`
  GROUP BY 1
),

contato AS (
  SELECT
    id_gateway_customer,
    LOWER(nm_email) AS nm_email,
    cd_cleaned_phone_number,
    cd_address_state
  FROM `bp-datawarehouse.masterdata.dim_contact`
),

-- emails com compra aprovada ANTES da campanha = já era cliente
clientes_anteriores AS (
  SELECT DISTINCT LOWER(c.nm_email) AS nm_email
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  INNER JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.dt_ordered_at < '2026-07-28'
),

usuario AS (
  SELECT
    LOWER(nm_email) AS nm_email,
    id_user,
    dt_birthday,
    nm_gender_inferred
  FROM `bp-datawarehouse.masterdata.dim_user`
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY LOWER(nm_email)
    ORDER BY dt_birthday IS NULL, id_user
  ) = 1
),

renda AS (
  SELECT id_user, cd_income_decile
  FROM `bp-datawarehouse.datamart.dtm_purchasing_power`
)

SELECT
  cp.*,
  ct.nm_email,
  ct.cd_cleaned_phone_number,
  ct.cd_address_state,
  ca.nm_email IS NOT NULL AS bl_ja_era_cliente,
  u.id_user,
  DATE_DIFF(CURRENT_DATE(), DATE(u.dt_birthday), YEAR) AS qt_idade,
  u.nm_gender_inferred,
  r.cd_income_decile
FROM compradores cp
LEFT JOIN contato ct USING (id_gateway_customer)
LEFT JOIN clientes_anteriores ca ON ct.nm_email = ca.nm_email
LEFT JOIN usuario u ON ct.nm_email = u.nm_email
LEFT JOIN renda r ON u.id_user = r.id_user;
