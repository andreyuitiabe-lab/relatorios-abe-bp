-- Abordagens comerciais (Zenvia) por dia — denominador de esforço do Comercial
-- Conversão por abordagem = vendas comerciais do dia (query 02) ÷ abordagens do dia
SELECT
  DATE(dt_approach_start) AS dia,
  COUNT(*) AS abordagens,
  COUNT(DISTINCT cd_cleaned_phone_number) AS pessoas_abordadas,
  COUNTIF(id_transaction IS NOT NULL) AS abordagens_com_venda
FROM datamart.dtm_sales_by_zenvia
WHERE DATE(dt_approach_start) BETWEEN '2025-08-01' AND '2026-08-20'
GROUP BY 1
ORDER BY 1
