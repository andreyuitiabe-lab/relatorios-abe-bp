-- Consumo na 1ª semana × upsell posterior. Só quem já completou 7 dias e não subiu no one-click.
-- Correlação: quem consome mais pode já ser quem estava mais propenso a subir.
SELECT CASE WHEN h7 = 0 THEN '1 nada' WHEN h7 < 1 THEN '2 menos de 1h' WHEN h7 < 3 THEN '3 1–3h' ELSE '4 3h ou mais' END AS faixa,
  COUNT(*) AS pessoas, COUNTIF(up_dep) AS subiram
FROM pessoa
WHERE tem7d AND NOT up1h
GROUP BY 1 ORDER BY 1
