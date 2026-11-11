-- O que compram depois: plano, quando e por qual canal (pessoas distintas e receita).
SELECT tipo,
  CASE WHEN min_apos <= 60 THEN 'até 1h' WHEN min_apos <= 1440 THEN '1h–24h' WHEN min_apos <= 10080 THEN '1–7 dias' ELSE 'mais de 7 dias' END AS janela,
  CASE WHEN NOT com THEN 'Digital' WHEN lambda THEN 'Lambda (IA WhatsApp)' ELSE 'Vendedor humano' END AS canal,
  COUNT(DISTINCT e) AS pessoas, COUNT(*) AS compras, ROUND(SUM(v)) AS receita
FROM depois
GROUP BY 1, 2, 3
