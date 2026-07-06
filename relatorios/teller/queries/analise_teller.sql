-- Análise Teller 2026 — queries de apoio
-- Fonte vendas: masterdata.fct_transactions | Engajamento: events.fct_mixpanel__teller_*
-- Filtro padrão: nm_status='approved' AND bl_is_renovation=FALSE

-- =====================================================================
-- A1) Vendas do PRODUTO Teller por mês
-- =====================================================================
SELECT FORMAT_DATE('%Y-%m', DATE(dt_ordered_at)) mes,
       CASE WHEN nm_gateway_plan='teller' THEN 'teller_standalone'
            WHEN nm_gateway_plan='premium-teller' THEN 'premium_teller'
            WHEN nm_gateway_plan='intermediario-teller' THEN 'interm_teller'
            WHEN bl_lifetime_offer THEN 'vitalicio_teller' END tipo,
       COUNT(*) n, ROUND(SUM(vl_payment_gross)) receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='2026-01-01'
  AND (nm_gateway_plan IN ('teller','premium-teller','intermediario-teller')
       OR (bl_lifetime_offer AND LOWER(nm_gateway_product) LIKE '%teller%'))
GROUP BY 1,2 ORDER BY 1,2;

-- =====================================================================
-- A2) Vendas atribuídas à CAMPANHA Teller (utm TLR/TLR12) por mês e intenção
-- =====================================================================
SELECT FORMAT_DATE('%Y-%m', DATE(dt_ordered_at)) mes,
       CASE WHEN LOWER(nm_pptc_utm_campaign) LIKE '%membro%' OR LOWER(nm_pptc_utm_campaign) LIKE '%cross%' THEN 'membros_crosssell'
            WHEN LOWER(nm_pptc_utm_campaign) LIKE '%recupera%' THEN 'recuperacao'
            ELSE 'aquisicao_geral' END intencao,
       COUNT(*) n, ROUND(SUM(vl_payment_gross)) receita
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='2026-01-01'
  AND REGEXP_CONTAINS(LOWER(nm_pptc_utm_campaign), r'(^|[^a-z])tlr([^a-z]|$)|tlr12')
GROUP BY 1,2 ORDER BY 1,2;

-- =====================================================================
-- B) Perfil do comprador (membro / ex-membro / não-membro) NO MOMENTO da 1a compra Teller
--    Membership = acesso não-Teller: assinatura paga ativa OU vitalício anterior
-- =====================================================================
WITH teller_buyers AS (
  SELECT id_gateway_customer,
         MIN(dt_ordered_at) dt_teller,
         ARRAY_AGG(nm_gateway_plan ORDER BY dt_ordered_at LIMIT 1)[OFFSET(0)] plano
  FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='2026-01-01'
    AND nm_gateway_plan IN ('teller','premium-teller','intermediario-teller')
  GROUP BY 1),
subs AS (SELECT id_gateway_customer, dt_started_at, dt_expires_in FROM masterdata.dim_subscriptions
         WHERE nm_type='paid' AND (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%')),
vital AS (SELECT DISTINCT id_gateway_customer, dt_ordered_at dt_vital FROM masterdata.fct_transactions
          WHERE nm_status='approved' AND bl_lifetime_offer AND LOWER(nm_gateway_product) NOT LIKE '%teller%'),
classificado AS (
  SELECT b.plano,
    (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=b.id_gateway_customer AND s.dt_started_at<b.dt_teller AND s.dt_expires_in>=b.dt_teller) ativo_now,
    (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=b.id_gateway_customer AND s.dt_started_at<b.dt_teller) teve_sub,
    (SELECT COUNT(1) FROM vital v WHERE v.id_gateway_customer=b.id_gateway_customer AND v.dt_vital<b.dt_teller) teve_vital
  FROM teller_buyers b)
SELECT CASE WHEN plano='premium-teller' THEN 'premium_teller' ELSE 'teller_standalone' END tipo,
  CASE WHEN ativo_now>0 OR teve_vital>0 THEN '1_membro'
       WHEN teve_sub>0 THEN '2_ex_membro' ELSE '3_nao_membro' END perfil,
  COUNT(*) compradores
FROM classificado GROUP BY 1,2 ORDER BY 1,2;

-- =====================================================================
-- C) Funil: não-membros que entram por Teller e depois compram membership plena
-- =====================================================================
WITH teller_buyers AS (
  SELECT id_gateway_customer, MIN(dt_ordered_at) dt_teller
  FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND dt_ordered_at>='2026-01-01'
    AND nm_gateway_plan IN ('teller','premium-teller','intermediario-teller')
  GROUP BY 1),
subs AS (SELECT id_gateway_customer, dt_started_at, dt_expires_in FROM masterdata.dim_subscriptions
         WHERE nm_type='paid' AND (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%')),
vital AS (SELECT DISTINCT id_gateway_customer, dt_ordered_at dt_vital FROM masterdata.fct_transactions
          WHERE nm_status='approved' AND bl_lifetime_offer AND LOWER(nm_gateway_product) NOT LIKE '%teller%'),
nao_membros AS (
  SELECT b.id_gateway_customer, b.dt_teller FROM teller_buyers b
  WHERE (SELECT COUNT(1) FROM subs s WHERE s.id_gateway_customer=b.id_gateway_customer AND s.dt_started_at<b.dt_teller)=0
    AND (SELECT COUNT(1) FROM vital v WHERE v.id_gateway_customer=b.id_gateway_customer AND v.dt_vital<b.dt_teller)=0),
conv AS (
  SELECT DISTINCT n.id_gateway_customer FROM nao_membros n
  JOIN masterdata.fct_transactions t ON t.id_gateway_customer=n.id_gateway_customer
  WHERE t.nm_status='approved' AND t.dt_ordered_at > n.dt_teller AND t.nm_gateway_plan NOT LIKE '%teller%'
    AND (t.nm_gateway_plan IN ('good','better','best','black','supporter','mecenas') OR t.bl_lifetime_offer))
SELECT (SELECT COUNT(*) FROM nao_membros) nao_membros_teller,
       (SELECT COUNT(*) FROM conv) converteram_p_membro;

-- =====================================================================
-- D1) Engajamento (escuta) por mês
-- =====================================================================
SELECT FORMAT_DATE('%Y-%m', DATE(time)) mes,
       COUNT(*) playbacks, COUNT(DISTINCT user_id) ouvintes, COUNT(DISTINCT media_id) livros_tocados
FROM events.fct_mixpanel__teller_media_playback_events
WHERE time>='2026-01-01' GROUP BY 1 ORDER BY 1;

-- =====================================================================
-- D2) Quem são os ouvintes (membership atual). user_id = dim_user.id_user
-- =====================================================================
WITH ouvintes AS (SELECT DISTINCT user_id FROM events.fct_mixpanel__teller_media_playback_events WHERE time>='2026-01-01' AND user_id IS NOT NULL),
sub_ativa AS (
  SELECT DISTINCT id_user,
    MAX(CASE WHEN (nm_gateway_plan IS NULL OR nm_gateway_plan NOT LIKE '%teller%') THEN 1 ELSE 0 END) tem_full,
    MAX(CASE WHEN nm_gateway_plan LIKE '%teller%' THEN 1 ELSE 0 END) tem_teller
  FROM masterdata.dim_subscriptions
  WHERE nm_type='paid' AND nm_status IN ('active','wo renewal')
    AND dt_started_at<=CURRENT_DATETIME() AND dt_expires_in>=CURRENT_DATETIME() GROUP BY 1),
vital AS (SELECT DISTINCT s.id_user FROM masterdata.fct_transactions t JOIN masterdata.dim_subscriptions s USING(id_gateway_customer)
          WHERE t.nm_status='approved' AND t.bl_lifetime_offer)
SELECT CASE WHEN v.id_user IS NOT NULL OR sa.tem_full=1 THEN '1_membro_pleno_ativo'
            WHEN sa.tem_teller=1 THEN '2_so_teller_ativo' ELSE '3_sem_assinatura_ativa' END perfil,
  COUNT(*) ouvintes
FROM ouvintes o LEFT JOIN sub_ativa sa ON sa.id_user=o.user_id LEFT JOIN vital v ON v.id_user=o.user_id
GROUP BY 1 ORDER BY 1;

-- D3) Top audiolivros e gêneros: JOIN media_id = dim_teller__audiobooks.id_book (ver export_transacoes.sql p/ granular)
