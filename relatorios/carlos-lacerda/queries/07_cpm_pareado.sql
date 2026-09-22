-- Teste within-campaign: o CPM subiu porque o LEILAO encareceu ou porque a carteira
-- da conta mudou de composicao? Pareia a MESMA campanha nos dois meses.
-- Se fosse so mix, campanhas individuais nao subiriam de forma consistente.
WITH c AS (
  SELECT
    nm_campaign_name,
    SUM(IF(reference_date BETWEEN '2026-07-01' AND '2026-07-31', vl_amount_spent, 0)) AS sj,
    SUM(IF(reference_date BETWEEN '2026-07-01' AND '2026-07-31', qt_impressions, 0)) AS ij,
    SUM(IF(reference_date BETWEEN '2026-09-01' AND '2026-09-21', vl_amount_spent, 0)) AS ss,
    SUM(IF(reference_date BETWEEN '2026-09-01' AND '2026-09-21', qt_impressions, 0)) AS isp
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE (reference_date BETWEEN '2026-07-01' AND '2026-07-31'
      OR reference_date BETWEEN '2026-09-01' AND '2026-09-21')
    AND NOT REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]')
  GROUP BY 1
  HAVING ij > 10000 AND isp > 10000 AND sj > 2000 AND ss > 2000
)
SELECT
  COUNT(*) AS qt_campanhas_pareadas,
  COUNTIF(ss / isp > sj / ij) AS qt_que_encareceram,
  ROUND(SUM(sj) / SUM(ij) * 1000, 2) AS cpm_jul,
  ROUND(SUM(ss) / SUM(isp) * 1000, 2) AS cpm_set,
  ROUND(((SUM(ss) / SUM(isp)) / (SUM(sj) / SUM(ij)) - 1) * 100, 1) AS variacao_pct
FROM c
