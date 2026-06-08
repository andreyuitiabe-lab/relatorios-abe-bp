-- Taxa de recuperação atual: clientes com falha por Saldo Insuficiente
-- que fizeram uma transação aprovada nos 90 dias seguintes à primeira falha.
-- Representa o resultado do processo atual (comercial + remarketing CRM).
--
-- ⚠️ Depende da query 01 — substituir o CTE `falhas` pelos resultados reais,
-- ou materializar a query 01 em tabela temporária antes de rodar esta.

WITH falhas AS (
  -- Copiar resultado da query 01 aqui, ou referenciar tabela materializada
  SELECT
    t.id_gateway_customer,
    t.nm_gateway_plan,
    t.nm_plan_label,
    MIN(DATE(t.dt_ordered_at)) AS dt_primeira_falha
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE
    DATE(t.dt_ordered_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
    AND t.bl_is_renovation = TRUE
    AND t.nm_status != 'approved'
    -- AND LOWER(t.nm_status_reason) LIKE '%saldo insuficiente%'
    AND t.nm_gateway_plan IN ('good', 'supporter', 'best')
  GROUP BY 1, 2, 3
),

recuperacoes AS (
  SELECT DISTINCT
    f.id_gateway_customer,
    f.nm_gateway_plan
  FROM falhas f
  JOIN `bp-datawarehouse.masterdata.fct_transactions` t
    ON  f.id_gateway_customer = t.id_gateway_customer
    AND DATE(t.dt_ordered_at) > f.dt_primeira_falha
    AND DATE(t.dt_ordered_at) <= DATE_ADD(f.dt_primeira_falha, INTERVAL 90 DAY)
    AND t.nm_status = 'approved'
    AND t.bl_is_renovation = TRUE  -- renovou (não comprou outro produto)
),

resumo AS (
  SELECT
    f.nm_gateway_plan,
    f.nm_plan_label,
    COUNT(DISTINCT f.id_gateway_customer)  AS clientes_com_falha,
    COUNT(DISTINCT r.id_gateway_customer)  AS recuperados_90d,
    ROUND(
      SAFE_DIVIDE(
        COUNT(DISTINCT r.id_gateway_customer),
        COUNT(DISTINCT f.id_gateway_customer)
      ), 3
    )                                       AS taxa_recuperacao
  FROM falhas f
  LEFT JOIN recuperacoes r USING (id_gateway_customer, nm_gateway_plan)
  GROUP BY 1, 2
)

SELECT
  nm_gateway_plan,
  nm_plan_label,
  clientes_com_falha,
  recuperados_90d,
  clientes_com_falha - recuperados_90d AS nao_recuperados,
  taxa_recuperacao,

  -- Receita atual: recuperados × valor anual do plano
  CASE nm_gateway_plan
    WHEN 'supporter' THEN recuperados_90d * 120
    WHEN 'good'      THEN recuperados_90d * 228
    WHEN 'best'      THEN recuperados_90d * 708
  END AS receita_atual_recuperada,

  -- Receita perdida: não recuperados × valor anual
  CASE nm_gateway_plan
    WHEN 'supporter' THEN (clientes_com_falha - recuperados_90d) * 120
    WHEN 'good'      THEN (clientes_com_falha - recuperados_90d) * 228
    WHEN 'best'      THEN (clientes_com_falha - recuperados_90d) * 708
  END AS receita_perdida_estimada

FROM resumo
ORDER BY clientes_com_falha DESC
