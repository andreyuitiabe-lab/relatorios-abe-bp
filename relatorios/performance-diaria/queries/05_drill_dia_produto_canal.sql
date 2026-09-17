-- Drill de um dia: receita e tx por produto (nm_plan_label) × canal, contra o esperado
-- (mediana do mesmo dia da semana nas 4 semanas anteriores). Parâmetro: @dia.
DECLARE dia DATE DEFAULT '2026-09-13';
WITH base AS (
  SELECT DATE(dt_ordered_at) AS d,
    COALESCE(nm_plan_label, nm_gateway_plan, 'sem plano') AS produto,
    CASE WHEN bl_is_commercial_channel THEN 'Comercial'
         WHEN nm_pptc_tracking_publisher IN ('Facebook Ads','Instagram Ads') THEN 'Ads Meta'
         WHEN nm_pptc_tracking_publisher IN ('Adwords','Adwords Remarketing') THEN 'Ads Google'
         WHEN nm_pptc_tracking_publisher IN ('E-mail','Message Service','WhatsApp') THEN 'CRM'
         WHEN nm_pptc_tracking_publisher IN ('Organic','Own Site','Member Area') THEN 'Orgânico/Portal'
         WHEN nm_pptc_tracking_publisher = 'YouTube' THEN 'YouTube' ELSE 'Outros' END AS canal,
    vl_payment_gross AS vl
  FROM masterdata.fct_transactions
  WHERE nm_status = 'approved' AND bl_is_renovation = FALSE
    AND DATE(dt_ordered_at) IN (dia, dia - 7, dia - 14, dia - 21, dia - 28)
),
agg AS (
  SELECT d, produto, COUNT(*) tx, SUM(vl) rec FROM base GROUP BY 1, 2
),
esp AS (
  SELECT produto,
    APPROX_QUANTILES(IF(d < dia, tx, NULL), 2)[OFFSET(1)] AS tx_esp,
    APPROX_QUANTILES(IF(d < dia, rec, NULL), 2)[OFFSET(1)] AS rec_esp,
    COUNTIF(d < dia) AS n_sem
  FROM agg GROUP BY 1
)
SELECT a.produto, a.tx, ROUND(a.rec) AS receita, ROUND(a.rec / a.tx) AS ticket,
       COALESCE(e.tx_esp, 0) AS tx_esp, ROUND(COALESCE(e.rec_esp, 0)) AS receita_esp, e.n_sem,
       ROUND(a.rec - COALESCE(e.rec_esp, 0)) AS delta
FROM agg a LEFT JOIN esp e USING (produto)
WHERE a.d = dia
ORDER BY ABS(a.rec - COALESCE(e.rec_esp, 0)) DESC
LIMIT 15
