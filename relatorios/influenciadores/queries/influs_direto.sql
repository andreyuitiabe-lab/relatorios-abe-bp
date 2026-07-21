-- Vendas DIRETAS por links de influenciadores/parceiros
-- Fonte: fct_transactions com nm_pptc_tracking_publisher = 'Influencers'
--        (classificação de canal da própria base) + trackings 'Afiliado - <nome>'
--        (programa de afiliados 2020-21, publisher variado)
-- Exclui renovações; só transações aprovadas. Nome do influenciador é extraído
-- do tracking_name/utm_source no refresh.py (regex).
SELECT
  COALESCE(nm_pptc_tracking_name, '')                 AS tracking_name,
  COALESCE(nm_utm_source, '')                         AS utm_source,
  COALESCE(nm_pptc_utm_content, '')                   AS utm_content,  -- publi 2025+: handle do influ (ex: tiba_camargo)
  FORMAT_DATE('%Y-%m', DATE(dt_ordered_at))           AS ano,  -- mês (alias 'ano' mantido p/ refresh.py)
  COALESCE(nm_plan_label, nm_gateway_product, 'outro') AS produto,
  COUNT(*)                                            AS qt,
  ROUND(SUM(vl_payment_gross), 2)                     AS receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND dt_ordered_at >= '2025-01-01'  -- recorte do relatório: 2025 em diante
  AND (
    nm_pptc_tracking_publisher = 'Influencers'
    OR STARTS_WITH(COALESCE(nm_pptc_tracking_name, ''), 'Afiliado')
  )
GROUP BY 1, 2, 3, 4, 5
ORDER BY receita DESC
