-- Sinal de recência/frequência de cadastro → conversão
-- Cohort: leads registrados em 2025 (maturidade ≥ 6 meses), por status no cadastro
WITH base AS (
  SELECT
    nm_email,
    nm_tag,
    dt_registered_at_br,
    numero_do_cadastro,
    lead_status_at_registration AS status,
    bl_converted,
    DATETIME_DIFF(
      dt_registered_at_br,
      LAG(dt_registered_at_br) OVER (PARTITION BY nm_email ORDER BY dt_registered_at_br),
      DAY
    ) AS dias_desde_cadastro_anterior
  FROM `bp-staging.dbt_abe.tb_leads_qualification_base`
),

cohort AS (
  SELECT
    *,
    CASE
      WHEN numero_do_cadastro = 1 THEN '0_primeiro_cadastro'
      WHEN dias_desde_cadastro_anterior IS NULL THEN '1_recadastro_anterior_pre2025'
      WHEN dias_desde_cadastro_anterior <= 30 THEN '2_recadastro_ate_30d'
      WHEN dias_desde_cadastro_anterior <= 90 THEN '3_recadastro_31_90d'
      WHEN dias_desde_cadastro_anterior <= 180 THEN '4_recadastro_91_180d'
      WHEN dias_desde_cadastro_anterior <= 365 THEN '5_recadastro_181_365d'
      ELSE '6_recadastro_mais_365d'
    END AS bucket_recencia,
    CASE
      WHEN numero_do_cadastro = 1 THEN '1'
      WHEN numero_do_cadastro = 2 THEN '2'
      WHEN numero_do_cadastro <= 4 THEN '3-4'
      ELSE '5+'
    END AS bucket_frequencia
  FROM base
  WHERE DATE(dt_registered_at_br) BETWEEN '2025-01-01' AND '2025-12-31'
)

SELECT
  status,
  bucket_recencia,
  COUNT(*) AS leads,
  SUM(bl_converted) AS convertidos,
  ROUND(SAFE_DIVIDE(SUM(bl_converted), COUNT(*)) * 100, 2) AS conv_pct
FROM cohort
GROUP BY 1, 2

UNION ALL

SELECT
  status,
  'freq_' || bucket_frequencia,
  COUNT(*),
  SUM(bl_converted),
  ROUND(SAFE_DIVIDE(SUM(bl_converted), COUNT(*)) * 100, 2)
FROM cohort
GROUP BY 1, 2
ORDER BY status, bucket_recencia;
