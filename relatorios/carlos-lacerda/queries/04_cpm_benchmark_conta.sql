-- CPM da conta Meta inteira, dia a dia, nas duas janelas (controle de leilao/sazonalidade)
-- Janelas D1-D3 pareadas em numero de dias. ⚠️ Dias da semana NAO sao equivalentes:
-- ENE = ter/qua/qui, LAC = sab/dom/seg -> usar o indice campanha ÷ conta do MESMO dia.
WITH conta AS (
  SELECT
    reference_date,
    CASE WHEN reference_date <= '2026-07-31' THEN 'ENE (jul)' ELSE 'LAC (set)' END AS janela,
    SUM(IF(REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]'), vl_amount_spent, 0)) AS spend_lead,
    SUM(IF(REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]'), qt_impressions, 0)) AS impr_lead,
    SUM(IF(REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]'), 0, vl_amount_spent)) AS spend_venda,
    SUM(IF(REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]'), 0, qt_impressions)) AS impr_venda
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-07-28' AND '2026-07-30'
     OR reference_date BETWEEN '2026-09-19' AND '2026-09-21'
  GROUP BY 1, 2
),
campanha AS (
  SELECT
    reference_date,
    SUM(IF(REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]'), 0, vl_amount_spent)) AS spend_camp,
    SUM(IF(REGEXP_CONTAINS(nm_campaign_name, r'\[LEAD\]'), 0, qt_impressions)) AS impr_camp
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[lac\]') AND reference_date BETWEEN '2026-09-19' AND '2026-09-21')
     OR (REGEXP_CONTAINS(LOWER(nm_campaign_name), r'\[ene\]') AND reference_date BETWEEN '2026-07-28' AND '2026-07-30')
  GROUP BY 1
)
SELECT
  c.janela,
  c.reference_date,
  FORMAT_DATE('%a', c.reference_date) AS dia_semana,
  c.spend_venda AS vl_spend_conta_venda,
  c.impr_venda AS qt_impr_conta_venda,
  ROUND(c.spend_lead / NULLIF(c.impr_lead, 0) * 1000, 2) AS cpm_conta_lead,
  ROUND(c.spend_venda / NULLIF(c.impr_venda, 0) * 1000, 2) AS cpm_conta_venda,
  ROUND(k.spend_camp / NULLIF(k.impr_camp, 0) * 1000, 2) AS cpm_campanha_venda,
  ROUND((k.spend_camp / NULLIF(k.impr_camp, 0)) / NULLIF(c.spend_venda / NULLIF(c.impr_venda, 0), 0), 2) AS indice_camp_vs_conta
FROM conta c
JOIN campanha k USING (reference_date)
ORDER BY c.reference_date
