-- KPIs consolidados: doadores distintos (vendas) e cobertura de instituição (distribuição).
WITH vendas AS (
  SELECT t.id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status = 'approved'
    AND LOWER(COALESCE(t.nm_gateway_product, '')) NOT LIKE '%solid%'
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%solid%'
    AND t.nm_gateway_plan <> 'mecenas_mecenas-solidario-premium'
    AND COALESCE(t.nm_gateway_product, '') NOT LIKE '%Mecenas Patrono%'
    AND COALESCE(t.nm_gateway_product, '') NOT LIKE '%Mecenas Apoiador%'
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
    AND LOWER(COALESCE(t.nm_gateway_product, '')) NOT LIKE '%order bump%'
    AND ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
      OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
    AND t.vl_payment_gross >= 1000
),

dist AS (
  SELECT
    id_user, nm_reason, nm_create_reason_type,
    (nm_status IN ('active', 'wo renewal')
      AND dt_started_at <= CURRENT_DATETIME()
      AND dt_expires_in >= CURRENT_DATETIME()) AS bl_vigente
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_create_reason_type = 'mecenas'
     OR nm_type = 'donator'
     OR nm_plan LIKE 'bolsa-mecenas%'
),

com_inst AS (
  SELECT id_user
  FROM (
    SELECT
      id_user,
      TRIM(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(
        nm_reason,
        r'Uploaded from Caverna\s*', ''),
        r'Aluno de instituição parceira\s*', ''),
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+', ''),
        r'\b[0-9a-f]{24}\b', '')) AS inst
    FROM dist
    WHERE nm_create_reason_type = 'mecenas'
      AND nm_reason LIKE 'Uploaded from Caverna%'
  )
  WHERE LOWER(inst) NOT IN ('', 'não', 'nao')
    AND LOWER(inst) NOT LIKE 'renova%'
    AND NOT REGEXP_CONTAINS(LOWER(inst), r'^(outro\s+)?bolsista')
)

SELECT
  (SELECT COUNT(DISTINCT id_gateway_customer) FROM vendas)  AS qt_contas_doadoras,
  (SELECT COUNT(DISTINCT id_user) FROM dist)                AS qt_contas_beneficiarias,
  (SELECT COUNT(DISTINCT IF(bl_vigente, id_user, NULL)) FROM dist) AS qt_contas_vigentes,
  (SELECT COUNT(DISTINCT id_user) FROM com_inst)            AS qt_contas_com_instituicao
