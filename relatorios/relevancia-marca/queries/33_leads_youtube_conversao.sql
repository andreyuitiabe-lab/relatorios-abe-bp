-- RODADA 9b — o lead captado por vídeo do YouTube converte na campanha? Por campanha (nm_tag) × fonte,
-- mesma janela de cadastro: leads, conversão em ≤60d, receita e RPL. Fonte pelo utm_source/medium.
WITH l AS (
  SELECT nm_tag, nm_email, DATE(dt_registered_at) dt,
    CASE WHEN LOWER(utm_source)='organic_youtube' OR LOWER(utm_medium)='programas' THEN '1 youtube_organico'
         WHEN LOWER(utm_source)='live_youtube' THEN '2 youtube_live'
         WHEN LOWER(utm_source) LIKE '%fb%' OR LOWER(utm_source) LIKE '%facebook%' OR LOWER(utm_source) LIKE '%ig%' OR LOWER(utm_source) LIKE '%meta%' OR LOWER(utm_medium) LIKE '%facebook%' THEN '3 meta_ads'
         WHEN LOWER(utm_source) LIKE '%google%' OR LOWER(utm_source) LIKE '%youtube%' THEN '4 google_youtube_ads'
         ELSE '5 outros' END fonte,
    (SELECT COUNT(*) FROM UNNEST(arr_st_approved_transactions) t WHERE t.days_to_purchase BETWEEN 0 AND 60) tx60,
    (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t WHERE t.days_to_purchase BETWEEN 0 AND 60) rec60,
    (SELECT MIN(t.days_to_purchase) FROM UNNEST(arr_st_approved_transactions) t WHERE t.days_to_purchase BETWEEN 0 AND 60) d1
  FROM datamart.dtm_analytics_lead_conversion
  WHERE DATE(dt_registered_at) BETWEEN '2025-08-01' AND '2026-07-16'  -- cadastros com 60d de maturação até 15/09
),
tags AS (SELECT nm_tag FROM l WHERE fonte='1 youtube_organico' GROUP BY 1 HAVING COUNT(DISTINCT nm_email) >= 300)
SELECT nm_tag, fonte, COUNT(DISTINCT nm_email) leads, COUNTIF(tx60>0) convertidos,
  ROUND(100*COUNTIF(tx60>0)/COUNT(DISTINCT nm_email),2) conv_pct,
  ROUND(SUM(COALESCE(rec60,0))) receita60, ROUND(SUM(COALESCE(rec60,0))/COUNT(DISTINCT nm_email),2) rpl,
  APPROX_QUANTILES(d1, 2)[OFFSET(1)] mediana_dias
FROM l WHERE nm_tag IN (SELECT nm_tag FROM tags)
GROUP BY 1,2 ORDER BY 1,2
