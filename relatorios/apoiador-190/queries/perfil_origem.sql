-- Quem compra (perfil antes da compra) × por onde chegou, com a taxa de upsell de cada grupo por canal.
-- up_dep = qualquer upsell posterior; up_digital_depois = posterior sem Lambda nem vendedor.
SELECT entrada, seg, COUNT(*) AS pessoas, COUNTIF(up1h) AS up1h, COUNTIF(up_dep) AS up_dep,
  COUNTIF(up_lambda) AS up_lambda, COUNTIF(up_humano) AS up_humano,
  COUNTIF(up_dep AND NOT up_lambda AND NOT up_humano) AS up_digital_depois,
  COUNTIF(up1h OR up_dep) AS upsell
FROM pessoa
GROUP BY 1, 2
