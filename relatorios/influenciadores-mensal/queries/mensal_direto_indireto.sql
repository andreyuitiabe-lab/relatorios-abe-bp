SELECT
  CASE WHEN COALESCE(nm_pptc_tracking_publisher,'')='Influencers'
            OR STARTS_WITH(COALESCE(nm_pptc_tracking_name,''),'Afiliado')
       THEN 'direto' ELSE 'indireto' END           AS categoria,
  COALESCE(nm_pptc_tracking_name,'')               AS tracking_name,
  COALESCE(nm_utm_source,'')                       AS utm_source,
  COALESCE(nm_pptc_utm_content,'')                 AS utm_content,
  COALESCE(nm_lead_last_tracking,'')               AS lead_tracking,
  COALESCE(nm_plan_label, nm_gateway_product,'outro') AS produto,
  COUNT(*)                                         AS qt,
  ROUND(SUM(vl_payment_gross),2)                   AS receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status='approved' AND bl_is_renovation=FALSE
  AND DATE(dt_ordered_at) BETWEEN '2026-08-01' AND '2026-08-31'
  AND (
    COALESCE(nm_pptc_tracking_publisher,'')='Influencers'
    OR STARTS_WITH(COALESCE(nm_pptc_tracking_name,''),'Afiliado')
    OR (REGEXP_CONTAINS(UPPER(COALESCE(nm_lead_last_tracking,'')), r'INFLU|PARC')
        AND NOT REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_medium,'')), r'ads'))
  )
GROUP BY 1,2,3,4,5,6
ORDER BY receita DESC
