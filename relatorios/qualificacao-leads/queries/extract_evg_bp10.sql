-- Dataset de modelagem: EVG + BP10 (pesquisa in-funnel, cobertura ~66-72%)
-- Fonte canônica: bp-datawarehouse.datamart.dtm_analytics_lead_conversion
-- Alvo: conv = qt_vendas>0 (venda atribuída à campanha; days_to_purchase mediana 0)
-- Dedup: 1 linha por email+campanha (registro mais antigo)
WITH base AS (
  SELECT
    nm_email, nm_tag, dt_registered_at_br, utm_content, utm_source, nm_lead_channel,
    st_member_status_at_registration, bl_is_new_registration,
    IF(qt_vendas > 0, 1, 0) AS conv,
    (SELECT MIN(tx.days_to_purchase) FROM UNNEST(arr_st_approved_transactions) tx
       WHERE tx.days_to_purchase IS NOT NULL) AS days_to_purchase,
    (SELECT SUM(tx.vl_payment_gross) FROM UNNEST(arr_st_approved_transactions) tx) AS ticket,
    ARRAY(SELECT AS STRUCT sr.nm_question AS q, sr.nm_answer AS a
          FROM UNNEST(arr_survey_responses) ar, UNNEST(ar.st_data) sr) AS survey,
    ROW_NUMBER() OVER (PARTITION BY nm_email, nm_tag ORDER BY dt_registered_at_br) AS rn
  FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
  WHERE nm_tag IN ('EVG', 'BP10')
)
SELECT
  nm_tag, dt_registered_at_br, utm_content, utm_source, nm_lead_channel,
  st_member_status_at_registration, bl_is_new_registration,
  conv, days_to_purchase, ticket,
  (SELECT a FROM UNNEST(survey) WHERE q = 'renda' LIMIT 1) AS renda,
  (SELECT a FROM UNNEST(survey) WHERE q = 'relacao_bp' LIMIT 1) AS relacao_bp,
  (SELECT a FROM UNNEST(survey) WHERE q = 'tempo_conhece_bp' LIMIT 1) AS tempo_conhece_bp,
  (SELECT a FROM UNNEST(survey) WHERE q = 'fonte_confianca' LIMIT 1) AS fonte_confianca,
  (SELECT a FROM UNNEST(survey) WHERE q = 'qtd_streaming' LIMIT 1) AS qtd_streaming,
  (SELECT a FROM UNNEST(survey) WHERE q = 'streaming' LIMIT 1) AS streaming,
  (SELECT a FROM UNNEST(survey) WHERE q = 'midia_tradicional' LIMIT 1) AS midia_tradicional,
  (SELECT a FROM UNNEST(survey) WHERE q = 'religiao' LIMIT 1) AS religiao
FROM base
WHERE rn = 1
