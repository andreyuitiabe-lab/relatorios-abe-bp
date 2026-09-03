WITH influ AS (
  SELECT arr_st_all_approved_transactions AS arr_dir, arr_commercial_deals_breakdown AS arr_com
  FROM `bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel`
  WHERE reference_date BETWEEN '2026-08-01' AND '2026-08-31'
    AND (REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'influ|inlfu')
      OR REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')),
         r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni'))
),
ids AS (
  SELECT DISTINCT t.id_transaction FROM influ, UNNEST(arr_dir) t
  UNION DISTINCT
  SELECT DISTINCT s.id_transaction FROM influ, UNNEST(arr_com) d, UNNEST(d.arr_sales_transaction_ids) s
),
-- venda indireta: mesma regra usada na seção 02 do relatório
indireta AS (
  SELECT id_transaction, vl_payment_gross
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status='approved' AND bl_is_renovation=FALSE
    AND DATE(dt_ordered_at) BETWEEN '2026-08-01' AND '2026-08-31'
    AND COALESCE(nm_pptc_tracking_publisher,'') != 'Influencers'
    AND NOT STARTS_WITH(COALESCE(nm_pptc_tracking_name,''),'Afiliado')
    AND REGEXP_CONTAINS(UPPER(COALESCE(nm_lead_last_tracking,'')), r'INFLU|PARC')
    AND NOT REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_medium,'')), r'ads')
)
SELECT
  COUNT(*)                                                      AS ids_do_modelo_de_ads,
  COUNTIF(f.id_transaction IS NULL)                             AS nao_achados_no_fct,
  COUNTIF(f.nm_status != 'approved')                            AS nao_aprovadas,
  COUNTIF(f.bl_is_renovation)                                   AS RENOVACOES,
  COUNTIF(DATE(f.dt_ordered_at) NOT BETWEEN '2026-08-01' AND '2026-08-31') AS fora_de_agosto,
  ROUND(SUM(f.vl_payment_gross),2)                              AS receita_recalculada_no_fct,
  COUNTIF(i.id_transaction IS NOT NULL)                         AS TAMBEM_NA_VENDA_INDIRETA,
  ROUND(SUM(IF(i.id_transaction IS NOT NULL, f.vl_payment_gross, 0)),2) AS valor_sobreposto
FROM ids
LEFT JOIN `bp-datawarehouse.masterdata.fct_transactions` f USING (id_transaction)
LEFT JOIN indireta i USING (id_transaction)
