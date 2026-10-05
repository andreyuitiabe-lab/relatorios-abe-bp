-- Vendas novas com a UTM da live em blocos de 5 min. dt_ordered_at já está em horário de Brasília.
SELECT
  FORMAT_DATETIME('%Y-%m-%d %H:%M', DATETIME_SUB(DATETIME_TRUNC(dt_ordered_at, MINUTE), INTERVAL MOD(EXTRACT(MINUTE FROM dt_ordered_at), 5) MINUTE)) AS bloco,
  COUNT(*) AS vendas,
  ROUND(SUM(vl_payment_gross), 2) AS receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND nm_pptc_utm_content = 'apuracao_eleicoes_04out'
GROUP BY 1
ORDER BY 1
