-- Qualificação de leads: CPL × CAC por campanha
-- Evidencia anticorrelação entre CPL barato e CAC real
-- Requer: custo de mídia por campanha (origem: Meta Ads / Google Ads)
-- e receita convertida por atribuição last-click de lead_last_tracking

WITH

leads_por_campanha AS (
  SELECT
    nm_campaign_tag,
    lead_status_at_registration,
    COUNT(*) AS total_leads
  FROM `bp-staging.dbt_abe.tb_leads_qualification_base`
  GROUP BY 1, 2
),

compradores_por_campanha AS (
  SELECT
    nm_lead_last_tracking                              AS campaign_tag,
    COUNT(DISTINCT id_gateway_customer)                AS compradores,
    SUM(vl_payment_gross)                              AS receita_atribuida
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
    AND nm_lead_last_tracking IS NOT NULL
  GROUP BY 1
)

-- JOIN com tabela de custo (preencher manualmente ou via Meta Ads funnel)
SELECT
  l.nm_campaign_tag,
  SUM(CASE WHEN l.lead_status_at_registration = 'Membro' THEN l.total_leads ELSE 0 END) AS leads_membros,
  SUM(CASE WHEN l.lead_status_at_registration = 'Não Membro' THEN l.total_leads ELSE 0 END) AS leads_nao_membros,
  SUM(l.total_leads)                                                   AS total_leads,
  c.compradores,
  c.receita_atribuida,
  ROUND(c.receita_atribuida / NULLIF(c.compradores, 0), 0)             AS ticket_medio,
  -- CPL e CAC requerem custo de mídia externo:
  -- CPL = custo / total_leads
  -- CAC = custo / compradores
  NULL AS cpl_placeholder,
  NULL AS cac_placeholder
FROM leads_por_campanha l
LEFT JOIN compradores_por_campanha c ON c.campaign_tag = l.nm_campaign_tag
GROUP BY l.nm_campaign_tag, c.compradores, c.receita_atribuida
ORDER BY c.receita_atribuida DESC NULLS LAST
