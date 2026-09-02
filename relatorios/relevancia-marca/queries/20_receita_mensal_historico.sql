-- Receita/vendas mensais 2021-09 → 2026-08 para backtest do Share of Search (Fase 1)
SELECT
  DATE_TRUNC(DATE(dt_ordered_at), MONTH) AS mes,
  COUNT(*) AS tx,
  ROUND(SUM(vl_payment_gross)) AS receita,
  COUNTIF(bl_is_first_subscription_transaction) AS primeiras_compras,
  ROUND(SUM(IF(bl_is_first_subscription_transaction, vl_payment_gross, 0))) AS receita_novos
FROM masterdata.fct_transactions
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND DATE(dt_ordered_at) BETWEEN '2021-09-01' AND '2026-08-20'
GROUP BY 1 ORDER BY 1
