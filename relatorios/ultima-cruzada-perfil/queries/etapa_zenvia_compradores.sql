WITH b AS (SELECT email, id_gateway_customer, bl_comercial FROM `bp-staging.dbt_abe.tb_uc_compradores`),
tel AS (
  SELECT b.email, b.bl_comercial, c.cd_cleaned_phone_number AS fone
  FROM b JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE c.cd_cleaned_phone_number IS NOT NULL
),
zc AS (
  SELECT z.cd_cleaned_phone_number AS fone, z.nm_stage, TRIM(z.nm_group) AS grupo, z.nm_status,
         z.nm_latest_lead_product_detail AS produto_interesse
  FROM `bp-datawarehouse.masterdata.dim_zenvia_contacts` z
  WHERE z.cd_cleaned_phone_number IN (SELECT fone FROM tel)
  QUALIFY ROW_NUMBER() OVER (PARTITION BY z.cd_cleaned_phone_number ORDER BY z.dt_last_status_updated_at DESC) = 1
)
SELECT COALESCE(zc.nm_stage,'(sem contato)') AS etapa_zenvia, zc.grupo,
       COUNT(*) AS n,
       COUNTIF(t.bl_comercial) AS venda_comercial,
       COUNTIF(NOT t.bl_comercial) AS venda_digital
FROM tel t LEFT JOIN zc USING (fone)
GROUP BY 1,2 ORDER BY n DESC LIMIT 20
