-- Modelo de cenários: projeção de receita com downgrade anual → mensal
-- para os clientes NÃO recuperados pelo processo atual (comercial + CRM)
--
-- Inputs (preencher com resultados da query 02):
--   @clientes_nao_recuperados_supporter = ?
--   @clientes_nao_recuperados_good      = ?
--   @clientes_nao_recuperados_best      = ?
--
-- Cenários de taxa de adesão ao plano mensal: 40%, 60%, 80%
-- Cenário de retenção média (meses pagos): 9 meses
-- (ajustar se houver dados históricos de retenção mensal pós-upgrade)

WITH nao_recuperados AS (
  -- Preencher com resultados reais da query 02
  SELECT 'supporter' AS nm_gateway_plan, 10   AS preco_mensal, 0 AS clientes  -- substituir 0
  UNION ALL
  SELECT 'good',                          19,                  0               -- substituir 0
  UNION ALL
  SELECT 'best',                          59,                  0               -- substituir 0
),

cenarios AS (
  SELECT
    nm_gateway_plan,
    preco_mensal,
    clientes,
    taxa_adesao,
    meses_retidos,
    ROUND(clientes * taxa_adesao * meses_retidos * preco_mensal) AS receita_projetada
  FROM nao_recuperados
  CROSS JOIN UNNEST([0.40, 0.60, 0.80]) AS taxa_adesao
  CROSS JOIN UNNEST([9, 12]) AS meses_retidos
)

SELECT
  nm_gateway_plan,
  preco_mensal,
  clientes                                  AS clientes_nao_recuperados,
  ROUND(taxa_adesao * 100)                  AS taxa_adesao_pct,
  meses_retidos,
  receita_projetada,
  -- Comparativo: receita se tivessem renovado anual (100% deles)
  CASE nm_gateway_plan
    WHEN 'supporter' THEN clientes * 120
    WHEN 'good'      THEN clientes * 228
    WHEN 'best'      THEN clientes * 708
  END AS receita_teto_anual
FROM cenarios
ORDER BY nm_gateway_plan, taxa_adesao_pct, meses_retidos
