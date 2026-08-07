-- Lift de playlist nos 90 dias ANTES da compra de Mecenas.
-- ⚠️ O ponto crítico: o controle usa data-âncora SORTEADA da mesma distribuição de datas de
-- compra dos mecenas. Sem isso, a sazonalidade de lançamento de cada doc domina e produz
-- falso achado (foi o que fez "El Salvador" parecer gatilho — lift real 0,98).
WITH mecenas AS (
  SELECT
    LOWER(c.nm_email) AS email,
    MIN(DATE(t.dt_ordered_at)) AS dt_ancora
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c
    ON c.id_gateway_customer = t.id_gateway_customer
  WHERE t.nm_status = 'approved'
    AND ((t.nm_gateway_plan LIKE 'mecenas%' AND t.nm_gateway_plan <> 'mecenas_bp-essencial')
      OR LOWER(COALESCE(t.nm_gateway_product, '')) LIKE '%mecenas%')
    AND LOWER(COALESCE(t.nm_gateway_offer, '')) NOT LIKE '%order bump%'
    AND t.vl_payment_gross >= 300          -- exclui o order bump de R$180 (não é doador)
    AND DATE(t.dt_ordered_at) >= '2026-01-01'
    AND c.nm_email IS NOT NULL
  GROUP BY 1
),

-- distribuição de datas-âncora, para sortear no controle
datas AS (
  SELECT dt_ancora, ROW_NUMBER() OVER (ORDER BY dt_ancora) - 1 AS idx, COUNT(*) OVER () AS n
  FROM mecenas
),

controle AS (
  SELECT
    b.email,
    (SELECT dt_ancora FROM datas WHERE idx = MOD(ABS(FARM_FINGERPRINT(b.email)), (SELECT n FROM datas LIMIT 1))) AS dt_ancora
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base` b
  WHERE b.bl_membro_ativo = 1 AND NOT b.bl_is_mecenas
),

universo AS (
  SELECT email, dt_ancora, 'mecenas' AS grupo FROM mecenas
  UNION ALL
  SELECT email, dt_ancora, 'controle' FROM controle
),

-- sessões na janela de 90 dias antes da âncora
vistas AS (
  SELECT DISTINCT u.grupo, u.email, v.nm_playlist
  FROM universo u
  JOIN `bp-datawarehouse.datamart.obt_kafka__view_sessions` v
    ON LOWER(v.nm_email) = u.email
   AND DATE(v.dt_created_at) BETWEEN DATE_SUB(u.dt_ancora, INTERVAL 90 DAY) AND u.dt_ancora
  WHERE v.vl_watch_time_seconds >= 300     -- 5 min = sessão real
    AND v.nm_playlist IS NOT NULL
),

tot AS (
  SELECT grupo, COUNT(*) AS n FROM universo GROUP BY 1
)

SELECT
  v.nm_playlist AS playlist,
  COUNTIF(v.grupo = 'mecenas') AS n_mecenas,
  ROUND(100 * COUNTIF(v.grupo = 'mecenas') / (SELECT n FROM tot WHERE grupo = 'mecenas'), 2) AS pc_mecenas,
  ROUND(100 * COUNTIF(v.grupo = 'controle') / (SELECT n FROM tot WHERE grupo = 'controle'), 2) AS pc_controle,
  ROUND(
    SAFE_DIVIDE(
      COUNTIF(v.grupo = 'mecenas') / (SELECT n FROM tot WHERE grupo = 'mecenas'),
      COUNTIF(v.grupo = 'controle') / (SELECT n FROM tot WHERE grupo = 'controle')
    ), 2) AS lift
FROM vistas v
GROUP BY 1
HAVING n_mecenas >= 30
ORDER BY lift DESC
