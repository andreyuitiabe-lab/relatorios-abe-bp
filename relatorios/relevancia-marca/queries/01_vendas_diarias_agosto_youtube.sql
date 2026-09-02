-- Etapa 1 — datar sabatinas: vendas diárias de agosto/2026 com atribuição YouTube/live
-- Sabatinas confirmadas por fonte pública: Renan Santos 14/08, Marçal 17/08 (meio-dia)
SELECT
  DATE(dt_ordered_at) AS dia,
  COUNTIF(nm_pptc_utm_medium = 'live_youtube') AS tx_live_yt,
  COUNTIF(nm_pptc_tracking_publisher = 'YouTube') AS tx_pub_yt,
  COUNTIF(UPPER(COALESCE(nm_pptc_tracking_name, '')) LIKE '%LIVE%') AS tx_track_live,
  COUNT(*) AS tx_total,
  ROUND(SUM(vl_payment_gross)) AS receita_total
FROM masterdata.fct_transactions
WHERE nm_status = 'approved'
  AND bl_is_renovation = FALSE
  AND DATE(dt_ordered_at) BETWEEN '2026-08-01' AND '2026-08-21'
GROUP BY 1
ORDER BY 1
