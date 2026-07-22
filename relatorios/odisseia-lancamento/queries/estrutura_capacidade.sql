-- Diferenças estruturais entre as campanhas + capacidade do time.

-- 1) Capacidade total do Comercial (abordagens Zenvia e vendedores) nas duas janelas
SELECT CASE WHEN DATE(dt_approach_start) BETWEEN '2026-05-05' AND '2026-05-11'
            THEN 'mai' ELSE 'jul' END AS janela,
       COUNT(*) AS abordagens, COUNT(DISTINCT id_seller) AS vendedores,
       ROUND(COUNT(*)/7,0) AS abordagens_dia
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '2026-05-05' AND '2026-05-11'
   OR DATE(dt_approach_start) BETWEEN '2026-07-16' AND '2026-07-22'
GROUP BY 1;

-- 2) Leads de aquecimento com tag/UTM da campanha (ODI = 0; CDL = 4.638 até 17/05)
SELECT 'ODI' AS camp, COUNT(*) AS leads
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'ODI\]|ODISSEIA')
UNION ALL
SELECT 'CDL', COUNT(*)
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'CDL\]|CLUBE.DO.LIVRO')
  AND dt_registered_at_br < '2026-05-18';

-- 3) Spend Meta por campanha até a abertura da venda (ODI = 0)
SELECT CASE WHEN UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%'
            THEN 'ODI' ELSE 'CDL' END AS camp,
       ROUND(SUM(vl_amount_spent),0) AS spend
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE reference_date >= '2026-04-01'
  AND ((UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')
    OR (UPPER(nm_campaign_name) LIKE '%[CDL]%' AND reference_date < '2026-05-18'))
GROUP BY 1;

-- 4) Vitalícios da oferta de aniversário (BP10) vendidos pelo Comercial na semana 16–22/07
SELECT COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND bl_lifetime_offer
  AND DATE(dt_ordered_at) BETWEEN '2026-07-16' AND '2026-07-22'
  AND LOWER(nm_gateway_offer) LIKE '%aniv26%';
