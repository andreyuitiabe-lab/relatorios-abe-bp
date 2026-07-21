-- Vendas de ANÚNCIOS PAGOS com criativo de influenciador (VVS = video de venda).
-- O influ grava o criativo e a mídia paga distribui — venda atribuída ao ad.
-- Identificação: utm_content ou utm_campaign contém 'influ' (excluindo 'sem influs'
-- e criativos temáticos 'VVS influencia' da campanha Banco Master).
-- Nome do influenciador extraído do utm_content no refresh.py.
SELECT
  COALESCE(nm_pptc_utm_content, '')                    AS utm_content,
  COALESCE(nm_pptc_utm_campaign, '')                   AS utm_campaign,
  FORMAT_DATE('%Y-%m', DATE(dt_ordered_at))            AS ano,  -- mês (alias 'ano' mantido p/ refresh.py)
  COALESCE(nm_plan_label, nm_gateway_product, 'outro') AS produto,
  COUNT(*)                                             AS qt,
  ROUND(SUM(vl_payment_gross), 2)                      AS receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND dt_ordered_at >= '2025-01-01'  -- recorte do relatório: 2025 em diante
  AND COALESCE(nm_pptc_tracking_publisher, '') != 'Influencers'
  AND NOT STARTS_WITH(COALESCE(nm_pptc_tracking_name, ''), 'Afiliado')
  AND (
    REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_content, '')), r'influ')
    OR REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_campaign, '')), r'influ')
  )
  AND NOT REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_content, '')), r'sem influ')
  AND NOT REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_campaign, '')), r'sem influ')
  AND NOT REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_content, '')), r'vvs influencia')
GROUP BY 1, 2, 3, 4
ORDER BY receita DESC
