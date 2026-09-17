-- Performance diária — vendas aprovadas (não-renovação) por dia × grupo de canal × sigla de campanha × produto.
-- Grupo de canal: Comercial tem precedência (bl_is_commercial_channel); o resto pelo publisher.
-- Sigla: extraída do utm_campaign (bracket ou palavra); 'sem_sigla' quando não casa.
SELECT
  DATE(dt_ordered_at) AS dia,
  CASE
    WHEN bl_is_commercial_channel THEN 'Comercial'
    WHEN nm_pptc_tracking_publisher IN ('Facebook Ads', 'Instagram Ads') THEN 'Ads Meta'
    WHEN nm_pptc_tracking_publisher IN ('Adwords', 'Adwords Remarketing') THEN 'Ads Google'
    WHEN nm_pptc_tracking_publisher IN ('E-mail', 'Message Service', 'WhatsApp') THEN 'CRM'
    WHEN nm_pptc_tracking_publisher IN ('Organic', 'Own Site', 'Member Area') THEN 'Orgânico/Portal'
    WHEN nm_pptc_tracking_publisher = 'YouTube' THEN 'YouTube'
    WHEN nm_pptc_tracking_publisher = 'Influencers' THEN 'Influenciadores'
    ELSE 'Outros/CS'
  END AS canal,
  COALESCE(REGEXP_EXTRACT(UPPER(COALESCE(nm_pptc_utm_campaign, '')),
    r'(?:^|[\[\s_\-])(BP10|TEC|CBR|ELS|ENE|FNC|10R|ODI|CDL|EVG|JOM|MEC|TLR|DOM|BMA|DBI|VIT|FREE|BIT|GEO|ELB26|SDC|FAU)(?:$|[\]\s_\-])'),
    'sem_sigla') AS sigla,
  COALESCE(nm_plan_label, nm_gateway_plan, 'sem plano') AS produto,
  COUNT(*) AS tx,
  ROUND(SUM(vl_payment_gross), 2) AS receita
FROM masterdata.fct_transactions
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND DATE(dt_ordered_at) BETWEEN '2026-05-01' AND '2026-09-13'
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4
