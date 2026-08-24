-- Resumo por braço de teste da campanha JOM
-- Braço = campanha Meta (para as tags com utm_content contendo ad_id) ou a própria tag
-- (form nativo, cujo utm_content traz o NOME do anúncio, sem id numérico).
--
-- ⚠️ Gotchas tratados aqui:
--   1. Tag JOM é reusada desde out/2025 → filtro por data de início do teste.
--   2. JOM-*-FORMS entram em LOTE: dt_registered_at_br = hora do import, não do cadastro.
--      Por isso a série diária desses braços não é confiável (só o agregado).
--   3. Qualidade geral é contaminada pela cobertura de pesquisa (form nativo pergunta menos).
--      A comparação justa é pc_qual_resp / score_resp — medidos SÓ entre respondentes.
DECLARE dt_inicio DATE DEFAULT '2026-07-25';

WITH leads AS (
    SELECT
        i.nm_tag,
        i.nm_email,
        DATE(i.dt_registered_at_br) AS dt_lead,
        i.nm_iql_band,
        i.qt_iql_points,
        i.vl_reference_ev,
        i.nm_survey_response_level,
        REGEXP_EXTRACT(i.utm_content, r'(\d{10,})$') AS id_ad
    FROM `bp-datawarehouse.masterdata.fct_lead_iql` AS i
    WHERE i.nm_tag LIKE 'JOM%'
      AND DATE(i.dt_registered_at_br) >= dt_inicio
),

ads AS (  -- ad_id → campanha Meta
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
            WHEN l.nm_tag LIKE '%FORMS' THEN 'Form nativo Meta'
            WHEN a.nm_campaign_name IS NOT NULL
                THEN REGEXP_REPLACE(a.nm_campaign_name, r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] ', '')
            ELSE 'Sem atribuição (orgânico/CRM/UTM ausente)'
        END AS nm_arm
    FROM leads AS l
    LEFT JOIN ads AS a USING (id_ad)
),

spend AS (
    SELECT
        CASE
            WHEN nm_campaign_name LIKE '%JOM-FORM%' THEN 'Form nativo Meta'
            ELSE REGEXP_REPLACE(nm_campaign_name, r'^\[LAN\] \[JOM[^\]]*\] \[LEAD\] ', '')
        END AS nm_arm,
        SUM(vl_amount_spent) AS vl_spend,
        MIN(reference_date) AS dt_ini,
        MAX(reference_date) AS dt_fim
    FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
    WHERE nm_campaign_name LIKE '%JOM%' AND reference_date >= dt_inicio AND vl_amount_spent > 0
    GROUP BY 1
),

revenue AS (  -- receita observada atribuída ao lead (qualquer produto/canal)
    SELECT
        d.nm_email, d.nm_tag,
        SUM(t.vl_payment_gross) AS vl_revenue,
        COUNT(*) AS qt_sales
    FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion` AS d,
        UNNEST(d.arr_st_approved_transactions) AS t
    WHERE d.nm_tag LIKE 'JOM%' AND t.vl_payment_gross IS NOT NULL
    GROUP BY 1, 2
),

final AS (
    SELECT
        l.nm_arm,
        COUNT(*) AS qt_leads,
        s.vl_spend,
        ROUND(SAFE_DIVIDE(s.vl_spend, COUNT(*)), 2) AS vl_cpl,
        -- qualidade GERAL (contaminada pela cobertura de pesquisa)
        ROUND(100 * COUNTIF(l.nm_iql_band IN ('A+', 'A')) / COUNT(*), 1) AS pc_qual,
        ROUND(AVG(l.qt_iql_points), 1) AS vl_score,
        ROUND(AVG(l.vl_reference_ev), 2) AS vl_ev,
        -- cobertura de pesquisa
        ROUND(100 * COUNTIF(l.nm_survey_response_level = 'sim') / COUNT(*), 1) AS pc_survey,
        -- qualidade COMPARÁVEL (só entre respondentes)
        COUNTIF(l.nm_survey_response_level = 'sim') AS qt_resp,
        ROUND(SAFE_DIVIDE(
            100 * COUNTIF(l.nm_survey_response_level = 'sim' AND l.nm_iql_band IN ('A+', 'A')),
            COUNTIF(l.nm_survey_response_level = 'sim')), 1) AS pc_qual_resp,
        ROUND(AVG(IF(l.nm_survey_response_level = 'sim', l.qt_iql_points, NULL)), 1) AS vl_score_resp,
        ROUND(AVG(IF(l.nm_survey_response_level = 'sim', l.vl_reference_ev, NULL)), 2) AS vl_ev_resp,
        -- retorno esperado (métrica-mestra) e realizado até agora
        ROUND(SAFE_DIVIDE(AVG(l.vl_reference_ev) * COUNT(*), s.vl_spend), 2) AS vl_retorno_esp,
        -- retorno COMPARÁVEL: aplica o EV dos respondentes a todos os leads do braço.
        -- Corrige o viés de cobertura de pesquisa (braço que pergunta menos tem EV
        -- artificialmente baixo — o lead cai em faixa C por ausência de sinal).
        ROUND(SAFE_DIVIDE(
            AVG(IF(l.nm_survey_response_level = 'sim', l.vl_reference_ev, NULL)) * COUNT(*),
            s.vl_spend), 2) AS vl_retorno_ajust,
        ROUND(SUM(IFNULL(r.vl_revenue, 0)), 0) AS vl_receita_obs,
        SUM(IFNULL(r.qt_sales, 0)) AS qt_vendas,
        s.dt_ini,
        s.dt_fim
    FROM leads_arm AS l
    LEFT JOIN spend AS s USING (nm_arm)
    LEFT JOIN revenue AS r ON l.nm_email = r.nm_email AND l.nm_tag = r.nm_tag
    GROUP BY l.nm_arm, s.vl_spend, s.dt_ini, s.dt_fim
)

SELECT * FROM final ORDER BY qt_leads DESC
