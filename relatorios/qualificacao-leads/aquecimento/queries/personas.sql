-- Personas dos leads qualificados (A+/A): cascata mutuamente exclusiva sobre status e
-- tempo que conhece a BP (atributos legíveis; nunca pontos — D20).
DECLARE tag STRING DEFAULT 'ENE';
DECLARE dt_inicio DATE DEFAULT '2026-07-27';

WITH q AS (
    SELECT
        CASE
            WHEN nm_status_level != 'nao_membro' THEN 'base_reimpactada'
            WHEN nm_awareness_time_level = 'mais_3a' THEN 'veterano'
            WHEN nm_awareness_time_level = '6m_a_3a' THEN 'descobridor'
            WHEN nm_awareness_time_level IN ('ate_6m', 'primeiro_contato') THEN 'recem_chegado'
            ELSE 'sem_pesquisa'
        END AS persona,
        qt_vendas,
        (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) AS t
         WHERE t.vl_payment_gross IS NOT NULL AND t.days_to_purchase >= 0) AS vl_receita
    FROM `bp-datawarehouse.datamart.cbo_lead_conversion_iql`
    WHERE nm_tag = tag AND DATE(dt_registered_at_br) >= dt_inicio AND nm_iql_band IN ('A+', 'A')
)

SELECT persona, COUNT(*) AS qt_leads,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pc_qual,
       COUNTIF(qt_vendas > 0) AS qt_compradores,
       ROUND(100 * COUNTIF(qt_vendas > 0) / COUNT(*), 2) AS pc_conv,
       ROUND(SUM(IFNULL(vl_receita, 0)), 0) AS vl_receita
FROM q GROUP BY 1 ORDER BY qt_leads DESC
