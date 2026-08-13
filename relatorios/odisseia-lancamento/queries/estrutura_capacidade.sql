-- Diferenças estruturais entre as campanhas + capacidade do time.
-- Janelas D1–Dn dinâmicas no refresh.py; snapshot abaixo: D1–D27 (13/08/2026).

-- 1) Capacidade total do Comercial (abordagens Zenvia e vendedores) nas duas janelas
SELECT CASE WHEN DATE(dt_approach_start) BETWEEN '2026-05-05' AND '2026-05-31'
            THEN 'mai' ELSE 'jul' END AS janela,
       COUNT(*) AS abordagens, COUNT(DISTINCT id_seller) AS vendedores,
       ROUND(COUNT(*)/27,0) AS abordagens_dia
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '2026-05-05' AND '2026-05-31'
   OR DATE(dt_approach_start) BETWEEN '2026-07-17' AND '2026-08-12'
GROUP BY 1;

-- 2) Leads com tag/UTM da campanha (CDL até a abertura digital de 18/05; ODI acumulado —
--    era 0 no lançamento, captação começou na fase 2)
SELECT 'ODI' AS camp, COUNT(*) AS leads
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'ODI\]|ODISSEIA')
UNION ALL
SELECT 'CDL', COUNT(*)
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'CDL\]|CLUBE.DO.LIVRO')
  AND dt_registered_at_br < '2026-05-18';

-- 3) Spend Meta por campanha (CDL até a abertura da venda; ODI acumulado —
--    era R$ 0 no lançamento, mídia ligou na fase 2)
SELECT CASE WHEN UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%'
            THEN 'ODI' ELSE 'CDL' END AS camp,
       ROUND(SUM(vl_amount_spent),0) AS spend
FROM datamart.dtm_analytics_facebook_ads_funnel
WHERE reference_date >= '2026-04-01'
  AND ((UPPER(nm_campaign_name) LIKE '%[ODI]%' OR UPPER(nm_campaign_name) LIKE '%ODISSEIA%')
    OR (UPPER(nm_campaign_name) LIKE '%[CDL]%' AND reference_date < '2026-05-18'))
GROUP BY 1;

-- 4) Vitalícios da oferta de aniversário (BP10) vendidos pelo Comercial na janela ODI
SELECT COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND bl_lifetime_offer
  AND DATE(dt_ordered_at) BETWEEN '2026-07-17' AND '2026-08-12'
  AND LOWER(nm_gateway_offer) LIKE '%aniv26%';
