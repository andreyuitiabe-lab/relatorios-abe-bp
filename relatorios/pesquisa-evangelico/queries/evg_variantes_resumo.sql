-- Resumo por variante de landing page — campanha EVG
-- Variante extraída do path da URL: /cadastro-o-brasil-evangelico/[letra]
-- Separação checkout normal vs. página de confirmação feita somente no SELECT final

WITH

lead_registration_raw AS (
  SELECT
    *,
    LOWER(TRIM(nm_email)) AS nm_email_clean,
    ROW_NUMBER() OVER (
      PARTITION BY LOWER(TRIM(nm_email))
      ORDER BY ts_registered_at ASC
    ) AS global_rank
  FROM `bp-lake.marketing.lead_registration`
  WHERE nm_tag = 'EVG'
    AND ts_registered_at IS NOT NULL
),

lead_registration AS (
  SELECT
    * EXCEPT (nm_email, nm_email_clean, global_rank),
    nm_email_clean AS nm_email,
    global_rank    AS cd_global_rank,
    DATETIME(TIMESTAMP(ts_registered_at), 'America/Sao_Paulo') AS dt_registered_at_br
  FROM lead_registration_raw
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY nm_email_clean, nm_tag
    ORDER BY ts_registered_at ASC
  ) = 1
),

leads AS (
  SELECT
    nm_email,
    dt_registered_at_br,
    COALESCE(
      REGEXP_EXTRACT(nm_url, r'/cadastro-o-brasil-evangelico/([a-z])\?'),
      '(base)'
    ) AS variante
  FROM lead_registration
),

all_approved_transactions AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY nm_email
      ORDER BY dt_ordered_at ASC
    ) AS vl_numero_da_venda,
    CASE
      WHEN nm_plan_label = 'Outros' THEN nm_gateway_product
      ELSE nm_plan_label
    END AS nm_plan
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` USING (id_gateway_customer)
  WHERE nm_status = 'approved'
),

sales_last_click AS (
  SELECT
    t.nm_email,
    t.id_transaction,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.nm_pptc_checkout_name,
    l.variante
  FROM all_approved_transactions AS t
  INNER JOIN leads AS l
    ON t.nm_email = l.nm_email
    AND t.dt_ordered_at >= l.dt_registered_at_br
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY t.id_transaction
    ORDER BY l.dt_registered_at_br DESC
  ) = 1
)

SELECT
  l.variante,
  COUNT(DISTINCT l.nm_email)                                                               AS cadastros,
  COUNTIF(sc.id_transaction IS NOT NULL
    AND NOT CONTAINS_SUBSTR(LOWER(sc.nm_pptc_checkout_name), 'confirmac'))                AS conversoes_checkout,
  ROUND(SUM(IF(NOT CONTAINS_SUBSTR(LOWER(sc.nm_pptc_checkout_name), 'confirmac'),
    sc.vl_payment_gross, 0)), 2)                                                           AS receita_checkout,
  COUNTIF(CONTAINS_SUBSTR(LOWER(sc.nm_pptc_checkout_name), 'confirmac'))                  AS conversoes_confirmacao,
  ROUND(SUM(IF(CONTAINS_SUBSTR(LOWER(sc.nm_pptc_checkout_name), 'confirmac'),
    sc.vl_payment_gross, 0)), 2)                                                           AS receita_confirmacao
FROM leads AS l
LEFT JOIN sales_last_click AS sc USING (variante)
GROUP BY 1
ORDER BY 1
