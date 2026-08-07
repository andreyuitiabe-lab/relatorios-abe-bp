-- Validação out-of-time honesta: universo = quem NÃO era mecenas em 30/06/2026.
-- Alvo = virou mecenas em jul-ago/2026. Sem isso, quem já é mecenas infla o lift histórico.
-- Compara o modelo de ML existente com os segmentos por regra.
WITH s AS (
  SELECT id_user, cd_percentile_y_predicted_probabilities AS p
  FROM `bp-datawarehouse.ml_models.dtm_lead_score_predictions_upsell_current`
  WHERE nm_target_variable = 'upsell_mecenas_in_30_days'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id_user ORDER BY dt_date DESC) = 1
),

elegivel AS (
  SELECT
    b.*,
    s.p,
    (b.dt_primeiro_mecenas IS NOT NULL AND DATE(b.dt_primeiro_mecenas) >= '2026-07-01') AS converteu
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base` b
  LEFT JOIN s ON s.id_user = b.id_user
  WHERE b.dt_primeiro_mecenas IS NULL OR DATE(b.dt_primeiro_mecenas) >= '2026-07-01'
),

modelo_ml AS (
  SELECT
    'ML: ' || CASE WHEN p IS NULL THEN 'sem score' WHEN p >= 95 THEN 'p95+' WHEN p >= 90 THEN 'p90-95'
                   WHEN p >= 80 THEN 'p80-90' WHEN p >= 50 THEN 'p50-80' ELSE 'p<50' END AS abordagem,
    COUNT(*) AS elegiveis,
    COUNTIF(converteu) AS converteram
  FROM elegivel
  GROUP BY 1
),

segmentos AS (
  SELECT
    CASE
      WHEN vl_capital_social >= 1000000 AND nm_credit_card_level_max IN ('6_black', '5_amex') AND bl_vitalicio = 1
        THEN 'S1 cap1M+ & black/amex & vitalicio'
      WHEN vl_capital_social >= 1000000 AND nm_credit_card_level_max IN ('6_black', '5_amex')
        THEN 'S2 cap1M+ & black/amex'
      WHEN nm_credit_card_level_max IN ('6_black', '5_amex') AND bl_vitalicio = 1 AND vl_total_outras >= 2000
        THEN 'S3 black/amex & vitalicio & 2k+'
      WHEN nm_credit_card_level_max IN ('6_black', '5_amex') AND vl_total_outras >= 2000
        THEN 'S5 black/amex & gasto 2k+'
      WHEN pc_similaridade >= 0.95 AND nm_credit_card_level_max IN ('6_black', '5_amex') AND cd_income_decile >= 9
        THEN 'S4 socio & black/amex & decil9+'
      ELSE 'resto da base' END AS abordagem,
    COUNT(*) AS elegiveis,
    COUNTIF(converteu) AS converteram
  FROM elegivel
  GROUP BY 1
),

todos AS (SELECT * FROM modelo_ml UNION ALL SELECT * FROM segmentos),
tx_base AS (SELECT COUNTIF(converteu) / COUNT(*) AS taxa FROM elegivel)

SELECT
  t.abordagem,
  t.elegiveis,
  t.converteram,
  ROUND(10000 * t.converteram / t.elegiveis, 2) AS conv_por_10k,
  ROUND((t.converteram / t.elegiveis) / tx_base.taxa, 2) AS lift_oot
FROM todos t
CROSS JOIN tx_base
ORDER BY conv_por_10k DESC
