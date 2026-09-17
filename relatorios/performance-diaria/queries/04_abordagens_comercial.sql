-- Performance diária — esforço do Comercial: abordagens Zenvia por dia (⚠️ recarga de 08/09 perdeu ~72% de 01–04/09).
SELECT DATE(dt_approach_start) AS dia, COUNT(*) AS abordagens,
       COUNT(DISTINCT cd_cleaned_phone_number) AS pessoas_abordadas
FROM datamart.dtm_sales_by_zenvia
WHERE DATE(dt_approach_start) BETWEEN '2026-05-01' AND '2026-09-13'
GROUP BY 1 ORDER BY 1
