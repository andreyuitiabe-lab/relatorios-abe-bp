-- Anúncios do Meta desde {INI}, um registro por anúncio. O refresh.py filtra os que têm influ no nome.
SELECT CAST(id_advertising AS STRING) ad_id, ANY_VALUE(nm_ad_name) anuncio, ANY_VALUE(nm_campaign_name) campanha_meta,
  ROUND(SUM(COALESCE(vl_amount_spent,0)),2) gasto, ROUND(SUM(COALESCE(vl_total_revenue,0)),2) receita,
  SUM(COALESCE(qt_total_sales,0)) vendas, COUNTIF(COALESCE(qt_impressions,0)>0) dias_no_ar,
  SUM(COALESCE(qt_impressions,0)) impressoes, SUM(COALESCE(qt_outbound_clicks,0)) cliques,
  SUM(COALESCE(qt_three_second_views,0)) views_3s, SUM(COALESCE(qt_thruplays,0)) thruplays,
  SUM(COALESCE(qt_leads,0)) leads,
  CAST(MIN(IF(qt_impressions>0, reference_date, NULL)) AS STRING) primeiro_dia,
  CAST(MAX(IF(qt_impressions>0, reference_date, NULL)) AS STRING) ultimo_dia
FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
WHERE reference_date >= '{INI}'
GROUP BY ad_id
HAVING gasto > 0 OR receita > 0
