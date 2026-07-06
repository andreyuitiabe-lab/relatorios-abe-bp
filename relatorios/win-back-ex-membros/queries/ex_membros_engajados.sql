-- Win-back: ex-membros (churn 2026-05-01 a 2026-06-15) com alto engajamento,
-- não abordados pelo Comercial nos últimos 30 dias.
-- Engajamento = horas totais assistidas durante a assinatura; corte = quartil superior (P75).
-- Exclusões high-ticket pedidas: Mecenas, CEC-BP, Retiro BP, Vitalícios, Clube do Livro
-- (triple-check email + telefone + CPF). NÃO exclui Black/certificações de propósito.
-- Exclusões padrão de lista comercial: Zenvia (30d), Pipedrive (30d), blacklist.

WITH ex_members AS (
  SELECT
    s.id_user,
    s.id_gateway_customer,
    s.nm_gateway_plan,
    s.nm_plan_label,
    s.dt_started_at,
    s.dt_expires_in
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  WHERE s.bl_is_last_user_subscription = TRUE
    AND s.nm_type = 'paid'
    AND s.nm_status IN ('canceled', 'expired')
    AND DATE(s.dt_expires_in) BETWEEN '2026-05-01' AND '2026-06-15'
),

engagement AS (
  SELECT
    e.id_user,
    SUM(v.vl_watch_time_seconds) / 3600 AS hours_watched
  FROM ex_members e
  JOIN `bp-datawarehouse.datamart.obt_kafka__view_sessions` v
    ON v.id_user = e.id_user
   AND v.dt_created_at BETWEEN e.dt_started_at AND e.dt_expires_in
  GROUP BY e.id_user
),

threshold AS (
  SELECT APPROX_QUANTILES(hours_watched, 100)[OFFSET(75)] AS cut
  FROM engagement
),

engaged AS (
  SELECT e.id_user, e.hours_watched
  FROM engagement e, threshold t
  WHERE e.hours_watched >= t.cut
),

base AS (
  SELECT
    em.id_user,
    em.id_gateway_customer,
    em.nm_gateway_plan,
    em.nm_plan_label,
    em.dt_expires_in,
    g.hours_watched,
    c.nm_name,
    c.nm_email,
    c.cd_cleaned_phone_number,
    c.cd_cpf
  FROM ex_members em
  JOIN engaged g ON g.id_user = em.id_user
  JOIN `bp-datawarehouse.masterdata.dim_contact` c
    ON c.id_gateway_customer = em.id_gateway_customer
),

high_ticket AS (
  SELECT DISTINCT
    c.nm_email,
    c.cd_cleaned_phone_number,
    c.cd_cpf
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c
    ON c.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND (
      t.nm_gateway_plan LIKE 'mecenas%'                            -- Mecenas
      OR t.bl_lifetime_offer = TRUE                                -- Vitalícios
      OR t.nm_plan_label LIKE '%Vitalício%'
      OR LOWER(t.nm_gateway_product) LIKE '%conselho editorial%'   -- CEC-BP
      OR LOWER(t.nm_gateway_product) LIKE '%retiro%'               -- Retiro BP
      OR LOWER(t.nm_gateway_product) LIKE '%clube do livro%'       -- Clube do Livro
      OR t.nm_gateway_plan = 'clube-do-livro'
    )
),

zenvia AS (
  SELECT cd_cleaned_phone_number
  FROM `bp-datawarehouse.datamart.dtm_sales_by_zenvia`
  WHERE nm_last_prospect_status = 'followUp'
     OR nm_gateway_plan LIKE 'mecenas%'
     OR dt_approach_end >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY cd_cleaned_phone_number ORDER BY dt_approach_end DESC
  ) = 1
),

pipedrive AS (
  SELECT cd_person_phone_number
  FROM `bp-datawarehouse.datamart.dtm_pipedrive_analytics`
  WHERE nm_status = 'OPEN'
     OR nm_pipeline LIKE '%MECENAS%'
     OR nm_stage LIKE '%MECENAS%'
     OR dt_created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY cd_person_phone_number ORDER BY dt_created_at DESC
  ) = 1
),

blacklist AS (
  SELECT string_field_1 AS nm_email
  FROM `bp-staging.dbt_cherete.tb_black_list_crm`
)

SELECT
  base.nm_name,
  base.nm_email,
  base.cd_cleaned_phone_number,
  base.nm_gateway_plan,
  base.nm_plan_label,
  DATE(base.dt_expires_in) AS dt_perdeu_acesso,
  ROUND(base.hours_watched, 1) AS horas_assistidas
FROM base
LEFT JOIN high_ticket h1 ON h1.nm_email = base.nm_email AND base.nm_email IS NOT NULL
LEFT JOIN high_ticket h2 ON h2.cd_cleaned_phone_number = base.cd_cleaned_phone_number AND base.cd_cleaned_phone_number IS NOT NULL
LEFT JOIN high_ticket h3 ON h3.cd_cpf = base.cd_cpf AND base.cd_cpf IS NOT NULL
LEFT JOIN zenvia z ON z.cd_cleaned_phone_number = base.cd_cleaned_phone_number
LEFT JOIN pipedrive pd ON pd.cd_person_phone_number = base.cd_cleaned_phone_number
LEFT JOIN blacklist bl ON bl.nm_email = base.nm_email
WHERE h1.nm_email IS NULL AND h2.cd_cleaned_phone_number IS NULL AND h3.cd_cpf IS NULL
  AND z.cd_cleaned_phone_number IS NULL
  AND pd.cd_person_phone_number IS NULL
  AND bl.nm_email IS NULL
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY
    COALESCE(base.nm_email, CONCAT('__noemail__', base.id_gateway_customer)),
    COALESCE(base.cd_cleaned_phone_number, CONCAT('__nofone__', base.id_gateway_customer)),
    COALESCE(base.cd_cpf, CONCAT('__nocpf__', base.id_gateway_customer))
  ORDER BY base.hours_watched DESC
) = 1
ORDER BY horas_assistidas DESC
