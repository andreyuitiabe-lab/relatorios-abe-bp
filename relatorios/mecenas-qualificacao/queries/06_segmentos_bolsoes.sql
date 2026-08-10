-- Entregável acionável: segmentos de abordagem e tamanho do bolsão ainda não convertido.
-- Ordem do CASE importa (segmentos mutuamente exclusivos, do mais forte para o mais fraco).
WITH b AS (
  SELECT *,
    (nm_credit_card_level_max IN ('6_black', '5_amex')) AS premium,
    (pc_similaridade >= 0.95) AS socio,
    (vl_capital_social >= 1000000) AS cap1m,
    (cd_income_decile >= 9) AS rico
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
),

seg AS (
  SELECT *,
    CASE
      WHEN cap1m AND premium AND bl_vitalicio = 1 THEN 'S1 Patrono: cap1M+ & black/amex & vitalicio'
      WHEN cap1m AND premium THEN 'S2 Empresario premium: cap1M+ & black/amex'
      WHEN premium AND bl_vitalicio = 1 AND vl_total_outras >= 2000 THEN 'S3 Fiel rico: black/amex & vitalicio & 2k+'
      WHEN socio AND premium AND rico THEN 'S4 Socio qualificado: socio & black/amex & decil9+'
      WHEN premium AND vl_total_outras >= 2000 THEN 'S5 Alto gasto premium'
      WHEN bl_certificacao = 1 AND premium THEN 'S6 Certificacao & premium'
    END AS segmento
  FROM b
)

SELECT
  segmento,
  COUNT(*) AS total_pessoas,
  COUNTIF(bl_is_mecenas) AS ja_mecenas,
  COUNTIF(NOT bl_is_mecenas) AS bolsao_abordavel,
  COUNTIF(NOT bl_is_mecenas AND bl_membro_ativo = 1) AS bolsao_membro_ativo,
  ROUND(100 * COUNTIF(bl_is_mecenas) / COUNT(*), 1) AS pc_ja_convertido,
  ROUND((COUNTIF(bl_is_mecenas) / COUNT(*)) / 0.00584, 1) AS lift_vs_base,
  ROUND(AVG(IF(bl_is_mecenas, vl_total_mecenas, NULL))) AS ticket_medio_esperado
FROM seg
WHERE segmento IS NOT NULL
GROUP BY 1
ORDER BY lift_vs_base DESC
