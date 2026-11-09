-- Deal da Pipedrive que levou cada venda de vitalício da BNO26 (dtm_seller_conversion_rate, venda achada no
-- arr_st_commercial_transactions; se houver mais de um, o deal mais recente) e, no hotlead, a transação que
-- gerou o deal (id_source_transaction → fct_transactions). Sem PII na saída.
-- ⚠️ vl_source_payment_gross / nm_source_gateway_plan do mart mentem (vêm da transação atual): por isso o join na fct.
-- Parâmetros: {ini_bno26} {fim_bno26}

WITH vit AS (
  SELECT t.id_transaction, t.dt_ordered_at, t.vl_payment_gross, t.nm_plan_label, t.nm_gateway_plan, t.nm_gateway_product
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status='approved' AND NOT t.bl_is_renovation AND t.bl_lifetime_offer
    AND DATE(t.dt_ordered_at) BETWEEN '{ini_bno26}' AND '{fim_bno26}'
    AND (t.nm_gateway_plan IN ('good','better','best','black') OR LOWER(t.nm_gateway_product) LIKE '%vital%')
    AND NOT REGEXP_CONTAINS(t.nm_gateway_plan, r'^(livro-odisseia|odisseia-|clube-do-livro|black-clube-do-livro|ebooks-|analises-clube-livro|educacao-literaria|colecao-brasil-a-ultima-cruzada|teller$)')
    AND NOT LOWER(t.nm_gateway_product) LIKE '%membro fundador%'
),
deal AS (
  SELECT ct.id_transaction, m.id_pipedrive_deal, m.nm_commercial_channel, m.nm_hotlead_type, m.nm_deal_source, m.nm_transaction_trigger,
         m.id_source_transaction, m.dt_created_at dt_deal, m.nm_stage
  FROM `bp-datawarehouse.datamart.dtm_seller_conversion_rate` m, UNNEST(m.arr_st_commercial_transactions) ct
  WHERE m.dt_created_at >= '2025-01-01'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY ct.id_transaction ORDER BY m.dt_created_at DESC) = 1
)
SELECT v.*, d.* EXCEPT(id_transaction),
  s.dt_ordered_at dt_src, s.nm_status src_status, s.bl_is_renovation src_renov, s.bl_is_commercial_channel src_comercial,
  s.nm_plan_label src_plano, s.nm_gateway_product src_produto, s.vl_payment_gross src_valor, s.bl_lifetime_offer src_vit,
  COALESCE(s.nm_pptc_utm_campaign, s.nm_pptc_tracking_name) src_campanha
FROM vit v
LEFT JOIN deal d USING (id_transaction)
LEFT JOIN `bp-datawarehouse.masterdata.fct_transactions` s ON s.id_transaction = d.id_source_transaction
