-- O que foi vendido com a UTM da live, por degrau de oferta.
-- O checkout da live oferecia Apoiador R$ 1,90/mês, com upgrade para Essencial/Premium e order bump de 2º ano.
SELECT
  CASE
    WHEN bl_is_commercial_channel THEN 'Comercial (vendedor)'
    WHEN nm_gateway_offer LIKE '%R$1,90%' THEN 'Apoiador · 12x R$ 1,90'
    WHEN nm_plan_label LIKE 'Extensao%' THEN 'Order bump · 2º ano'
    WHEN nm_plan_label = 'Básico' OR nm_plan_label LIKE '%Essencial%' THEN 'Essencial · R$ 238,80'
    WHEN nm_plan_label LIKE 'Premium%' THEN 'Premium · R$ 478,80'
    ELSE 'Outros'
  END AS degrau,
  COUNT(*) AS vendas,
  ROUND(SUM(vl_payment_gross)) AS receita,
  ROUND(AVG(vl_payment_gross), 2) AS ticket
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND nm_pptc_utm_content = 'apuracao_eleicoes_04out'
GROUP BY 1
ORDER BY receita DESC
