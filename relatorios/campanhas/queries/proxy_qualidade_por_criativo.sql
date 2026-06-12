-- Campanhas: proxy de qualidade de leads por criativo (Meta Ads)
-- Proxy = % decil7+ entre leads com dados em dim_user (cobertura ~15% para Não Membros)
-- Usar para ranking relativo entre criativos DENTRO de uma campanha — não entre campanhas

WITH

leads_campanha AS (
  SELECT
    lr.nm_email,
    lr.nm_tag                                    AS campanha,
    -- campo de criativo disponível via dtm_analytics_facebook_ads_funnel:
    fa.ad_name                                   AS criativo,
    fa.adset_name                                AS conjunto
  FROM `bp-datawarehouse.bp-lake.marketing.lead_registration` lr
  LEFT JOIN `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel` fa
    ON fa.nm_email = lr.nm_email
    AND fa.nm_campaign_tag = lr.nm_tag
  WHERE lr.nm_tag = 'ELS'  -- <-- trocar para a campanha desejada
    AND lr.nm_email IS NOT NULL
),

perfil AS (
  SELECT
    u.nm_email,
    pp.cd_income_decile
  FROM `bp-datawarehouse.masterdata.dim_user` u
  LEFT JOIN `bp-datawarehouse.datamart.dtm_purchasing_power` pp
    ON pp.id_user = u.id_user
  WHERE u.nm_email IS NOT NULL
)

SELECT
  lc.criativo,
  lc.conjunto,
  COUNT(*)                                                                                          AS total_leads,
  COUNTIF(p.nm_email IS NOT NULL)                                                                   AS leads_com_dados,
  ROUND(COUNTIF(p.nm_email IS NOT NULL) / COUNT(*) * 100, 1)                                        AS pct_cobertura,
  ROUND(AVG(CASE WHEN p.cd_income_decile > 0 THEN p.cd_income_decile END), 2)                       AS decil_medio,
  ROUND(COUNTIF(p.cd_income_decile >= 7) / NULLIF(COUNTIF(p.cd_income_decile > 0), 0) * 100, 1)    AS proxy_pct_decil7plus
FROM leads_campanha lc
LEFT JOIN perfil p ON p.nm_email = lc.nm_email
WHERE lc.criativo IS NOT NULL
GROUP BY lc.criativo, lc.conjunto
HAVING total_leads >= 50  -- mínimo para o proxy ser estável
ORDER BY proxy_pct_decil7plus DESC
