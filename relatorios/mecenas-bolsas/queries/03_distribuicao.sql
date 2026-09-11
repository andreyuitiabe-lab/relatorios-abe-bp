-- Bolsas Mecenas DISTRIBUÍDAS: contas de beneficiário ativadas na plataforma, por ano × sistema.
-- Três sistemas de provisionamento (wiki mecenas.md, "Lado beneficiário"):
--   novo (bolsa-mecenas)  → planos bolsa-mecenas-best/good (mar/2026+)
--   legado (donator)      → nm_type = 'donator' (2020 a ago/2022, tudo cancelado)
--   caverna (manual)      → nm_create_reason_type = 'mecenas' ("Aluno de instituição parceira")
WITH bolsas AS (
  SELECT
    EXTRACT(YEAR FROM dt_started_at) AS ano,
    id_user,
    CASE
      WHEN nm_plan LIKE 'bolsa-mecenas%' THEN 'novo (bolsa-mecenas)'
      WHEN nm_type = 'donator'           THEN 'legado (donator)'
      ELSE 'caverna (manual)'
    END AS sistema,
    (nm_status IN ('active', 'wo renewal')
      AND dt_started_at <= CURRENT_DATETIME()
      AND dt_expires_in >= CURRENT_DATETIME()) AS bl_vigente
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_create_reason_type = 'mecenas'
     OR nm_type = 'donator'
     OR nm_plan LIKE 'bolsa-mecenas%'
)

SELECT
  ano,
  sistema,
  COUNT(*)                                    AS qt_assinaturas,
  COUNT(DISTINCT id_user)                     AS qt_contas,
  COUNTIF(bl_vigente)                         AS qt_vigentes,
  COUNT(DISTINCT IF(bl_vigente, id_user, NULL)) AS qt_contas_vigentes
FROM bolsas
GROUP BY ano, sistema
ORDER BY ano, sistema
