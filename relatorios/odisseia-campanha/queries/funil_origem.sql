-- Funil geral da campanha Odisseia + atribuição por origem (último clique da transação).
-- Janela dinâmica no refresh.py (venda desde 2026-07-17 até ontem). Snapshot: 13/08/2026.
-- Filtro do produto: plano 'livro-odisseia-edicao-colecionador' OU produto '%odis%'.

-- 1) Vendas por dia e canal
SELECT DATE(dt_ordered_at) AS dia,
       CASE WHEN bl_is_commercial_channel THEN 'comercial' ELSE 'digital' END AS canal,
       COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE
  AND (nm_gateway_plan='livro-odisseia-edicao-colecionador' OR LOWER(nm_gateway_product) LIKE '%odis%')
  AND DATE(dt_ordered_at) >= '2026-07-17'
GROUP BY 1,2 ORDER BY 1;

-- 2) Origem por último clique (digital: origem da venda; comercial: última sessão antes da venda)
--    Trocar bl_is_commercial_channel=FALSE/TRUE conforme o corte.
SELECT CASE
         WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) = 'facebook_ads' THEN 'Ads Meta'
         WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) IN ('pmax_ads','kw_google_ads','youtube_ads') THEN 'Ads Google'
         WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) = 'email' THEN 'CRM e-mail'
         WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) LIKE '%whatsapp%' THEN 'CRM WhatsApp'
         WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) IN ('app_push','in_app') THEN 'CRM push/in-app'
         WHEN LOWER(COALESCE(nm_pptc_utm_medium,'')) LIKE 'organic%'
           OR LOWER(COALESCE(nm_pptc_tracking_publisher,'')) = 'organic' THEN 'Orgânico'
         WHEN COALESCE(TRIM(nm_pptc_utm_medium),'') = '' THEN 'Sem UTM'
         ELSE 'Outros'
       END AS origem,
       COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=FALSE
  AND (nm_gateway_plan='livro-odisseia-edicao-colecionador' OR LOWER(nm_gateway_product) LIKE '%odis%')
  AND DATE(dt_ordered_at) >= '2026-07-17'
GROUP BY 1 ORDER BY receita DESC;
