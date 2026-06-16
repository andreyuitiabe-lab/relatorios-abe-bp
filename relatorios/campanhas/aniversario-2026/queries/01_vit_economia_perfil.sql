-- Economia do funil Vitalício por perfil (base vs frio) — tag VIT
SELECT
  CASE WHEN st_member_status_at_registration IN ('Membro Ativo','Ex-Membro','Membro Ativo (Vitalício)')
       THEN 'BASE' ELSE 'FRIO' END AS perfil,
  COUNT(*) AS leads,
  SUM(CASE WHEN (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t) > 0 THEN 1 ELSE 0 END) AS compradores,
  ROUND(SAFE_DIVIDE(SUM(CASE WHEN (SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t) > 0 THEN 1 ELSE 0 END), COUNT(*))*100,2) AS conv_pct,
  ROUND(SUM((SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)),0) AS receita,
  ROUND(SAFE_DIVIDE(SUM((SELECT SUM(t.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) t)), COUNT(*)),2) AS receita_por_lead
FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
WHERE nm_tag = 'VIT'
GROUP BY perfil ORDER BY perfil;
