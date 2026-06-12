-- Funil ELS: viewers × leads × compradores
-- Compara perfil socioeconômico dos três grupos
-- Resultado: total, decil médio, % decil7+, % cartão premium, % masculino por grupo

WITH

viewers_raw AS (
  SELECT DISTINCT nm_email
  FROM `bp-datawarehouse.datamart.obt_kafka__view_sessions`
  WHERE nm_playlist = 'El Salvador: O Dia em que o Medo Mudou de Lado'
    AND vl_watch_time_seconds >= 300
    AND nm_email IS NOT NULL
),

leads_raw AS (
  SELECT DISTINCT nm_email
  FROM `bp-datawarehouse.bp-lake.marketing.lead_registration`
  WHERE nm_tag = 'ELS'
    AND nm_email IS NOT NULL
),

-- Método UTM: mais completo (inclui organic/live/Comercial sem lead registration)
buyers_raw AS (
  SELECT DISTINCT dc.nm_email
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc
    ON dc.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at >= '2025-11-19'
    AND (
      LOWER(t.nm_pptc_utm_campaign) LIKE '%els%'
      OR LOWER(t.nm_pptc_utm_campaign) LIKE '%el_salvador%'
      OR LOWER(t.nm_pptc_utm_campaign) LIKE '%el-salvador%'
    )
    AND dc.nm_email IS NOT NULL
),

user_profile AS (
  SELECT DISTINCT
    u.nm_email,
    u.nm_gender_inferred,
    u.cd_address_state,
    pp.cd_income_decile,
    pp.nm_credit_card_level
  FROM `bp-datawarehouse.masterdata.dim_user` u
  LEFT JOIN `bp-datawarehouse.datamart.dtm_purchasing_power` pp
    ON pp.id_user = u.id_user
  WHERE u.nm_email IS NOT NULL
),

all_groups AS (
  SELECT '1_viewers'   AS grupo, nm_email FROM viewers_raw
  UNION ALL
  SELECT '2_leads_els',          nm_email FROM leads_raw
  UNION ALL
  SELECT '3_buyers_els',         nm_email FROM buyers_raw
)

SELECT
  ag.grupo,
  COUNT(*)                                                                                            AS total,
  COUNTIF(up.nm_email IS NOT NULL)                                                                    AS com_dados,
  ROUND(AVG(CASE WHEN up.cd_income_decile > 0 THEN up.cd_income_decile END), 2)                      AS decil_medio,
  ROUND(COUNTIF(up.cd_income_decile >= 7) / NULLIF(COUNTIF(up.cd_income_decile > 0), 0) * 100, 1)   AS pct_decil7plus,
  ROUND(
    COUNTIF(up.nm_credit_card_level IN ('4_platinum','5_amex','6_black'))
    / NULLIF(COUNTIF(up.nm_credit_card_level IS NOT NULL), 0) * 100, 1
  )                                                                                                    AS pct_premium_card,
  ROUND(
    COUNTIF(up.nm_gender_inferred = 'Masculino')
    / NULLIF(COUNTIF(up.nm_gender_inferred IS NOT NULL), 0) * 100, 1
  )                                                                                                    AS pct_masculino
FROM all_groups ag
LEFT JOIN user_profile up ON up.nm_email = ag.nm_email
GROUP BY ag.grupo
ORDER BY ag.grupo
