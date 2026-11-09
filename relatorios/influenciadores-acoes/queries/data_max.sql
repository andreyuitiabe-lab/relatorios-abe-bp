-- Último dia com gasto no Meta (o dia corrente costuma vir parcial).
SELECT CAST(MAX(reference_date) AS STRING) d
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE reference_date >= DATE_SUB(CURRENT_DATE('America/Sao_Paulo'), INTERVAL 10 DAY) AND vl_amount_spent > 0
