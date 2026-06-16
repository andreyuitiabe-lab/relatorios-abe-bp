-- Ticket ponderado dos planos de assinatura de entrada (núcleo do Bundle) — novas vendas 2026
SELECT
  ROUND(SUM(vl_payment_gross)/COUNT(*),2) AS ticket_ponderado_assinatura,
  COUNT(*) AS vendas,
  ROUND(SUM(vl_payment_gross),0) AS receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_lifetime_offer=FALSE
  AND dt_ordered_at >= '2026-01-01'
  AND nm_gateway_plan IN ('good','supporter','best','better','bp-clube');

-- Detalhe por plano (todas as novas vendas de assinatura 2026)
SELECT nm_gateway_plan, nm_plan_label,
  COUNT(*) AS vendas, ROUND(AVG(vl_payment_gross),2) AS ticket, ROUND(SUM(vl_payment_gross),0) AS receita
FROM `bp-datawarehouse.masterdata.fct_transactions`
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_lifetime_offer=FALSE
  AND dt_ordered_at >= '2026-01-01'
GROUP BY nm_gateway_plan, nm_plan_label ORDER BY vendas DESC LIMIT 25;
