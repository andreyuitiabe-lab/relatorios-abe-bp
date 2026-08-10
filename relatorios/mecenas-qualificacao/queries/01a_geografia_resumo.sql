-- ============================================================================
-- 01a — GEOGRAFIA (resumo): região, capital x interior, porte da cidade
-- Mecenas por tier vs. controle. Reporta N e cobertura em cada linha.
-- ----------------------------------------------------------------------------
-- ⚠️ Gotchas aplicados:
--   - CEP com múltiplas linhas em dim_geolocation → QUALIFY ROW_NUMBER
--   - join IBGE exige normalizar acentos nos DOIS lados (NORMALIZE NFD + \pM)
--   - DF tem 29 regiões administrativas → consolidar em 'brasilia'
--   - CEP > nm_address_city (campo aberto, com typos)
-- Prelude idêntico a _prelude.sql
-- ============================================================================

CREATE TEMP TABLE pop AS
WITH mec_tx AS (
  SELECT
    LOWER(c.nm_email) AS email,
    t.dt_ordered_at, t.vl_payment_gross, t.bl_is_commercial_channel,
    LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas order bump%' AS is_bump
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact`      c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND (
      (t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
      OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%'
    )
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump mecenas%'
    AND c.nm_email IS NOT NULL
),
mec_person AS (
  SELECT
    email,
    COUNTIF(NOT is_bump)                         AS qt_tx_bolsa,
    MIN(IF(NOT is_bump, dt_ordered_at, NULL))    AS dt_first_bolsa,
    MIN(dt_ordered_at)                           AS dt_first_mecenas_any,
    MAX(IF(NOT is_bump, vl_payment_gross, NULL)) AS vl_max_bolsa
  FROM mec_tx GROUP BY email
),
mec_tier AS (
  SELECT
    email,
    CASE
      WHEN qt_tx_bolsa = 0      THEN 'B0 order bump R$180'
      WHEN vl_max_bolsa > 10000 THEN 'B3 alto/patrono'
      WHEN vl_max_bolsa >= 1188 THEN 'B2 bolsas comercial'
      ELSE 'abaixo de R$ 1.000 (não é bolsa)'
    END AS grupo,
    COALESCE(dt_first_bolsa, dt_first_mecenas_any) AS dt_ref
  FROM mec_person
),
ctrl AS (
  SELECT DISTINCT LOWER(c.nm_email) AS email
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  JOIN `bp-datawarehouse.masterdata.dim_contact`       c USING (id_gateway_customer)
  WHERE s.nm_status IN ('active', 'wo renewal')
    AND s.nm_type = 'paid'
    AND s.dt_started_at <= CURRENT_DATETIME()
    AND s.dt_expires_in >= CURRENT_DATETIME()
    AND c.nm_email IS NOT NULL
)
SELECT email, grupo, dt_ref FROM mec_tier
UNION ALL
SELECT email, 'A controle', NULL FROM ctrl
WHERE email NOT IN (SELECT email FROM mec_tier);

-- ---------------------------------------------------------------------------
CREATE TEMP TABLE geo_pessoa AS
WITH dc AS (
  SELECT LOWER(nm_email) AS email,
         cd_address_zipcode AS cep,
         cd_address_state   AS uf_cad
  FROM `bp-datawarehouse.masterdata.dim_contact`
  WHERE nm_email IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY LOWER(nm_email)
    ORDER BY IF(cd_address_zipcode IS NULL, 1, 0), dt_created_at DESC
  ) = 1
),
du AS (
  SELECT LOWER(nm_email) AS email,
         cd_address_zipcode AS cep,
         cd_address_state   AS uf_cad
  FROM `bp-datawarehouse.masterdata.dim_user`
  WHERE nm_email IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY LOWER(nm_email) ORDER BY IF(cd_address_zipcode IS NULL, 1, 0), id_user
  ) = 1
),
geo AS (
  SELECT
    REGEXP_REPLACE(cd_address_zipcode, r'\D', '') AS cep,
    nm_address_city  AS cidade,
    nm_address_state AS uf
  FROM `bp-datawarehouse.masterdata.dim_geolocation_of_brazil_addresses`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY cd_address_zipcode ORDER BY nm_address_city) = 1
),
ibge AS (
  SELECT
    LOWER(REGEXP_REPLACE(NORMALIZE(nm_city, NFD), r'\pM', '')) AS cidade_norm,
    cd_uf,
    ANY_VALUE(nm_region)      AS regiao,
    MAX(qt_city_population)   AS populacao,
    ANY_VALUE(nm_city_size)   AS porte,
    LOGICAL_OR(bl_is_capital) AS is_capital
  FROM `bp-datawarehouse.staging.int_ibge__geo_administrative_divisions`
  GROUP BY 1, 2
),
base AS (
  SELECT
    p.email,
    p.grupo,
    COALESCE(g.uf, dc.uf_cad, du.uf_cad) AS uf,
    CASE
      WHEN COALESCE(g.uf, dc.uf_cad, du.uf_cad) = 'DF' THEN 'brasilia'
      ELSE LOWER(REGEXP_REPLACE(NORMALIZE(g.cidade, NFD), r'\pM', ''))
    END AS cidade_norm
  FROM pop p
  LEFT JOIN dc USING (email)
  LEFT JOIN du USING (email)
  LEFT JOIN geo g
    ON g.cep = REGEXP_REPLACE(COALESCE(dc.cep, du.cep), r'\D', '')
)
SELECT b.*, i.regiao, i.populacao, i.porte, i.is_capital
FROM base b
LEFT JOIN ibge i
  ON i.cidade_norm = b.cidade_norm AND i.cd_uf = b.uf;

-- ---------------------------------------------------------------------------
SELECT
  grupo,
  COUNT(*)                                                AS n_total,
  COUNTIF(uf IS NOT NULL)                                 AS n_com_uf,
  ROUND(100 * COUNTIF(uf IS NOT NULL) / COUNT(*), 1)      AS cob_uf_pct,
  COUNTIF(regiao IS NOT NULL)                             AS n_com_ibge,
  ROUND(100 * COUNTIF(regiao IS NOT NULL) / COUNT(*), 1)  AS cob_ibge_pct,
  -- percentuais sobre a base COM cobertura, não sobre n_total
  ROUND(100 * COUNTIF(regiao = 'Sudeste')      / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_sudeste,
  ROUND(100 * COUNTIF(regiao = 'Sul')          / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_sul,
  ROUND(100 * COUNTIF(regiao = 'Nordeste')     / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_nordeste,
  ROUND(100 * COUNTIF(regiao = 'Centro-Oeste') / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_centro_oeste,
  ROUND(100 * COUNTIF(regiao = 'Norte')        / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_norte,
  ROUND(100 * COUNTIF(is_capital)              / NULLIF(COUNTIF(is_capital IS NOT NULL), 0), 1) AS pct_capital,
  ROUND(100 * COUNTIF(populacao >= 500000)     / NULLIF(COUNTIF(populacao IS NOT NULL), 0), 1) AS pct_cid_500k_mais,
  ROUND(100 * COUNTIF(populacao <  100000)     / NULLIF(COUNTIF(populacao IS NOT NULL), 0), 1) AS pct_cid_menos_100k,
  ROUND(APPROX_QUANTILES(populacao, 2)[OFFSET(1)])                                            AS mediana_populacao
FROM geo_pessoa
GROUP BY grupo
ORDER BY grupo
