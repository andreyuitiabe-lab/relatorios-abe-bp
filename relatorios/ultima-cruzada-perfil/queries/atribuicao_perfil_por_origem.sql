WITH comp AS (
  SELECT b.email, b.bl_comercial, b.vl_uc, b.bl_membro_ativo, b.bl_vitalicio, b.bl_cdl,
         b.vl_ltv_ant, b.cd_income_decile, b.nivel_cartao, b.qt_dias_ativos_90d, b.qt_dias_de_casa,
         c.cd_cleaned_phone_number AS fone
  FROM `bp-staging.dbt_abe.tb_uc_compradores` b
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
),
ab AS (SELECT DISTINCT fone, TRUE AS bl_abordado_cbr FROM `bp-staging.dbt_abe.tb_uc_abordagens` WHERE fone IS NOT NULL)
SELECT
  CASE WHEN COALESCE(ab.bl_abordado_cbr, FALSE) AND comp.bl_comercial THEN '1. Abordado CBR -> venda Comercial'
       WHEN COALESCE(ab.bl_abordado_cbr, FALSE) AND NOT comp.bl_comercial THEN '2. Abordado CBR -> venda Digital'
       WHEN comp.bl_comercial THEN '3. Venda Comercial sem abordagem CBR'
       ELSE '4. Digital puro (sem abordagem)' END AS origem,
  COUNT(*) AS n, ROUND(SUM(vl_uc),0) AS receita, ROUND(AVG(vl_uc),0) AS ticket,
  ROUND(100*COUNTIF(bl_membro_ativo)/COUNT(*),0) AS pc_membro,
  ROUND(100*COUNTIF(bl_vitalicio)/COUNT(*),0) AS pc_vitalicio,
  ROUND(100*COUNTIF(bl_cdl)/COUNT(*),0) AS pc_cdl,
  ROUND(APPROX_QUANTILES(vl_ltv_ant,2)[OFFSET(1)],0) AS ltv_mediana,
  ROUND(AVG(cd_income_decile),1) AS decil_renda,
  ROUND(100*COUNTIF(nivel_cartao IN ('6_black','5_amex','4_platinum'))/COUNTIF(nivel_cartao IS NOT NULL),0) AS pc_cartao_premium,
  ROUND(AVG(qt_dias_de_casa)/365,1) AS anos_casa,
  ROUND(AVG(qt_dias_ativos_90d),1) AS dias_ativos_90d
FROM comp LEFT JOIN ab USING (fone)
GROUP BY 1 ORDER BY 1
