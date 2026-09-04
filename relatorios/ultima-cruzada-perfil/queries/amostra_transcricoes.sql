-- Conversas Zenvia de set/2026 que mencionam a Coleção / Última Cruzada
SELECT a.id_approach, a.nm_stage, a.dt_approach_start, a.qt_seller_interactions, a.qt_prospect_interactions,
       a.nm_closing_reason,
       SUBSTR(REGEXP_REPLACE(a.nm_conversation, r'\s+', ' '), 1, 2500) AS conversa
FROM `bp-datawarehouse.masterdata.dim_zenvia_approaches` a
WHERE DATE(a.dt_approach_start) >= '2026-08-28'
  AND REGEXP_CONTAINS(LOWER(COALESCE(a.nm_conversation,'')), r'[uú]ltima cruzada|cole[cç][aã]o brasil')
ORDER BY a.dt_approach_start DESC
LIMIT 8
