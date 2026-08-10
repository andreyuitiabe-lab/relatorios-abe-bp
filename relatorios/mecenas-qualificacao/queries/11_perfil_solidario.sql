-- Perfil de quem compra o MECENAS SOLIDÁRIO (campanha atual, jul/2026+).
-- Produto recorrente a partir de ~R$ 30/mês, sem teto — população distinta do doador de bolsa.
-- Compara três grupos: Solidário · doador de bolsa (>= R$ 1.000) · membro ativo (controle).
SELECT
  CASE WHEN bl_is_solidario AND bl_is_mecenas THEN 'Solidário QUE JÁ ERA doador de bolsa'
       WHEN bl_is_solidario                   THEN 'Solidário (novo na doação)'
       WHEN bl_is_mecenas                     THEN 'Doador de bolsa (>= R$ 1.000)'
       WHEN bl_membro_ativo = 1                THEN 'Membro ativo (controle)'
  END AS grupo,
  COUNT(*) AS pessoas,
  ROUND(SUM(vl_total_solidario + vl_total_mecenas)) AS receita_doacao,
  ROUND(AVG(IF(bl_is_solidario, vl_maior_tx_solidario, vl_maior_tx_mecenas))) AS doacao_media,
  ROUND(APPROX_QUANTILES(IF(bl_is_solidario, vl_maior_tx_solidario, vl_maior_tx_mecenas), 2)[OFFSET(1)]) AS doacao_mediana,
  -- perfil socioeconômico
  ROUND(100 * AVG(IF(cd_income_decile >= 9, 1, 0)), 1) AS pc_renda_topo,
  ROUND(100 * AVG(IF(nm_credit_card_level_max IN ('6_black', '5_amex'), 1, 0)), 1) AS pc_cartao_topo,
  ROUND(100 * AVG(IF(nm_credit_card_level_max IS NULL, 1, 0)), 1) AS pc_sem_cartao,
  ROUND(100 * AVG(IF(pc_similaridade >= 0.95, 1, 0)), 1) AS pc_socio,
  ROUND(100 * AVG(IF(vl_capital_social >= 1000000, 1, 0)), 1) AS pc_capital_1m,
  -- histórico na BP
  ROUND(AVG(vl_total_outras)) AS gasto_previo,
  ROUND(APPROX_QUANTILES(vl_total_outras, 2)[OFFSET(1)]) AS gasto_previo_mediana,
  ROUND(AVG(qt_tx_outras), 1) AS compras_previas,
  ROUND(100 * AVG(bl_vitalicio), 1) AS pc_vitalicio,
  ROUND(100 * AVG(bl_certificacao), 1) AS pc_certificacao,
  ROUND(100 * AVG(bl_cdl), 1) AS pc_cdl,
  ROUND(100 * AVG(IF(vl_total_outras < 100, 1, 0)), 1) AS pc_quase_nada_antes,
  -- demografia e relação
  ROUND(100 * AVG(IF(nm_gender_inferred = 'Feminino', 1, 0)), 1) AS pc_feminino,
  ROUND(AVG(qt_idade), 1) AS idade,
  ROUND(AVG(qt_dias_casa) / 365, 1) AS anos_casa,
  ROUND(100 * AVG(bl_membro_ativo), 1) AS pc_membro_ativo,
  ROUND(100 * AVG(bl_ja_comprou_comercial), 1) AS pc_via_comercial
FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
WHERE bl_is_solidario OR bl_is_mecenas OR bl_membro_ativo = 1
GROUP BY 1
HAVING grupo IS NOT NULL
ORDER BY pessoas
