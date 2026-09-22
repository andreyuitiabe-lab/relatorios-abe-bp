-- Vendas por rastro (metodo ELS/ENE) nos 4 primeiros dias — LAC x ENE
WITH tx AS (
  SELECT
    CASE
      WHEN REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_tracking_name,'') || '|' || COALESCE(nm_pptc_utm_campaign,'') || '|' ||
                                 COALESCE(nm_pptc_utm_content,'') || '|' || COALESCE(nm_lead_last_tracking,'')),
                           r'\[lac\]|lacerda') THEN 'LAC'
      WHEN REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_tracking_name,'') || '|' || COALESCE(nm_pptc_utm_campaign,'') || '|' ||
                                 COALESCE(nm_pptc_utm_content,'') || '|' || COALESCE(nm_lead_last_tracking,'')),
                           r'\[ene\]|eneas') THEN 'ENE'
    END AS sigla,
    DATE(dt_ordered_at) AS dt,
    id_transaction, id_gateway_customer, vl_payment_gross
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
    AND (DATE(dt_ordered_at) BETWEEN '2026-09-19' AND '2026-09-22'
      OR DATE(dt_ordered_at) BETWEEN '2026-07-28' AND '2026-07-31')
)
SELECT
  sigla,
  DATE_DIFF(dt, IF(sigla = 'LAC', DATE '2026-09-19', DATE '2026-07-28'), DAY) + 1 AS dia,
  dt,
  COUNT(DISTINCT id_transaction) AS qt_transacoes,
  COUNT(DISTINCT id_gateway_customer) AS qt_compradores,
  ROUND(SUM(vl_payment_gross)) AS vl_receita,
  ROUND(AVG(vl_payment_gross)) AS ticket_medio
FROM tx
WHERE sigla IS NOT NULL
  AND ((sigla = 'LAC' AND dt BETWEEN '2026-09-19' AND '2026-09-22')
    OR (sigla = 'ENE' AND dt BETWEEN '2026-07-28' AND '2026-07-31'))
GROUP BY ROLLUP(sigla, dia, dt)
HAVING sigla IS NOT NULL
ORDER BY sigla, dia NULLS LAST
