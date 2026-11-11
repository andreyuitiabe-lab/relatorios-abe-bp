-- Números do topo da página.
SELECT COUNT(*) AS pessoas,
  COUNTIF(st0 = 'refunded') AS reemb,
  COUNTIF(up1h) AS up1h, COUNTIF(up_dep) AS up_dep,
  COUNTIF(up1h OR up_dep) AS upsell,
  (SELECT ROUND(SUM(v)) FROM depois) AS receita_depois,
  COUNTIF(tem7d) AS com7d, COUNTIF(tem7d AND h7 > 0) AS assistiu7d,
  ROUND(AVG(IF(tem7d, h7, NULL)), 2) AS h7_media,
  FORMAT_DATETIME('%Y-%m-%d', MIN(t0)) AS t0_min, FORMAT_DATETIME('%Y-%m-%d', MAX(t0)) AS t0_max
FROM pessoa
