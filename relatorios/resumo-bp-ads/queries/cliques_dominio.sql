-- Cliques do Resumo BP por domínio de destino e edição (janela móvel de 30 dias)
-- Segmentação de parceiro/anunciante: NET.REG_DOMAIN(nm_email_url)
-- ⚠️ Links de anunciante saem sem UTM (jul/2026) — domínio é o único identificador.
WITH rbp AS (
    SELECT
        nm_campaign,
        nm_event,
        nm_email,
        nm_email_url,
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
    NET.REG_DOMAIN(r.nm_email_url) AS nm_dominio,
    COUNTIF(r.nm_event = 'email_click') AS qt_cliques,
    COUNT(DISTINCT IF(r.nm_event = 'email_click', r.nm_email, NULL)) AS qt_clicadores
FROM rbp AS r
INNER JOIN edicoes AS e USING (nm_campaign)
WHERE r.nm_event = 'email_click' AND r.nm_email_url IS NOT NULL
GROUP BY 1, 2
HAVING qt_cliques > 3
ORDER BY 1, 3 DESC
