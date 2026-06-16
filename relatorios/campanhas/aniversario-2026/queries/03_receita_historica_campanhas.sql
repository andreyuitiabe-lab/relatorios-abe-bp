-- Receita histórica por campanha: BPDay e Black Friday
WITH campanhas AS (
  SELECT 'BPDay 2022'        AS campanha, DATE('2022-07-21') AS dt_ini, DATE('2022-07-21') AS dt_fim
  UNION ALL SELECT 'BPDay 2023',        DATE('2023-07-21'), DATE('2023-07-21')
  UNION ALL SELECT 'BPDay 2024',        DATE('2024-07-25'), DATE('2024-07-31')
  UNION ALL SELECT 'BPDay 2025',        DATE('2025-06-22'), DATE('2025-07-31')
  UNION ALL SELECT 'Black Friday 2023', DATE('2023-11-01'), DATE('2023-11-30')
  UNION ALL SELECT 'Black Friday 2024', DATE('2024-11-01'), DATE('2024-11-30')
)
SELECT
  c.campanha,
  SUM(CASE WHEN t.nm_status = 'approved' THEN t.vl_payment_gross END)                          AS receita_total,
  SUM(CASE WHEN t.nm_status = 'approved' AND t.bl_lifetime_offer = TRUE THEN t.vl_payment_gross END) AS receita_vitalicio,
  COUNT(DISTINCT CASE WHEN t.nm_status = 'approved' AND t.bl_lifetime_offer = TRUE THEN t.id_gateway_customer END) AS compradores_vitalicio_unicos,
  COUNT(DISTINCT CASE WHEN t.nm_status = 'approved' AND t.bl_is_renovation = FALSE THEN t.id_gateway_customer END) AS compradores_novos_total
FROM campanhas c
LEFT JOIN `bp-datawarehouse.masterdata.fct_transactions` t
  ON DATE(t.dt_ordered_at) BETWEEN c.dt_ini AND c.dt_fim
GROUP BY 1
ORDER BY MIN(c.dt_ini);
