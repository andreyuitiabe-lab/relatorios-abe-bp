-- Onde os 3 primeiros dias caem dentro da campanha inteira da ENE.
-- Marcos: estreia no Ticaracaticast em 19/08/2026 (22 dias depois do D1) e fim da
-- pre-venda de ate 50% OFF no mesmo dia.
SELECT
  DATE(dt_ordered_at) AS dt,
  DATE_DIFF(DATE(dt_ordered_at), DATE '2026-07-28', DAY) + 1 AS dia,
  COUNT(*) AS qt_transacoes,
  ROUND(SUM(vl_payment_gross)) AS vl_receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND DATE(dt_ordered_at) BETWEEN '2026-07-28' AND '2026-09-05'
  AND REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_tracking_name,'') || '|' || COALESCE(nm_pptc_utm_campaign,'') || '|' ||
                            COALESCE(nm_pptc_utm_content,'') || '|' || COALESCE(nm_lead_last_tracking,'')),
                      r'\[ene\]|eneas')
GROUP BY 1, 2
ORDER BY 1
