-- Coorte por semana da compra: o one-click digital só passou a existir no início de novembro.
-- Semanas recentes ainda não tiveram tempo de upsell posterior (coorte imatura).
SELECT FORMAT_DATE('%Y-%m-%d', DATE_TRUNC(DATE(t0), WEEK(MONDAY))) AS semana, COUNT(*) AS pessoas,
  COUNTIF(st0 = 'refunded') AS reemb, COUNTIF(up1h) AS up1h,
  COUNTIF(up_lambda) AS up_lambda, COUNTIF(up_humano) AS up_humano,
  COUNTIF(up_dep AND NOT up_lambda AND NOT up_humano) AS up_digital_depois
FROM pessoa
GROUP BY 1 ORDER BY 1
