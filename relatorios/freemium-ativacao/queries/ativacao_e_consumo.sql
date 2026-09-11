-- =====================================================================================
-- Freemium: quem ativa e o que consome
--
-- Responde duas coisas numa query só (coluna `secao` separa):
--   resumo   -> quantos da coorte ativaram, em 24h / 7d / 30d, e quantos nunca ativaram
--   conteudo -> o que foi consumido, por playlist e mídia, com alcance e horas
--
-- ------------------------------------------------------------------------------------
-- COMO A COORTE É DEFINIDA (as três regras que mudam o número)
--
-- 1. Freemium NÃO é `'free' IN UNNEST(dim_user.arr_roles)`. Esse papel é estado ATUAL e
--    some quando a pessoa converte — filtrar por ele subconta justamente os convertidos.
--    Aqui: criou conta e NÃO tinha compra aprovada até 1h depois do cadastro.
--
-- 2. A conta tem de nascer junto ou depois do download. Sem isso entra quem já era
--    cadastrado e só baixou o app depois — gente que converte muito mais e infla tudo.
--    ⚠️ A tolerância de 1h é obrigatória, não é folga de relógio: o `first_open` costuma
--    ser gravado DEPOIS do `dim_user.dt_created_at` na mesma sessão. Corte estrito
--    (`install <= cadastro`) descarta ~1/3 dos cadastros legítimos.
--
-- 3. A ponte device->conta é o primeiro evento posterior do mesmo `id_pseudo_user` com
--    `id_user` preenchido. O `first_open` tem `id_user` SEMPRE nulo.
--
-- ------------------------------------------------------------------------------------
-- ATIVAÇÃO
--
-- Aqui ativação = qualquer interação em `obt_user_media_interactions` (deu play). Se o que
-- você quer é consumo com profundidade, troque por `vl_total_watch_time_seconds >= 300`
-- (5 min), que é o critério usado no relatório "Essa galera assiste e compra?".
--
-- Medido em jul/2026 com esta definição: 50,5% ativam no MESMO DIA, 60,2% em 24h e 66,2%
-- em 30 dias. Ou seja, 91% de toda a ativação acontece até D+1 — ação de ativação depois
-- de 48h chega tarde.
--
-- ⚠️ GRAFIA: conteúdo da Tecnocracia se chama `Technocracia`, com H. Regex em `tecnocra`
-- volta VAZIO em silêncio.
-- =====================================================================================

DECLARE d0 DATE DEFAULT '2026-07-01';   -- início da coorte (data de CADASTRO)
DECLARE d1 DATE DEFAULT '2026-08-05';   -- fim da coorte. Deixe >= 30 dias no passado para
                                        -- a janela de 30d fechar; senão ela fica parcial.
DECLARE janela_dias INT64 DEFAULT 30;   -- até quando olhar consumo depois do cadastro

WITH fo AS (
  -- Instalações. Conta por device (`id_pseudo_user`); `first_open` não tem identidade.
  SELECT id_pseudo_user, MIN(dt_created_at) AS dt_install
  FROM `bp-datawarehouse.staging.stg_firebase__bp_platform_events`
  WHERE nm_event IN ('first_open', 'first_open_consented')
    AND DATE(dt_created_at) BETWEEN DATE_SUB(d0, INTERVAL 30 DAY) AND d1
  GROUP BY 1
),
ev AS (
  SELECT id_pseudo_user, id_user, dt_created_at
  FROM `bp-datawarehouse.staging.stg_firebase__bp_platform_events`
  WHERE DATE(dt_created_at) BETWEEN DATE_SUB(d0, INTERVAL 30 DAY) AND DATE_ADD(d1, INTERVAL 1 DAY)
    AND id_user IS NOT NULL AND id_user != ''
),
bridge AS (
  SELECT id_pseudo_user, id_user FROM (
    SELECT fo.id_pseudo_user, ev.id_user,
           ROW_NUMBER() OVER (PARTITION BY fo.id_pseudo_user ORDER BY ev.dt_created_at) AS rn
    FROM fo JOIN ev USING (id_pseudo_user)
  ) WHERE rn = 1
),
contas AS (
  SELECT DISTINCT
    du.id_user,
    du.dt_created_at AS dt_cadastro,
    LOWER(TRIM(du.nm_email)) AS email
  FROM fo
  JOIN bridge USING (id_pseudo_user)
  JOIN `bp-datawarehouse.masterdata.dim_user` du ON du.id_user = bridge.id_user
  WHERE DATE(du.dt_created_at) BETWEEN d0 AND d1
    AND du.dt_created_at >= DATETIME_SUB(fo.dt_install, INTERVAL 1 HOUR)   -- regra 2
),
tx AS (
  SELECT LOWER(TRIM(dc.nm_email)) AS email, t.dt_ordered_at
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
),
coorte AS (
  -- Regra 1: sem compra até 1h depois do cadastro.
  SELECT c.*
  FROM contas c
  WHERE NOT EXISTS (
    SELECT 1 FROM tx
    WHERE tx.email = c.email
      AND tx.dt_ordered_at <= DATETIME_ADD(c.dt_cadastro, INTERVAL 1 HOUR)
  )
),
consumo AS (
  -- Interações da coorte dentro da janela, contadas a partir do cadastro de cada um.
  SELECT
    c.id_user,
    c.dt_cadastro,
    umi.nm_playlist,
    umi.nm_media,
    umi.nm_playlist_type,
    umi.vl_total_watch_time_seconds,
    DATETIME_DIFF(umi.dt_created_at, c.dt_cadastro, HOUR) AS h_desde_cadastro
  FROM coorte c
  JOIN `bp-datawarehouse.datamart.obt_user_media_interactions` umi USING (id_user)
  WHERE umi.dt_created_at >= c.dt_cadastro
    AND umi.dt_created_at <= DATETIME_ADD(c.dt_cadastro, INTERVAL janela_dias DAY)
    AND DATE(umi.dt_created_at) BETWEEN d0 AND DATE_ADD(d1, INTERVAL janela_dias DAY)
),
primeiro AS (
  SELECT id_user, MIN(h_desde_cadastro) AS h_1a_interacao
  FROM consumo GROUP BY 1
)

-- ---------- resumo: a coorte ativa? ----------
SELECT
  'resumo' AS secao,
  'Coorte inteira' AS item,
  NULL AS playlist,
  COUNT(*) AS contas,
  COUNTIF(p.h_1a_interacao IS NOT NULL AND p.h_1a_interacao <= 24) AS ativou_24h,
  COUNTIF(p.h_1a_interacao IS NOT NULL AND p.h_1a_interacao <= 168) AS ativou_7d,
  COUNTIF(p.h_1a_interacao IS NOT NULL) AS ativou_na_janela,
  COUNTIF(p.h_1a_interacao IS NULL) AS nunca_ativou,
  ROUND(COUNTIF(p.h_1a_interacao IS NOT NULL) / COUNT(*) * 100, 2) AS pct_ativou,
  NULL AS horas_assistidas
FROM coorte c
LEFT JOIN primeiro p USING (id_user)

UNION ALL

-- ---------- conteudo: o que consumiram ----------
SELECT
  'conteudo' AS secao,
  nm_media AS item,
  nm_playlist AS playlist,
  COUNT(DISTINCT id_user) AS contas,
  NULL, NULL, NULL, NULL,
  ROUND(COUNT(DISTINCT id_user) / (SELECT COUNT(*) FROM coorte) * 100, 2) AS pct_ativou,
  ROUND(SUM(vl_total_watch_time_seconds) / 3600, 1) AS horas_assistidas
FROM consumo
GROUP BY nm_media, nm_playlist

ORDER BY secao, contas DESC
