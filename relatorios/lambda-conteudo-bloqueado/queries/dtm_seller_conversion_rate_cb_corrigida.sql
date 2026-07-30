-- Atribuição CORRIGIDA da campanha "Conteúdo bloqueado" (leads Lambda)
-- sobre dtm_seller_conversion_rate.
--
-- O que corrige (ver wiki fluxo-comercial.md, seção da campanha CB):
--   1. Pendura no deal CB as vendas Lambda (C0113) da pessoa — que o modelo
--      original espalha em outros deals (HOT LEAD do bot, AWSALES etc.),
--      porque 67% das vendas C0113 chegam sem nm_salesman_email e o fallback
--      de recência escolhe outro deal.
--   2. Remove do deal CB as vendas de outros canais/vendedores (C0036, C0104...)
--      que o modelo pendurou só por recência.
--
-- ⚠️ Não usa a janela do modelo (venda >= criação do deal − 2h): a conversa da
-- Lambda roda DIAS antes do card existir no Pipe (deals criados em lote 20/07,
-- vendas desde 15/07) — 21 das 25 vendas ficariam de fora. O corte passa a ser
-- o período da campanha (dt_inicio_campanha) + match por pessoa; a flag
-- bl_venda_antes_do_deal marca as vendas anteriores ao card, para auditoria.
--
-- Resultado: 1 linha por deal CB com venda, com array de transações Lambda.
-- Total da campanha = SUM(vl_total_lambda) / SUM(qt_vendas_lambda).

WITH params AS (
  SELECT DATETIME '2026-07-15 00:00:00' AS dt_inicio_campanha
),

cb_deals AS (
  SELECT
    id_pipedrive_deal,
    id_person,
    nm_person_name,
    LOWER(nm_person_email) AS email,
    REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]', '') AS tel,
    nm_title,
    nm_salesman_email AS owner_atual,
    dt_created_at,
    -- o que o modelo original atribuiu (para auditoria)
    arr_st_commercial_transactions AS arr_modelo_original
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate`
  WHERE nm_label = 'Conteúdo bloqueado'
     OR nm_deal_source = 'Conteúdo bloqueado'
     OR (nm_title LIKE 'UPSELL |%' AND DATE(dt_created_at) >= '2026-07-01')
),

lambda_sales AS (
  -- regra canônica de venda Lambda (wiki fluxo-comercial.md)
  SELECT
    t.id_transaction,
    t.dt_ordered_at,
    t.vl_payment_gross,
    t.nm_gateway_plan,
    t.nm_payment_method,
    LOWER(c.nm_email) AS email,
    REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]', '') AS tel
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  CROSS JOIN params
  WHERE t.nm_status = 'approved'
    AND ( UPPER(t.nm_pptc_tracking_name) LIKE '%C0113%'
       OR LOWER(t.nm_gateway_product) LIKE '%lambda%'
       OR LOWER(t.nm_gateway_offer) LIKE '%lambda%' )
    AND t.dt_ordered_at >= params.dt_inicio_campanha
),

-- match venda Lambda × deal CB da mesma pessoa (email e telefone em joins
-- separados — OR no ON vira cross-join)
matched AS (
  SELECT s.*, d.id_pipedrive_deal, d.dt_created_at AS dt_deal_criado
  FROM lambda_sales s
  JOIN cb_deals d ON s.email = d.email AND s.email IS NOT NULL AND s.email != ''
  UNION DISTINCT
  SELECT s.*, d.id_pipedrive_deal, d.dt_created_at
  FROM lambda_sales s
  JOIN cb_deals d ON s.tel = d.tel AND s.tel IS NOT NULL AND s.tel != ''
),

-- se a pessoa tiver mais de um deal CB, a venda fica no criado mais perto dela
matched_nodup AS (
  SELECT *
  FROM matched
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY id_transaction
    ORDER BY ABS(DATETIME_DIFF(dt_ordered_at, dt_deal_criado, MINUTE))
  ) = 1
),

vendas_por_deal AS (
  SELECT
    id_pipedrive_deal,
    COUNT(*) AS qt_vendas_lambda,
    SUM(vl_payment_gross) AS vl_total_lambda,
    ARRAY_AGG(
      STRUCT(
        id_transaction,
        dt_ordered_at,
        nm_gateway_plan,
        nm_payment_method,
        vl_payment_gross,
        dt_ordered_at < dt_deal_criado AS bl_venda_antes_do_deal
      )
      ORDER BY dt_ordered_at
    ) AS arr_vendas_lambda
  FROM matched_nodup
  GROUP BY 1
),

-- vendas que o modelo ORIGINAL pendurou no deal CB mas não são Lambda (excluir do dash)
vendas_erradas_no_original AS (
  SELECT
    d.id_pipedrive_deal,
    COUNT(*) AS qt_vendas_nao_lambda_no_original,
    SUM(ct.vl_payment_gross) AS vl_nao_lambda_no_original
  FROM cb_deals d, UNNEST(d.arr_modelo_original) ct
  WHERE ct.id_transaction NOT IN (SELECT id_transaction FROM lambda_sales)
  GROUP BY 1
)

SELECT
  d.id_pipedrive_deal,
  d.id_person,
  d.nm_person_name,
  d.email,
  d.nm_title,
  d.owner_atual,
  d.dt_created_at,
  COALESCE(v.qt_vendas_lambda, 0) AS qt_vendas_lambda,
  COALESCE(v.vl_total_lambda, 0) AS vl_total_lambda,
  v.arr_vendas_lambda,
  COALESCE(e.qt_vendas_nao_lambda_no_original, 0) AS qt_vendas_nao_lambda_no_original,
  COALESCE(e.vl_nao_lambda_no_original, 0) AS vl_nao_lambda_no_original
FROM cb_deals d
LEFT JOIN vendas_por_deal v USING (id_pipedrive_deal)
LEFT JOIN vendas_erradas_no_original e USING (id_pipedrive_deal)
WHERE v.id_pipedrive_deal IS NOT NULL OR e.id_pipedrive_deal IS NOT NULL
ORDER BY vl_total_lambda DESC
