-- Vendas aprovadas (sem renovação) com o handle do influ no rastreio do link (sitebp.la/vd_<camp>_<handle>).
-- Mídia com "ads" no utm_medium fica de fora: essas vendas já entram pelo funil de anúncios.
WITH t AS (
  SELECT LOWER(CONCAT(COALESCE(nm_pptc_utm_content,''),'|',COALESCE(nm_pptc_tracking_name,''),'|',
                      COALESCE(nm_utm_source,''),'|',COALESCE(nm_pptc_utm_campaign,''))) k,
         LOWER(COALESCE(nm_pptc_utm_medium,'')) med, vl_payment_gross v
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved' AND bl_is_renovation = FALSE AND DATE(dt_ordered_at) >= '{INI}')
SELECT h handle, COUNT(*) vendas, ROUND(SUM(v),2) receita,
  COUNTIF(STRPOS(med,'organic') > 0) vendas_organico, COUNTIF(STRPOS(med,'paid_publi') > 0) vendas_publi
FROM t, UNNEST([{HANDLES}]) h
WHERE STRPOS(k, h) > 0 AND STRPOS(med, 'ads') = 0
GROUP BY h
