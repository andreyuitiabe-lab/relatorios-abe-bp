-- Vendas novas por dia (todas e só as da live), 4 semanas antes até o dia seguinte.
SELECT
  CAST(DATE(dt_ordered_at) AS STRING) AS dia,
  COUNT(*) AS vendas,
  ROUND(SUM(vl_payment_gross)) AS receita,
  COUNTIF(nm_pptc_utm_content = 'apuracao_eleicoes_04out') AS vendas_live,
  ROUND(SUM(IF(nm_pptc_utm_content = 'apuracao_eleicoes_04out', vl_payment_gross, 0))) AS receita_live
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND DATE(dt_ordered_at) BETWEEN '2026-09-06' AND '2026-10-05'
GROUP BY 1
ORDER BY 1
