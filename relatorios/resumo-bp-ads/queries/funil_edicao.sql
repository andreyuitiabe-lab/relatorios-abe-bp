-- Funil do Resumo BP por edição (janela móvel de 30 dias)
-- Fonte: staging.stg_insider__events, campanhas [RBP]
-- "Enviados" ≈ delivered + blocked + dropped + bounce (Insider não expõe evento 'sent';
--   fica ~1% acima do "Sent" da UI do Insider)
-- Aberturas: total (padrão mercado, inclui Apple MPP) e humana (bl_human_open = 1)
WITH rbp AS (
    SELECT
        nm_campaign,
        nm_event,
        nm_email,
        bl_human_open,
        DATE(dt_event_created_at) AS dt
    FROM `bp-datawarehouse.staging.stg_insider__events`
    WHERE dt_bp_imported_at >= DATETIME(DATE_SUB(CURRENT_DATE(), INTERVAL 40 DAY))
        AND REGEXP_CONTAINS(nm_campaign, r'\[RBP\]')
),

edicoes AS (
    SELECT
        nm_campaign,
        MIN(IF(nm_event = 'email_delivered', dt, NULL)) AS dt_envio
    FROM rbp
    GROUP BY 1
    HAVING
        dt_envio >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND COUNTIF(nm_event = 'email_delivered') > 50000
)

SELECT
    e.dt_envio,
    r.nm_campaign,
    COUNTIF(r.nm_event IN ('email_delivered', 'email_blocked', 'email_dropped', 'email_bounce')) AS qt_enviados,
    COUNTIF(r.nm_event = 'email_delivered') AS qt_entregues,
    COUNT(DISTINCT IF(r.nm_event = 'email_open', r.nm_email, NULL)) AS qt_abridores_total,
    COUNT(DISTINCT IF(r.nm_event = 'email_open' AND r.bl_human_open = 1, r.nm_email, NULL)) AS qt_abridores_humano,
    COUNT(DISTINCT IF(r.nm_event = 'email_click', r.nm_email, NULL)) AS qt_clicadores,
    COUNTIF(r.nm_event = 'email_click') AS qt_cliques,
    COUNTIF(r.nm_event = 'email_unsubscribe') AS qt_unsub
FROM rbp AS r
INNER JOIN edicoes AS e USING (nm_campaign)
GROUP BY 1, 2
ORDER BY 1
