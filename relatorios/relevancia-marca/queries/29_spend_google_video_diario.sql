-- RODADA 9a (auditoria, ponto 6) — spend diário do Google separado por tipo de campanha,
-- para testar se o "Organic Video" do GA4 anda com o spend de VÍDEO/YouTube (contaminação
-- de mídia paga mal taggeada), e não só com o spend agregado.
-- Tipo pela nomenclatura de campanha (canais.md): [YT] = YouTube, PMAX = Performance Max,
-- DISPLAY, [KW]/Institucional = busca de marca; resto = outros (busca genérica etc.).
SELECT
  DATE(reference_date) AS dia,
  ROUND(SUM(IF(REGEXP_CONTAINS(UPPER(nm_campaign_name), r'\[YT\]|YOUTUBE|VIDEO|VÍDEO'), vl_amount_spent, 0))) AS spend_g_video,
  ROUND(SUM(IF(REGEXP_CONTAINS(UPPER(nm_campaign_name), r'PMAX|P-MAX|PERFORMANCE'), vl_amount_spent, 0))) AS spend_g_pmax,
  ROUND(SUM(IF(REGEXP_CONTAINS(UPPER(nm_campaign_name), r'DISPLAY|DEMAND'), vl_amount_spent, 0))) AS spend_g_display,
  ROUND(SUM(IF(REGEXP_CONTAINS(UPPER(nm_campaign_name), r'\[KW\]|INSTITUCIONAL|MARCA|BRAND'), vl_amount_spent, 0))) AS spend_g_marca,
  ROUND(SUM(vl_amount_spent)) AS spend_g_total,
  SUM(IF(REGEXP_CONTAINS(UPPER(nm_campaign_name), r'\[YT\]|YOUTUBE|VIDEO|VÍDEO'), qt_views, 0)) AS views_g_video
FROM datamart.dtm_analytics_google_ads_funnel
WHERE DATE(reference_date) BETWEEN '2025-08-01' AND '2026-09-13'
GROUP BY 1
ORDER BY 1
