-- ELB26 (relançamento Entre Lobos) — dimensionamento e perfil de públicos-semente para LKL Meta
-- Sementes candidatas: compradores ELB 2022, viewers da série (por recência/profundidade),
-- sub-segmento premium e compradores ELS (proximidade temática: segurança pública).
-- Aprendizado ELS: LKL compradores ROAS 1,90 / "sinal forte" 2,13 / genérico 0,98 — semente importa.

WITH compradores_elb22 AS (
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

compradores_els AS (
  SELECT DISTINCT LOWER(id_comprador) AS email
  FROM `bp-staging.dbt_abe.tb_aqv_compradores`
  WHERE sigla = 'ELS' AND bl_tem_email
),

-- Leads A+/A do próprio ELB26 (IQL) — "sinal forte" da campanha
-- ⚠️ pré-merge da MR !2426 o fct atualiza só com dbt run manual (ver iql.md)
leads_aa_elb26 AS (
  SELECT DISTINCT LOWER(nm_email) AS email
  FROM `bp-staging.dbt_abe.fct_lead_iql`
  WHERE nm_tag = 'ELB26' AND nm_iql_band IN ('A+', 'A')
),

usuario AS (
  SELECT
    LOWER(nm_email) AS email,
    MAX(nm_gender_inferred) AS genero,
    MAX(id_user) AS id_user
  FROM `bp-datawarehouse.masterdata.dim_user`
  WHERE nm_email IS NOT NULL
  GROUP BY 1
),

renda AS (
  SELECT u.email, MAX(pp.cd_income_decile) AS decil
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

segmentos AS (
  SELECT '1_compradores_elb22' AS segmento, email FROM compradores_elb22
  UNION ALL
  SELECT '2_viewers_elb_todos', email FROM viewers_elb
  UNION ALL
  SELECT '3_viewers_elb_12m', email FROM viewers_elb WHERE dt_ultima_view >= '2025-08-01'
  UNION ALL
  SELECT '4_viewers_elb_1h_mais', email FROM viewers_elb WHERE secs >= 3600
  UNION ALL
  SELECT '5_compradores_els', email FROM compradores_els
  UNION ALL
  SELECT '6_els_x_viewers_elb', email
  FROM compradores_els JOIN viewers_elb USING (email)
  UNION ALL
  SELECT '7_leads_aa_elb26', email FROM leads_aa_elb26
)

SELECT
  s.segmento,
  COUNT(*) AS n,
  ROUND(AVG(r.decil), 2) AS decil_medio,
  ROUND(COUNTIF(r.decil >= 7) / NULLIF(COUNTIF(r.decil IS NOT NULL), 0) * 100, 1) AS pct_decil7mais,
  ROUND(COUNTIF(c.nivel IN ('4_platinum', '5_amex', '6_black'))
    / NULLIF(COUNTIF(c.nivel IS NOT NULL), 0) * 100, 1) AS pct_cartao_premium,
  ROUND(COUNTIF(u.genero = 'Masculino')
    / NULLIF(COUNTIF(u.genero IN ('Masculino', 'Feminino')), 0) * 100, 1) AS pct_masc,
  COUNTIF(r.decil >= 7) AS n_decil7mais,
  COUNTIF(c.nivel IN ('4_platinum', '5_amex', '6_black')) AS n_cartao_premium
FROM segmentos s
LEFT JOIN usuario u USING (email)
LEFT JOIN renda r USING (email)
LEFT JOIN cartao c USING (email)
GROUP BY 1
ORDER BY 1
