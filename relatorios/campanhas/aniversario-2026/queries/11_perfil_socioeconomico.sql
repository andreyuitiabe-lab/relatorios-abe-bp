-- Perfil socioeconômico: compradores BP10 vs base geral (assinantes ativos)
WITH compras_bp10 AS (
  SELECT LOWER(c.nm_email) AS email
  FROM masterdata.fct_transactions t
  JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) >= '2026-06-11'
    AND (
      REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_utm_campaign, '')), r'bp10|vit')
      OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_lead_first_tracking, '') || ' ' || COALESCE(t.nm_lead_last_tracking, '')), r'bp10')
      OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_pptc_checkout_name, '') || ' ' || COALESCE(t.nm_pptc_tracking_name, '')), r'anos|aniversario|(^|/| )10(/|$)')
    )
  GROUP BY 1
),

u AS (
  SELECT
    id_user,
    LOWER(nm_email) AS email,
    nm_gender_inferred,
    dt_birthday,
    cd_address_state
  FROM masterdata.dim_user
  WHERE nm_email IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (PARTITION BY LOWER(nm_email) ORDER BY id_user) = 1
),

base_ativa AS (
  SELECT DISTINCT s.id_user
  FROM masterdata.dim_subscriptions s
  WHERE s.nm_status IN ('active', 'wo renewal')
    AND s.nm_type = 'paid'
    AND s.dt_started_at <= CURRENT_DATETIME()
    AND s.dt_expires_in >= CURRENT_DATETIME()
    AND s.id_user IS NOT NULL
),

pop AS (
  SELECT 'bp10' AS pop, u.* FROM u JOIN compras_bp10 b ON u.email = b.email
  UNION ALL
  SELECT 'base', u.* FROM u JOIN base_ativa USING (id_user)
),

enriquecido AS (
  SELECT
    p.*,
    DATE_DIFF(CURRENT_DATE(), DATE(p.dt_birthday), YEAR) AS idade,
    pp.cd_income_decile,
    cc.nm_credit_card_level_max,
    CASE
      WHEN p.cd_address_state IN ('AC','AP','AM','PA','RO','RR','TO') THEN 'Norte'
      WHEN p.cd_address_state IN ('AL','BA','CE','MA','PB','PE','PI','RN','SE') THEN 'Nordeste'
      WHEN p.cd_address_state IN ('DF','GO','MT','MS') THEN 'Centro-Oeste'
      WHEN p.cd_address_state IN ('ES','MG','RJ','SP') THEN 'Sudeste'
      WHEN p.cd_address_state IN ('PR','RS','SC') THEN 'Sul'
      ELSE NULL
    END AS regiao
  FROM pop p
  LEFT JOIN datamart.dtm_purchasing_power pp USING (id_user)
  LEFT JOIN (
    SELECT LOWER(nm_email) AS email, MAX(nm_credit_card_level_max) AS nm_credit_card_level_max
    FROM staging.int_credit_card_level
    GROUP BY 1
  ) cc USING (email)
)

SELECT
  pop,
  COUNT(*) AS n,
  -- gênero (inferido)
  ROUND(100 * COUNTIF(nm_gender_inferred = 'Masculino') / NULLIF(COUNTIF(nm_gender_inferred IS NOT NULL), 0), 1) AS pct_masc,
  ROUND(100 * COUNTIF(nm_gender_inferred = 'Feminino') / NULLIF(COUNTIF(nm_gender_inferred IS NOT NULL), 0), 1) AS pct_fem,
  -- faixa etária (quem informou nascimento)
  COUNTIF(idade BETWEEN 18 AND 80) AS n_idade,
  ROUND(100 * COUNTIF(idade BETWEEN 18 AND 24) / NULLIF(COUNTIF(idade BETWEEN 18 AND 80), 0), 1) AS pct_18_24,
  ROUND(100 * COUNTIF(idade BETWEEN 25 AND 34) / NULLIF(COUNTIF(idade BETWEEN 18 AND 80), 0), 1) AS pct_25_34,
  ROUND(100 * COUNTIF(idade BETWEEN 35 AND 44) / NULLIF(COUNTIF(idade BETWEEN 18 AND 80), 0), 1) AS pct_35_44,
  ROUND(100 * COUNTIF(idade BETWEEN 45 AND 54) / NULLIF(COUNTIF(idade BETWEEN 18 AND 80), 0), 1) AS pct_45_54,
  ROUND(100 * COUNTIF(idade BETWEEN 55 AND 64) / NULLIF(COUNTIF(idade BETWEEN 18 AND 80), 0), 1) AS pct_55_64,
  ROUND(100 * COUNTIF(idade BETWEEN 65 AND 80) / NULLIF(COUNTIF(idade BETWEEN 18 AND 80), 0), 1) AS pct_65m,
  -- região (quem tem UF)
  ROUND(100 * COUNTIF(regiao = 'Sudeste') / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_sudeste,
  ROUND(100 * COUNTIF(regiao = 'Sul') / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_sul,
  ROUND(100 * COUNTIF(regiao = 'Nordeste') / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_nordeste,
  ROUND(100 * COUNTIF(regiao = 'Centro-Oeste') / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_co,
  ROUND(100 * COUNTIF(regiao = 'Norte') / NULLIF(COUNTIF(regiao IS NOT NULL), 0), 1) AS pct_norte,
  -- renda (decil IBGE por CEP)
  ROUND(AVG(IF(cd_income_decile > 0, cd_income_decile, NULL)), 2) AS decil_medio,
  ROUND(100 * COUNTIF(cd_income_decile >= 7) / NULLIF(COUNTIF(cd_income_decile > 0), 0), 1) AS pct_decil7m,
  -- cartão (quem tem nível conhecido)
  ROUND(100 * COUNTIF(nm_credit_card_level_max IN ('4_platinum','5_amex','6_black'))
        / NULLIF(COUNTIF(nm_credit_card_level_max IS NOT NULL), 0), 1) AS pct_cartao_premium,
  ROUND(100 * COUNTIF(nm_credit_card_level_max = '6_black')
        / NULLIF(COUNTIF(nm_credit_card_level_max IS NOT NULL), 0), 1) AS pct_cartao_black
FROM enriquecido
GROUP BY 1
