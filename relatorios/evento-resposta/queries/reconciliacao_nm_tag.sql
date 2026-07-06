-- Reconciliação: cadastros/respostas do lançamento inteiro por nm_tag (métrica do dash oficial)
SELECT UPPER(nm_tag) AS lancamento,
      COUNT(*) AS tag_cad,
      COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) AS tag_resp,
      ROUND(COUNTIF(ARRAY_LENGTH(arr_survey_responses) > 0) / COUNT(*) * 100, 1) AS tag_taxa
    FROM `bp-datawarehouse.datamart.dtm_analytics_lead_conversion`
    WHERE dt_registered_at_br >= '2026-06-19' AND UPPER(nm_tag) IN ('EVG', 'BP10')
    GROUP BY 1
