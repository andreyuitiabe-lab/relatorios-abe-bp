-- Vitalício: base de oportunidades para upsell (GBB sem Black, certificação sem Black)
-- Usar como ponto de partida para lista do Comercial

WITH

vitalicio_atual AS (
  SELECT
    t.id_gateway_customer,
    MAX(CASE
      WHEN LOWER(t.nm_gateway_plan) LIKE '%black%' THEN 1 ELSE 0
    END) AS tem_black,
    MAX(CASE
      WHEN LOWER(t.nm_gateway_plan) LIKE '%premium%'
        OR LOWER(t.nm_gateway_plan) LIKE '%gbb%' THEN 1 ELSE 0
    END) AS tem_gbb,
    MAX(CASE
      WHEN LOWER(t.nm_gateway_plan) IN (
        'travessia', 'travessia-familia',
        'bitcoin', 'desafio-bitcoin', 'funil-bitcoin',
        'ciencia-politica', 'funil-ciencia-politica',
        'geopolitica', 'funil-geopolitica',
        'metodo-bp'
      ) THEN 1 ELSE 0
    END) AS tem_certificacao
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND (
      LOWER(t.nm_plan_label) LIKE '%vitalício%'
      OR LOWER(t.nm_plan_label) LIKE '%vitalicio%'
      OR t.nm_gateway_plan IN (
        'travessia', 'travessia-familia',
        'bitcoin', 'desafio-bitcoin', 'funil-bitcoin',
        'ciencia-politica', 'funil-ciencia-politica',
        'geopolitica', 'funil-geopolitica',
        'metodo-bp'
      )
    )
  GROUP BY 1
)

SELECT
  CASE
    WHEN tem_black = 0 AND tem_gbb = 1      THEN 'GBB sem Black'
    WHEN tem_black = 0 AND tem_certificacao = 1 THEN 'Certificação sem Black'
    WHEN tem_black = 0 AND tem_gbb = 0      THEN 'Básico sem upsell'
    ELSE 'Já tem Black'
  END                             AS segmento,
  COUNT(*)                        AS clientes
FROM vitalicio_atual
GROUP BY segmento
ORDER BY clientes DESC
