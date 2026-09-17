-- RODADA 9e — o cliente que entra em dia de audiência alta vale menos? (o ticket é 17% menor)
-- Primeiras compras por dia; para cada uma, receita acumulada em D+30/90/180 e se seguiu ativo.
-- Cohort maduro: aquisições até 15/06/2026 (180d completos até 12/09).
WITH primeiras AS (
  SELECT DATE(t.dt_ordered_at) AS dia_aq, t.id_gateway_customer, t.vl_payment_gross AS vl_inicial,
         COALESCE(t.nm_plan_label, t.nm_gateway_plan, 'sem plano') AS produto_inicial,
         CASE WHEN t.bl_is_commercial_channel THEN 'Comercial'
              WHEN t.nm_pptc_tracking_publisher IN ('Facebook Ads','Instagram Ads','Adwords','Adwords Remarketing') THEN 'Ads'
              WHEN t.nm_pptc_tracking_publisher IN ('E-mail','Message Service','WhatsApp') THEN 'CRM'
              ELSE 'Outros' END AS canal_aq
  FROM masterdata.fct_transactions t
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND t.bl_is_first_subscription_transaction = TRUE
    AND DATE(t.dt_ordered_at) BETWEEN '2025-08-01' AND '2026-06-15'
),
depois AS (
  SELECT p.dia_aq, p.id_gateway_customer, p.vl_inicial, p.produto_inicial, p.canal_aq,
    (SELECT COALESCE(SUM(t2.vl_payment_gross),0) FROM masterdata.fct_transactions t2
      WHERE t2.id_gateway_customer = p.id_gateway_customer AND t2.nm_status='approved'
        AND DATE(t2.dt_ordered_at) > p.dia_aq AND DATE(t2.dt_ordered_at) <= DATE_ADD(p.dia_aq, INTERVAL 90 DAY)) AS rec_pos_90,
    (SELECT COALESCE(SUM(t2.vl_payment_gross),0) FROM masterdata.fct_transactions t2
      WHERE t2.id_gateway_customer = p.id_gateway_customer AND t2.nm_status='approved'
        AND DATE(t2.dt_ordered_at) > p.dia_aq AND DATE(t2.dt_ordered_at) <= DATE_ADD(p.dia_aq, INTERVAL 180 DAY)) AS rec_pos_180,
    (SELECT COUNT(*) FROM masterdata.fct_transactions t2
      WHERE t2.id_gateway_customer = p.id_gateway_customer AND t2.nm_status='approved' AND t2.bl_is_renovation = TRUE
        AND DATE(t2.dt_ordered_at) > p.dia_aq AND DATE(t2.dt_ordered_at) <= DATE_ADD(p.dia_aq, INTERVAL 180 DAY)) AS n_renov_180
  FROM primeiras p
)
SELECT dia_aq, canal_aq,
  COUNT(*) AS clientes,
  ROUND(AVG(vl_inicial), 2) AS ticket_inicial,
  ROUND(AVG(rec_pos_90), 2) AS rec_extra_90,
  ROUND(AVG(rec_pos_180), 2) AS rec_extra_180,
  ROUND(AVG(vl_inicial + rec_pos_180), 2) AS ltv_180,
  ROUND(100 * COUNTIF(rec_pos_180 > 0) / COUNT(*), 2) AS pct_recompra_180,
  ROUND(100 * COUNTIF(n_renov_180 > 0) / COUNT(*), 2) AS pct_renovou_180
FROM depois
GROUP BY 1, 2
ORDER BY 1, 2
