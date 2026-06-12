-- Qualificação de leads: status no momento do registro + cobertura dim_user
-- Tabela base: bp-staging.dbt_abe.tb_leads_qualification_base (já materializada)
-- Para campanhas jan/2025+

SELECT
  nm_campaign_tag,
  lead_status_at_registration,
  COUNT(*)                                                               AS total_leads,
  COUNTIF(id_user IS NOT NULL)                                           AS com_dados_internos,
  ROUND(COUNTIF(id_user IS NOT NULL) / COUNT(*) * 100, 1)                AS pct_cobertura,
  ROUND(AVG(cd_income_decile) IGNORE NULLS, 2)                           AS decil_medio,
  ROUND(COUNTIF(cd_income_decile >= 7) / NULLIF(COUNTIF(cd_income_decile IS NOT NULL), 0) * 100, 1)
                                                                         AS pct_decil7plus
FROM `bp-staging.dbt_abe.tb_leads_qualification_enriched`
WHERE nm_campaign_tag IS NOT NULL
GROUP BY nm_campaign_tag, lead_status_at_registration
ORDER BY nm_campaign_tag, total_leads DESC
