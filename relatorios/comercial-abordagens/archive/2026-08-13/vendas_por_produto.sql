-- Vendas do canal Comercial por dia e produto (mesma classificação da análise
-- odisseia-lancamento). Janela dinâmica no refresh.py (Q_VENDAS_DIA):
-- últimos 28 dias completos. Snapshot: 16/07–12/08/2026.
SELECT DATE(dt_ordered_at) AS dia,
       CASE
         WHEN nm_gateway_plan='clube-do-livro' OR nm_gateway_plan LIKE 'ebooks%clube%' THEN 'Clube do Livro'
         WHEN nm_gateway_plan='livro-odisseia-edicao-colecionador'
           OR LOWER(nm_gateway_product) LIKE '%odis%' THEN 'Odisseia'
         WHEN nm_gateway_plan LIKE 'mecenas%' THEN 'Mecenas'
         WHEN bl_lifetime_offer THEN 'Vitalício'
         ELSE 'Assinaturas/outros'
       END AS produto,
       COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND DATE(dt_ordered_at) BETWEEN '2026-07-16' AND '2026-08-12'
GROUP BY 1,2 ORDER BY 1,2
