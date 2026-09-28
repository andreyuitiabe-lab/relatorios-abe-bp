-- Gênero dos membros ativos (inferido pelo primeiro nome via IBGE, ~86% preenchido em dim_user).
-- Comparar com a audiência do YouTube (Analytics API, dimensions=gender) — o YouTube mede % das views.
WITH ativos AS (
  SELECT DISTINCT s.id_user
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  WHERE s.dt_expires_in > CURRENT_DATETIME()
    AND LOWER(s.nm_status) IN ('active','ativo','paid')
)
SELECT
  COALESCE(LOWER(du.nm_gender_inferred), 'sem dado') AS genero,
  COUNT(*)                                           AS pessoas
FROM `bp-datawarehouse.masterdata.dim_user` du
JOIN ativos a USING (id_user)
GROUP BY genero
ORDER BY pessoas DESC
