-- Placar D1–D6 alinhado: CDL (D1=2026-05-05) vs Odisseia (D1=2026-07-17), por canal.
-- Versão parametrizada usada pelo refresh.py (Q_PLACAR).
WITH vendas AS (
  SELECT 'CDL' AS campanha,
         DATE_DIFF(DATE(dt_ordered_at), DATE '2026-05-05', DAY)+1 AS dia_campanha,
         CASE WHEN bl_is_commercial_channel THEN 'comercial' ELSE 'digital' END AS canal,
         vl_payment_gross
  FROM masterdata.fct_transactions
  WHERE DATE(dt_ordered_at) >= '2026-05-05'
    AND nm_status='approved' AND bl_is_renovation = FALSE
    AND nm_gateway_plan='clube-do-livro' AND nm_gateway_product NOT LIKE '%Bundle%'
  UNION ALL
  SELECT 'ODI',
         DATE_DIFF(DATE(dt_ordered_at), DATE '2026-07-17', DAY)+1,
         CASE WHEN bl_is_commercial_channel THEN 'comercial' ELSE 'digital' END,
         vl_payment_gross
  FROM masterdata.fct_transactions
  WHERE DATE(dt_ordered_at) >= '2026-07-17'
    AND nm_status='approved' AND bl_is_renovation = FALSE
    AND (nm_gateway_plan='livro-odisseia-edicao-colecionador' OR LOWER(nm_gateway_product) LIKE '%odis%')
)
SELECT campanha, dia_campanha, canal,
       COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM vendas
WHERE dia_campanha BETWEEN 1 AND 6
GROUP BY 1,2,3
ORDER BY dia_campanha, campanha, canal
