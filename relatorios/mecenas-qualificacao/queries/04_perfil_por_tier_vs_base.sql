-- Perfil comparado: cada tier de Mecenas vs o membro ativo padrão (grupo de controle).
-- É a ficha "quem é o mecenas x quem é a base".
SELECT
  CASE WHEN bl_is_mecenas AND vl_maior_tx_mecenas > 10000 THEN 'Bolsa: alto (> R$ 10 mil)'
       WHEN bl_is_mecenas AND vl_maior_tx_mecenas >= 2000 THEN 'Bolsa: múltiplas (R$ 2 a 10 mil)'
       WHEN bl_is_mecenas THEN 'Bolsa: única (R$ 1 a 2 mil)'
       WHEN bl_is_solidario THEN 'Mecenas Solidário (campanha atual)'
       WHEN bl_membro_ativo = 1 THEN 'MEMBRO ATIVO (controle)'
       ELSE 'ex-comprador inativo' END AS grupo,
  COUNT(*) AS pessoas,
  ROUND(100 * AVG(IF(cd_income_decile >= 9, 1, 0)), 1) AS pc_decil9mais,
  ROUND(100 * AVG(IF(cd_income_decile >= 7, 1, 0)), 1) AS pc_decil7mais,
  ROUND(100 * AVG(IF(nm_credit_card_level_max IN ('6_black', '5_amex'), 1, 0)), 1) AS pc_black_amex,
  ROUND(100 * AVG(IF(nm_credit_card_level_max IN ('6_black', '5_amex', '4_platinum'), 1, 0)), 1) AS pc_premium,
  ROUND(100 * AVG(IF(pc_similaridade >= 0.95, 1, 0)), 1) AS pc_socio,
  ROUND(100 * AVG(IF(vl_capital_social >= 1000000, 1, 0)), 1) AS pc_cap1m,
  ROUND(100 * AVG(IF(nm_gender_inferred = 'Feminino', 1, 0)), 1) AS pc_fem,
  ROUND(AVG(qt_idade), 1) AS idade_media,
  ROUND(AVG(qt_dias_casa)) AS dias_casa,
  ROUND(AVG(vl_total_outras)) AS gasto_nao_mecenas,
  ROUND(AVG(qt_tx_outras), 1) AS tx_nao_mecenas,
  ROUND(100 * AVG(bl_vitalicio), 1) AS pc_vitalicio,
  ROUND(100 * AVG(bl_certificacao), 1) AS pc_certif,
  ROUND(100 * AVG(bl_cdl), 1) AS pc_cdl
FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
GROUP BY 1
ORDER BY pessoas DESC
