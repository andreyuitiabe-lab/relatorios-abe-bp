-- Compradores únicos e ticket médio de Vitalício por tier e por campanha
SELECT
  CASE
    WHEN DATE(dt_ordered_at) BETWEEN '2023-11-01' AND '2023-11-30' THEN 'BF 2023'
    WHEN DATE(dt_ordered_at) BETWEEN '2024-07-25' AND '2024-07-31' THEN 'BPDay 2024'
    WHEN DATE(dt_ordered_at) BETWEEN '2024-11-01' AND '2024-11-30' THEN 'BF 2024'
    WHEN DATE(dt_ordered_at) BETWEEN '2025-06-22' AND '2025-07-31' THEN 'BPDay 2025'
  END AS campanha,
  nm_plan_label,
  COUNT(DISTINCT id_gateway_customer) AS compradores_unicos,
  AVG(vl_payment_gross)               AS ticket_medio,
  SUM(vl_payment_gross)               AS receita_total
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE bl_lifetime_offer = TRUE
  AND nm_status = 'approved'
  AND (
    (DATE(dt_ordered_at) BETWEEN '2023-11-01' AND '2023-11-30')
    OR (DATE(dt_ordered_at) BETWEEN '2024-07-25' AND '2024-07-31')
    OR (DATE(dt_ordered_at) BETWEEN '2024-11-01' AND '2024-11-30')
    OR (DATE(dt_ordered_at) BETWEEN '2025-06-22' AND '2025-07-31')
  )
GROUP BY 1, 2
ORDER BY 1, receita_total DESC;
