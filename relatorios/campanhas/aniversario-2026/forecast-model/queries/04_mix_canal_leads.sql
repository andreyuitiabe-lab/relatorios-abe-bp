-- Mix de canal dos leads de aquecimento (BPDay 2025) — separa lead pago (CPL > 0)
-- de lead CRM/owned (custo zero). Alimenta o split de investimento do modelo.
-- Fonte: bp-lake.marketing.lead_registration. UTMs ficam no struct st_utms
-- (campos source/medium/campaign/term/content). Sinais extra: id_fbclid, id_gclid.
-- Validado em 15/jun/2026.
-- Resultado (leads únicos): pago_meta 46.556 (66,3%) | organico 8.609 (12,3%)
--   crm_owned 8.389 (11,9%) | sem_atribuicao 3.804 (5,4%) | pago_google_yt 2.705 (3,9%)
--   >>> TOTAL PAGO ≈ 70% | CRM OWNED ≈ 12% | ORGÂNICO ≈ 12% | SEM ATRIB ≈ 6% <<<
SELECT
  CASE
    WHEN st_utms.source LIKE '%facebook%' OR st_utms.source LIKE '%fb%'
      OR st_utms.medium LIKE '%paid%' OR st_utms.medium LIKE '%cpc%'
      OR id_fbclid IS NOT NULL THEN 'pago_meta'
    WHEN st_utms.source LIKE '%youtube%' OR id_gclid IS NOT NULL
      OR st_utms.source LIKE '%google%' THEN 'pago_google_yt'
    WHEN st_utms.medium LIKE '%email%' OR st_utms.source LIKE '%insider%'
      OR st_utms.source LIKE '%crm%'
      OR st_utms.medium IN ('push','whatsapp','inapp','in-app') THEN 'crm_owned'
    WHEN st_utms.source LIKE '%instagram%' OR st_utms.source LIKE '%organic%'
      OR st_utms.medium LIKE '%social%' OR st_utms.source LIKE '%portal%' THEN 'organico'
    WHEN st_utms.source IS NULL AND st_utms.medium IS NULL
      AND id_fbclid IS NULL AND id_gclid IS NULL THEN 'sem_atribuicao'
    ELSE 'outros'
  END AS canal,
  COUNT(DISTINCT nm_email) AS leads
FROM `bp-lake.marketing.lead_registration`
WHERE ts_registered_at BETWEEN TIMESTAMP('2025-06-07') AND TIMESTAMP('2025-06-21 23:59:59')
GROUP BY 1 ORDER BY leads DESC;
