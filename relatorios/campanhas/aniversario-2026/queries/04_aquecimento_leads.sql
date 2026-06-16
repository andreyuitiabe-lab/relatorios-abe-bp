-- Volume de leads de aquecimento por campanha (landing page / lead registration)
-- Tabela fonte: bp-lake.marketing.lead_registration
-- Campo de data: ts_registered_at (TIMESTAMP)
WITH periodos AS (
  SELECT 'BPDay 2024' AS campanha, TIMESTAMP('2024-07-19') AS dt_ini, TIMESTAMP('2024-07-24 23:59:59') AS dt_fim
  UNION ALL
  SELECT 'BPDay 2025', TIMESTAMP('2025-06-07'), TIMESTAMP('2025-06-21 23:59:59')
)
SELECT
  p.campanha,
  p.dt_ini,
  p.dt_fim,
  COUNT(*)               AS qt_registros_total,
  COUNT(DISTINCT nm_email) AS qt_leads_unicos
FROM periodos p
LEFT JOIN `bp-lake.marketing.lead_registration` lr
  ON lr.ts_registered_at BETWEEN p.dt_ini AND p.dt_fim
GROUP BY 1, 2, 3
ORDER BY 2;
