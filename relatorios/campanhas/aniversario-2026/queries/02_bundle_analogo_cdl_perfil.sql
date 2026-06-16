-- Análogo do Bundle: tag CDL — perfil por status × canal
SELECT st_member_status_at_registration AS status,
  CASE WHEN nm_lead_channel IN ('Anúncios','Influenciadores | Ads') THEN 'PAGO'
       WHEN nm_lead_channel='CRM' THEN 'CRM' ELSE 'ORG/OUTRO' END AS canal,
  COUNT(*) AS leads,
  SUM(CASE WHEN (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)>0 THEN 1 ELSE 0 END) AS compradores,
  ROUND(SUM((SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)),0) AS receita
FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
WHERE nm_tag='CDL'
GROUP BY status, canal ORDER BY leads DESC;

-- CDL agregado por perfil (frio vs base)
SELECT
  CASE WHEN st_member_status_at_registration='Não Membro' THEN 'FRIO/NaoMembro' ELSE 'BASE' END AS perfil,
  COUNT(*) AS leads,
  SUM(CASE WHEN (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)>0 THEN 1 ELSE 0 END) AS compradores,
  ROUND(SAFE_DIVIDE(SUM(CASE WHEN (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)>0 THEN 1 ELSE 0 END),COUNT(*))*100,2) AS conv_pct,
  ROUND(SUM((SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)),0) AS receita,
  ROUND(SAFE_DIVIDE(SUM((SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)),COUNT(*)),2) AS rec_por_lead
FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
WHERE nm_tag='CDL'
GROUP BY perfil ORDER BY perfil;
