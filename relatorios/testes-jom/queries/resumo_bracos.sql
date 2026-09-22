-- Resumo por braço de teste da campanha JOM (janela cheia do relatório)
--
-- Braço = campanha de captação da tag JOM. A JOM roda em TRÊS contas de mídia (Meta, Google
-- Ads e PMax) — a atribuição de cada uma está documentada em queries/_atribuicao.md.
-- ⚠️ Olhar só o facebook_ads_funnel joga ~941 leads/semana de Google e PMax no balde
--    "sem atribuição", lidos como orgânico. Sempre unir as três tabelas de funil.
--
-- Qualidade GERAL é contaminada pela cobertura de pesquisa (braço que pergunta menos tem lead
-- em faixa baixa por AUSÊNCIA de sinal). A comparação justa é pc_qual_resp / score_resp,
-- medidos só entre respondentes.
DECLARE dt_inicio DATE DEFAULT '2026-07-25';

WITH leads AS (
    SELECT
        i.nm_tag,
        LOWER(TRIM(i.nm_email)) AS nm_email,
        i.nm_iql_band,
        i.qt_iql_points,
        i.vl_reference_ev,
        i.nm_survey_response_level,
        LOWER(i.utm_source) AS utm_source,
        REGEXP_EXTRACT(i.utm_content, r'(\d{10,})$') AS id_ad
    FROM `bp-datawarehouse.masterdata.fct_lead_iql` AS i
    WHERE i.nm_tag IN ('JOM', 'JOM-BR-FORMS')
      AND DATE(i.dt_registered_at_br) >= dt_inicio
),

ads AS (  -- id do anúncio Meta -> campanha
    SELECT
        CAST(id_advertising AS STRING) AS id_ad,
        ANY_VALUE(nm_campaign_name) AS nm_campaign_name
    FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
    WHERE nm_campaign_name LIKE '%JOM%' AND reference_date >= dt_inicio
    GROUP BY 1
),

leads_arm AS (
    SELECT
        l.*,
        CASE
            WHEN l.nm_tag LIKE '%FORMS' THEN 'Form nativo (Meta)'
            WHEN a.nm_campaign_name IS NOT NULL
                THEN REGEXP_REPLACE(a.nm_campaign_name,
                    r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] (\[ADVANTAGE\] )?', '')
            WHEN l.utm_source = 'pmax' THEN 'Google PMax [PMAX]'
            WHEN l.utm_source = 'google' THEN 'Google Ads [KW]'
            ELSE 'Sem atribuição (orgânico/CRM)'
        END AS nm_arm
    FROM leads AS l
    LEFT JOIN ads AS a USING (id_ad)
),

spend AS (  -- gasto das TRÊS contas, no mesmo rótulo de braço dos leads
    SELECT
        CASE
            WHEN nm_campaign_name LIKE '%JOM-FORM%' THEN 'Form nativo (Meta)'
            ELSE REGEXP_REPLACE(nm_campaign_name,
                r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] (\[ADVANTAGE\] )?', '')
        END AS nm_arm,
        SUM(vl_amount_spent) AS vl_spend,
        MIN(reference_date) AS dt_ini,
        MAX(reference_date) AS dt_fim
    FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
    WHERE nm_campaign_name LIKE '%JOM%' AND nm_campaign_name LIKE '%[LEAD]%'
      AND reference_date >= dt_inicio AND vl_amount_spent > 0
    GROUP BY 1
    UNION ALL
    SELECT 'Google PMax [PMAX]', SUM(vl_amount_spent), MIN(reference_date), MAX(reference_date)
    FROM `bp-datawarehouse.datamart.dtm_analytics_pmax_ads_funnel`
    WHERE nm_campaign_name LIKE '%[JOM]%' AND nm_campaign_name LIKE '%[LEAD]%'
      AND reference_date >= dt_inicio
    UNION ALL
    SELECT 'Google Ads [KW]', SUM(vl_amount_spent), MIN(reference_date), MAX(reference_date)
    FROM `bp-datawarehouse.datamart.dtm_analytics_google_ads_funnel`
    WHERE nm_campaign_name LIKE '%[JOM]%' AND nm_campaign_name LIKE '%[LEAD]%'
      AND reference_date >= dt_inicio
),

revenue AS (  -- receita observada atribuída ao lead (qualquer produto/canal)
    SELECT
        LOWER(TRIM(d.nm_email)) AS nm_email,
        d.nm_tag,
        SUM(t.vl_payment_gross) AS vl_revenue,
        COUNT(*) AS qt_sales
    FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion` AS d,
        UNNEST(d.arr_st_approved_transactions) AS t
    WHERE d.nm_tag IN ('JOM', 'JOM-BR-FORMS') AND t.vl_payment_gross IS NOT NULL
    GROUP BY 1, 2
),

final AS (
    SELECT
        l.nm_arm,
        COUNT(*) AS qt_leads,
        s.vl_spend,
        ROUND(SAFE_DIVIDE(s.vl_spend, COUNT(*)), 2) AS vl_cpl,
        ROUND(100 * COUNTIF(l.nm_iql_band IN ('A+', 'A')) / COUNT(*), 1) AS pc_qual,
        ROUND(AVG(l.qt_iql_points), 1) AS vl_score,
        ROUND(AVG(l.vl_reference_ev), 2) AS vl_ev,
        ROUND(100 * COUNTIF(l.nm_survey_response_level = 'sim') / COUNT(*), 1) AS pc_survey,
        COUNTIF(l.nm_survey_response_level = 'sim') AS qt_resp,
        ROUND(SAFE_DIVIDE(
            100 * COUNTIF(l.nm_survey_response_level = 'sim' AND l.nm_iql_band IN ('A+', 'A')),
            COUNTIF(l.nm_survey_response_level = 'sim')), 1) AS pc_qual_resp,
        ROUND(AVG(IF(l.nm_survey_response_level = 'sim', l.qt_iql_points, NULL)), 1) AS vl_score_resp,
        ROUND(AVG(IF(l.nm_survey_response_level = 'sim', l.vl_reference_ev, NULL)), 2) AS vl_ev_resp,
        ROUND(SAFE_DIVIDE(AVG(l.vl_reference_ev) * COUNT(*), s.vl_spend), 2) AS vl_retorno_esp,
        -- retorno COMPARÁVEL: aplica o EV dos respondentes a todos os leads do braço,
        -- corrigindo o viés de cobertura de pesquisa.
        ROUND(SAFE_DIVIDE(
            AVG(IF(l.nm_survey_response_level = 'sim', l.vl_reference_ev, NULL)) * COUNT(*),
            s.vl_spend), 2) AS vl_retorno_ajust,
        ROUND(SUM(IFNULL(r.vl_revenue, 0)), 0) AS vl_receita_obs,
        SUM(IFNULL(r.qt_sales, 0)) AS qt_vendas,
        -- ROAS já realizado (receita observada / gasto) — o IQL não vê intenção de busca,
        -- então em braço de keyword o esperado e o realizado divergem muito.
        ROUND(SAFE_DIVIDE(SUM(IFNULL(r.vl_revenue, 0)), s.vl_spend), 2) AS vl_roas_obs,
        s.dt_ini,
        s.dt_fim
    FROM leads_arm AS l
    LEFT JOIN spend AS s USING (nm_arm)
    LEFT JOIN revenue AS r ON l.nm_email = r.nm_email AND l.nm_tag = r.nm_tag
    GROUP BY l.nm_arm, s.vl_spend, s.dt_ini, s.dt_fim
)

SELECT * FROM final ORDER BY qt_leads DESC
