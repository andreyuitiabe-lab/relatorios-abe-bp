-- Cobertura real da atribuição de install por sistema operacional.
-- Serve para fact-check da afirmação "iOS não tem atribuição nenhuma": tem, mas ~4x pior
-- que o Android. Resultado em 18/06–13/08/2026:
--   Android  44.203 first_open · 7.985 cpc (18,1%) · 2.274 com token [APP]
--   iOS      38.460 first_open · 1.731 cpc ( 4,5%) · 1.089 com token [APP]
SELECT
    nm_device_operating_system AS nm_os,
    COUNT(*)                                                          AS qt_first_open,
    COUNTIF(nm_traffic_source_medium = 'cpc')                         AS qt_cpc,
    ROUND(100 * COUNTIF(nm_traffic_source_medium = 'cpc') / COUNT(*), 1) AS pct_cpc,
    COUNTIF(REGEXP_CONTAINS(nm_traffic_source_name, r'\[APP\]'))      AS qt_tag_app
FROM `bp-datawarehouse.staging.stg_firebase__bp_platform_events`
WHERE dt_created_at BETWEEN '2026-06-18' AND '2026-08-13'
    AND nm_event = 'first_open'
GROUP BY nm_os
ORDER BY qt_first_open DESC
