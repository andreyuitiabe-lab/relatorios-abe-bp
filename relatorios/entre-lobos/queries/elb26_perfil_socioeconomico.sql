-- ELB26 — Perfil socioeconômico completo das sementes de lookalike
-- Dimensões: renda (decil + R$ per capita), cartão (hierarquia completa), gênero,
-- idade (cobertura ~13%), região, porte de cidade e capital vs interior (IBGE via CEP)
-- Gotchas aplicados (bq-schema-extra): dedup de CEP por QUALIFY, normalização de acentos
-- no join IBGE, DF consolidado em Brasília.

WITH compradores AS (
  SELECT LOWER(id_comprador) AS email, nm_caminho
  FROM `bp-staging.dbt_abe.tb_aqv_compradores`
  WHERE sigla = 'ELS' AND bl_tem_email
),

viewers_elb AS (
  SELECT
    LOWER(nm_email) AS email,
    SUM(vl_watch_time_seconds) AS secs,
    MAX(DATE(dt_created_at)) AS dt_ultima_view
  FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
  WHERE nm_playlist LIKE 'Entre Lobos%'
    AND nm_email IS NOT NULL
  GROUP BY 1
  HAVING SUM(vl_watch_time_seconds) >= 300
),

compradores_elb22 AS (
  SELECT DISTINCT LOWER(c.nm_email) AS email
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2022-05-17' AND '2022-07-31'
    AND (
      REGEXP_CONTAINS(LOWER(t.nm_pptc_tracking_name), r'(^|[^a-z])elb([^a-z0-9]|$)|entre[-_ ]?lobos')
      OR REGEXP_CONTAINS(LOWER(t.nm_pptc_utm_campaign), r'(^|[^a-z])elb([^a-z0-9]|$)|entre[-_ ]?lobos')
      OR REGEXP_CONTAINS(LOWER(t.nm_pptc_utm_content), r'(^|[^a-z])elb([^a-z0-9]|$)|entre[-_ ]?lobos')
    )
    AND c.nm_email IS NOT NULL
),

leads_aa_elb26 AS (
  SELECT DISTINCT LOWER(nm_email) AS email
  FROM `bp-staging.dbt_abe.fct_lead_iql`
  WHERE nm_tag = 'ELB26' AND nm_iql_band IN ('A+', 'A')
),

segmentos AS (
  SELECT '1_compradores_elb22' AS segmento, email FROM compradores_elb22
  UNION ALL
  SELECT '2_viewers_elb_todos', email FROM viewers_elb
  UNION ALL
  SELECT '3_viewers_elb_12m', email FROM viewers_elb WHERE dt_ultima_view >= '2025-08-01'
  UNION ALL
  SELECT '4_viewers_elb_1h_mais', email FROM viewers_elb WHERE secs >= 3600
  UNION ALL
  SELECT '5_compradores_els', email FROM compradores WHERE TRUE
  UNION ALL
  SELECT '6_els_x_viewers_elb', c.email
  FROM compradores c JOIN viewers_elb USING (email)
  UNION ALL
  SELECT '7_leads_aa_elb26', email FROM leads_aa_elb26
),

usuario AS (
  SELECT
    LOWER(nm_email) AS email,
    MAX(id_user) AS id_user,
    MAX(nm_gender_inferred) AS genero,
    MAX(cd_address_state) AS uf,
    MAX(cd_address_zipcode) AS cep,
    MAX(DATE(dt_birthday)) AS nascimento
  FROM `bp-datawarehouse.masterdata.dim_user`
  WHERE nm_email IS NOT NULL
  GROUP BY 1
),

renda AS (
  SELECT
    u.email,
    MAX(pp.cd_income_decile) AS decil,
    MAX(pp.vl_income_per_capita) AS renda_pc
  FROM usuario u
  JOIN `bp-datawarehouse.datamart.dtm_purchasing_power` pp USING (id_user)
  WHERE pp.cd_income_decile > 0
  GROUP BY 1
),

cartao AS (
  SELECT LOWER(nm_email) AS email, MAX(nm_credit_card_level_max) AS nivel
  FROM `bp-datawarehouse.staging.int_credit_card_level`
  WHERE nm_email IS NOT NULL
  GROUP BY 1
),

cep_cidade AS (
  SELECT cd_address_zipcode, nm_address_city, nm_address_state
  FROM `bp-datawarehouse.masterdata.dim_geolocation_of_brazil_addresses`
  QUALIFY ROW_NUMBER() OVER (PARTITION BY cd_address_zipcode ORDER BY nm_address_city) = 1
),

ibge AS (
  SELECT
    CASE WHEN cd_uf = 'DF' THEN 'brasilia'
      ELSE LOWER(TRANSLATE(NORMALIZE(nm_city, NFD), 'áàâãäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc'))
    END AS cidade_norm,
    cd_uf,
    MAX(nm_city_size) AS porte,
    MAX(CAST(bl_is_capital AS INT64)) AS capital,
    MAX(qt_city_population) AS populacao
  FROM `bp-datawarehouse.staging.int_ibge__geo_administrative_divisions`
  GROUP BY 1, 2
),

geo AS (
  SELECT
    u.email,
    i.porte,
    i.capital
  FROM usuario u
  JOIN cep_cidade g ON u.cep = g.cd_address_zipcode
  JOIN ibge i
    ON i.cidade_norm = CASE WHEN g.nm_address_state = 'DF' THEN 'brasilia'
        ELSE LOWER(TRANSLATE(NORMALIZE(g.nm_address_city, NFD), 'áàâãäéèêëíìîïóòôõöúùûüç', 'aaaaaeeeeiiiiooooouuuuc')) END
    AND i.cd_uf = g.nm_address_state
)

SELECT
  s.segmento,
  COUNT(*) AS n,

  -- renda
  ROUND(AVG(r.decil), 2) AS decil_medio,
  ROUND(COUNTIF(r.decil >= 7) / NULLIF(COUNTIF(r.decil IS NOT NULL), 0) * 100, 1) AS pct_decil7,
  ROUND(APPROX_QUANTILES(r.renda_pc, 100)[OFFSET(50)], 0) AS renda_pc_mediana,
  ROUND(COUNTIF(r.decil IS NOT NULL) / COUNT(*) * 100, 1) AS cob_renda,

  -- cartão (hierarquia)
  ROUND(COUNTIF(c.nivel = '6_black') / NULLIF(COUNTIF(c.nivel IS NOT NULL), 0) * 100, 1) AS pct_black,
  ROUND(COUNTIF(c.nivel IN ('4_platinum', '5_amex')) / NULLIF(COUNTIF(c.nivel IS NOT NULL), 0) * 100, 1) AS pct_plat_amex,
  ROUND(COUNTIF(c.nivel = '3_gold') / NULLIF(COUNTIF(c.nivel IS NOT NULL), 0) * 100, 1) AS pct_gold,
  ROUND(COUNTIF(c.nivel IN ('0_debit', '1_business', '2_standard')) / NULLIF(COUNTIF(c.nivel IS NOT NULL), 0) * 100, 1) AS pct_basico,
  ROUND(COUNTIF(c.nivel IS NOT NULL) / COUNT(*) * 100, 1) AS cob_cartao,

  -- gênero
  ROUND(COUNTIF(u.genero = 'Masculino') / NULLIF(COUNTIF(u.genero IN ('Masculino', 'Feminino')), 0) * 100, 1) AS pct_masc,

  -- idade
  ROUND(AVG(IF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 14 AND 95,
    DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR), NULL)), 1) AS idade_media,
  ROUND(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 14 AND 29)
    / NULLIF(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 14 AND 95), 0) * 100, 1) AS pct_14_29,
  ROUND(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 30 AND 44)
    / NULLIF(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 14 AND 95), 0) * 100, 1) AS pct_30_44,
  ROUND(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 45 AND 59)
    / NULLIF(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 14 AND 95), 0) * 100, 1) AS pct_45_59,
  ROUND(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 60 AND 95)
    / NULLIF(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 14 AND 95), 0) * 100, 1) AS pct_60_mais,
  ROUND(COUNTIF(DATE_DIFF(CURRENT_DATE(), u.nascimento, YEAR) BETWEEN 14 AND 95) / COUNT(*) * 100, 1) AS cob_idade,

  -- região
  ROUND(COUNTIF(u.uf IN ('SP','RJ','MG','ES')) / NULLIF(COUNTIF(u.uf IS NOT NULL), 0) * 100, 1) AS pct_sudeste,
  ROUND(COUNTIF(u.uf IN ('PR','SC','RS')) / NULLIF(COUNTIF(u.uf IS NOT NULL), 0) * 100, 1) AS pct_sul,
  ROUND(COUNTIF(u.uf IN ('BA','SE','AL','PE','PB','RN','CE','PI','MA')) / NULLIF(COUNTIF(u.uf IS NOT NULL), 0) * 100, 1) AS pct_nordeste,
  ROUND(COUNTIF(u.uf IN ('MT','MS','GO','DF')) / NULLIF(COUNTIF(u.uf IS NOT NULL), 0) * 100, 1) AS pct_centrooeste,
  ROUND(COUNTIF(u.uf IN ('AM','PA','AC','RO','RR','AP','TO')) / NULLIF(COUNTIF(u.uf IS NOT NULL), 0) * 100, 1) AS pct_norte,

  -- porte de cidade / capital
  ROUND(COUNTIF(geo.capital = 1) / NULLIF(COUNTIF(geo.capital IS NOT NULL), 0) * 100, 1) AS pct_capital,
  ROUND(COUNTIF(geo.porte IN ('Grande', 'Metrópole')) / NULLIF(COUNTIF(geo.porte IS NOT NULL), 0) * 100, 1) AS pct_cid_grande,
  ROUND(COUNTIF(geo.porte LIKE 'Pequeno%') / NULLIF(COUNTIF(geo.porte IS NOT NULL), 0) * 100, 1) AS pct_cid_pequena,
  ROUND(COUNTIF(geo.porte IS NOT NULL) / COUNT(*) * 100, 1) AS cob_geo

FROM segmentos s
LEFT JOIN usuario u USING (email)
LEFT JOIN renda r USING (email)
LEFT JOIN cartao c USING (email)
LEFT JOIN geo USING (email)
GROUP BY 1
ORDER BY 1
