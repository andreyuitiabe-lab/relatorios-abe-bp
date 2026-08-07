-- Como o perfil do doador mudou por safra. Grain = pessoa (id_person), não conta.
WITH mec_tx AS (
  SELECT
    m.id_person,
    DATE(t.dt_ordered_at) AS dt,
    t.vl_payment_gross AS vl,
    t.bl_is_commercial_channel AS com
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-staging.dbt_abe.tb_mecenas_person_map` m
    ON m.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
      OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
    AND t.vl_payment_gross >= 300
    AND DATE(t.dt_ordered_at) >= '2025-01-01'
),

safra AS (
  SELECT
    id_person,
    CASE WHEN dt >= '2026-08-01' THEN '2026-08'
         WHEN dt >= '2026-07-01' THEN '2026-07'
         WHEN dt >= '2026-01-01' THEN '2026 H1'
         ELSE '2025' END AS safra,
    MAX(vl) AS vl,
    MAX(CAST(com AS INT64)) AS com
  FROM mec_tx
  GROUP BY 1, 2
)

SELECT
  s.safra,
  COUNT(*) AS pessoas,
  ROUND(AVG(s.vl)) AS ticket_medio,
  ROUND(100 * AVG(s.com), 0) AS pc_comercial,
  ROUND(100 * AVG(IF(b.cd_income_decile >= 9, 1, 0)), 1) AS pc_decil9mais,
  ROUND(100 * AVG(IF(b.nm_credit_card_level_max IN ('6_black', '5_amex'), 1, 0)), 1) AS pc_black_amex,
  ROUND(100 * AVG(IF(b.pc_similaridade >= 0.95, 1, 0)), 1) AS pc_socio,
  ROUND(100 * AVG(IF(b.vl_capital_social >= 1000000, 1, 0)), 1) AS pc_cap1m,
  ROUND(100 * AVG(b.bl_membro_ativo), 1) AS pc_membro_ativo,
  ROUND(100 * AVG(IF(b.bl_vitalicio = 1, 1, 0)), 1) AS pc_vitalicio,
  ROUND(AVG(b.qt_dias_casa)) AS dias_casa_medio,
  ROUND(AVG(b.vl_total_outras)) AS gasto_previo_medio
FROM safra s
JOIN `bp-staging.dbt_abe.tb_mecenas_qualificacao_base` b USING (id_person)
GROUP BY 1
ORDER BY 1
