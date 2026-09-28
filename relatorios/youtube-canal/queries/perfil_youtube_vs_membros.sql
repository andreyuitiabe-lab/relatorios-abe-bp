-- Perfil etário e de gênero: membros ativos × compradores novos de 2026.
-- Serve para comparar com a demografia da audiência do YouTube (Analytics API,
-- dimensions=ageGroup,gender — está no data.json do relatório).
--
-- ⚠️ RESSALVAS
-- 1. `dt_birthday` cobre só ~22% dos membros ativos. Quem informa data pode não ser
--    representativo — a comparação é indicativa, não censitária.
-- 2. O YouTube reporta % de VIEWS (quem assiste mais pesa mais); aqui é % de PESSOAS.
--    Não são a mesma unidade; a comparação vale para direção, não para precisão.
-- 3. `fct_transactions` não tem id_user — o caminho é via id_subscription → dim_subscriptions.

WITH ativos AS (
  SELECT DISTINCT s.id_user
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  WHERE s.dt_expires_in > CURRENT_DATETIME()
    AND LOWER(s.nm_status) IN ('active','ativo','paid')
),

novos_2026 AS (                                  -- comprou pela primeira vez uma assinatura em 2026
  SELECT DISTINCT s.id_user
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_subscriptions` s USING (id_subscription)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE               -- venda nova (ver bq-regras.md)
    AND DATE(t.dt_ordered_at) BETWEEN '2026-01-01' AND '2026-09-19'
    AND s.id_user IS NOT NULL
),

base AS (
  SELECT
    du.id_user,
    DATE_DIFF(CURRENT_DATE(), DATE(du.dt_birthday), YEAR) AS idade,
    LOWER(du.nm_gender_inferred)                          AS genero,   -- inferido por nome (IBGE), ~86% preenchido
    a.id_user IS NOT NULL                                 AS eh_ativo,
    n.id_user IS NOT NULL                                 AS eh_novo_2026
  FROM `bp-datawarehouse.masterdata.dim_user` du
  LEFT JOIN ativos      a USING (id_user)
  LEFT JOIN novos_2026  n USING (id_user)
  WHERE a.id_user IS NOT NULL OR n.id_user IS NOT NULL
)

SELECT
  CASE
    WHEN idade BETWEEN 13 AND 17 THEN '13-17'
    WHEN idade BETWEEN 18 AND 24 THEN '18-24'
    WHEN idade BETWEEN 25 AND 34 THEN '25-34'
    WHEN idade BETWEEN 35 AND 44 THEN '35-44'
    WHEN idade BETWEEN 45 AND 54 THEN '45-54'
    WHEN idade BETWEEN 55 AND 64 THEN '55-64'
    WHEN idade >= 65              THEN '65+'
    ELSE 'zz sem data'
  END                                                  AS faixa,
  COUNTIF(eh_ativo)                                    AS membros_ativos,
  COUNTIF(eh_novo_2026)                                AS compradores_novos_2026,
  ROUND(100 * COUNTIF(eh_ativo AND genero = 'feminino')
            / NULLIF(COUNTIF(eh_ativo AND genero IS NOT NULL), 0), 1) AS pct_feminino_ativos
FROM base
GROUP BY faixa
ORDER BY faixa
