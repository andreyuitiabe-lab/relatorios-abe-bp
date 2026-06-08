-- Clientes únicos com renovação recusada por Saldo Insuficiente (últimos 12 meses)
--
-- ⚠️ CONFIRMAR: o campo/valor exato que identifica "Saldo Insuficiente"
-- Possibilidades: nm_status_reason, nm_error_code, nm_refuse_reason
-- Rodar antes: SELECT DISTINCT <campo_status_recusa>, COUNT(*) FROM ... para descobrir o campo
--
-- Assumindo que transações recusadas têm nm_status != 'approved' e bl_is_renovation = TRUE
-- Ajustar filtro de status_reason conforme o campo real da tabela.

SELECT
  t.id_gateway_customer,
  t.nm_gateway_plan,
  t.nm_plan_label,
  MIN(DATE(t.dt_ordered_at)) AS dt_primeira_falha,
  MAX(DATE(t.dt_ordered_at)) AS dt_ultima_falha,
  COUNT(*)                   AS total_tentativas_recusadas
FROM `bp-datawarehouse.masterdata.fct_transactions` t
WHERE
  DATE(t.dt_ordered_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
  AND t.bl_is_renovation = TRUE
  AND t.nm_status != 'approved'
  -- SUBSTITUIR pelo filtro real de "Saldo Insuficiente":
  -- AND LOWER(t.nm_status_reason) LIKE '%saldo insuficiente%'
  -- AND LOWER(t.nm_status_reason) LIKE '%insufficient%'
  AND t.nm_gateway_plan IN ('good', 'supporter', 'best')  -- Básico, Apoiador, Premium GBB
GROUP BY 1, 2, 3
ORDER BY total_tentativas_recusadas DESC
