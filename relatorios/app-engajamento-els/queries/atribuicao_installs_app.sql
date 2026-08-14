-- Universo atribuído: devices cujo first_open carrega campanha com token [APP]
-- Atribuição first-touch do Firebase (Play Install Referrer no Android; App Store no iOS).
-- O filtro é o token [APP] no nome da campanha, NÃO medium='cpc' — é o que separa
-- campanha de download de campanha de venda.
-- Grão: 1 linha por id_pseudo_user (device). Base do relatório de 13/08/2026 (3.374 devices).
SELECT
    id_pseudo_user,
    ANY_VALUE(nm_traffic_source_name)     AS nm_campanha,
    ANY_VALUE(nm_traffic_source_medium)   AS nm_medium,
    ANY_VALUE(nm_device_operating_system) AS nm_os,
    MIN(DATE(dt_created_at))              AS dt_install
FROM `bp-datawarehouse.staging.stg_firebase__bp_platform_events`
WHERE dt_created_at BETWEEN '2026-06-18' AND '2026-08-13'
    AND nm_event = 'first_open'
    AND REGEXP_CONTAINS(nm_traffic_source_name, r'\[APP\]')
GROUP BY id_pseudo_user
