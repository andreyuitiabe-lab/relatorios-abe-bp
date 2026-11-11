-- Coorte do Apoiador R$ 1,90/mês e o que cada pessoa fez depois.
-- Só CTEs: o refresh.py concatena este arquivo com o SELECT final de cada queries/<nome>.sql.
--
-- Coorte: 1ª compra (aprovada ou reembolsada, sem renovação) de oferta `supporter` "12x de R$1,90"
-- desde 23/09/2026, uma linha por e-mail. Reembolsadas entram porque o gateway reembolsa o R$ 1,90
-- quando a pessoa troca de plano.
-- Perfil medido 10 min antes da compra, para não contar a assinatura recém-criada.
-- Origem por utm_medium do PPTC (o publisher tem rastreio quebrado nesse checkout; ver bq-regras).
WITH tx AS (
  SELECT LOWER(c.nm_email) AS e, t.dt_ordered_at, t.nm_status, t.nm_gateway_offer, t.nm_gateway_plan, t.nm_plan_label,
    t.bl_is_commercial_channel AS com, t.bl_is_renovation AS renov, t.vl_payment_gross AS v,
    t.nm_pptc_utm_content, LOWER(t.nm_pptc_utm_medium) AS med, t.nm_pptc_checkout_name AS ck,
    UPPER(t.nm_pptc_tracking_name) LIKE '%C0113%' AS lambda, c.cd_cleaned_phone_number AS fone,
    (t.nm_gateway_plan = 'supporter' AND REGEXP_CONTAINS(t.nm_gateway_offer, r'12x de R\$1,90')) AS is190
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE c.nm_email IS NOT NULL
),
origem AS (
  SELECT e, dt_ordered_at AS t0, nm_status AS st0, ck AS ck0, fone AS fone0,
    CASE WHEN com THEN 'Comercial (vendedor)'
         WHEN nm_pptc_utm_content IN ('apuracao_eleicoes_04out', 'vvs_paraguai') OR med IN ('programas', 'live_youtube', 'lpvendas') THEN 'Live/YouTube orgânico'
         WHEN med IN ('facebook_ads', 'meta_ads') THEN 'Meta Ads'
         WHEN med IN ('pmax_ads', 'kw_google_ads', 'google_ads', 'youtube_ads', 'bing', 'twitter_ads') THEN 'Google/YouTube/X Ads'
         WHEN REGEXP_CONTAINS(med, r'whatsapp|email|in_app|push|sms') THEN 'CRM (WhatsApp/e-mail/app)'
         WHEN med IN ('organic_social', 'paid_publi') THEN 'Social orgânico/influ'
         ELSE 'Sem rastreio/outros' END AS entrada
  FROM tx
  WHERE is190 AND nm_status IN ('approved', 'refunded') AND NOT renov AND dt_ordered_at >= '2026-09-23'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY e ORDER BY dt_ordered_at) = 1
),
subs AS (
  SELECT LOWER(c.nm_email) AS e, s.dt_started_at, s.dt_expires_in
  FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE s.nm_type = 'paid'
),
primeira AS (
  SELECT e, MIN(dt_ordered_at) AS dt FROM tx WHERE nm_status = 'approved' GROUP BY 1
),
perfil AS (
  SELECT o.e,
    CASE WHEN LOGICAL_OR(s.dt_started_at < DATETIME_SUB(o.t0, INTERVAL 10 MINUTE) AND s.dt_expires_in >= o.t0) THEN 'Membro ativo'
         WHEN LOGICAL_OR(s.dt_started_at < DATETIME_SUB(o.t0, INTERVAL 10 MINUTE)) THEN 'Ex-membro'
         WHEN MIN(pr.dt) < DATETIME_SUB(o.t0, INTERVAL 10 MINUTE) THEN 'Já comprou, sem assinatura'
         ELSE 'Novo na base' END AS seg
  FROM origem o LEFT JOIN subs s USING (e) LEFT JOIN primeira pr USING (e)
  GROUP BY o.e, o.t0
),
-- Compras aprovadas depois do R$ 1,90 (exceto outro R$ 1,90 e renovação).
-- one_click = digital em até 60 min (oferta pós-compra do checkout); o resto é "upsell posterior".
depois AS (
  SELECT o.e, t.dt_ordered_at, t.com, t.lambda, t.v,
    DATETIME_DIFF(t.dt_ordered_at, o.t0, MINUTE) AS min_apos,
    DATETIME_DIFF(t.dt_ordered_at, o.t0, MINUTE) <= 60 AND NOT t.com AS one_click,
    CASE
      WHEN REGEXP_CONTAINS(LOWER(t.nm_plan_label), r'vital|black') OR t.nm_gateway_plan LIKE 'mecenas%' THEN 'Black/Vitalício/Mecenas'
      WHEN t.nm_plan_label LIKE 'Extensao%' THEN 'Extensão 2º ano'
      WHEN t.nm_gateway_plan IN ('best', 'premium') OR REGEXP_CONTAINS(t.nm_gateway_plan, r'^(bp-)?premium-') THEN 'Premium'
      WHEN t.nm_gateway_plan = 'good' OR REGEXP_CONTAINS(LOWER(t.nm_plan_label), r'essencial|básico') THEN 'Essencial'
      WHEN t.nm_gateway_plan = 'supporter' OR REGEXP_CONTAINS(LOWER(t.nm_plan_label), r'apoiador|econ') THEN 'Outro Apoiador'
      ELSE 'Outros (livro, CDL, certificação…)' END AS tipo
  FROM origem o JOIN tx t ON t.e = o.e
  WHERE t.nm_status = 'approved' AND NOT t.renov AND NOT t.is190 AND t.dt_ordered_at > o.t0
),
-- Consumo nos 7 dias após a compra; sessão limitada a 4h para não deixar TV ligada distorcer.
views AS (
  SELECT o.e, SUM(LEAST(v.vl_watch_time_seconds, 4 * 3600)) / 3600 AS h7
  FROM origem o JOIN `bp-datawarehouse.datamart.obt_kafka__view_sessions` v
    ON LOWER(v.nm_email) = o.e AND v.dt_created_at BETWEEN o.t0 AND DATETIME_ADD(o.t0, INTERVAL 7 DAY)
  WHERE v.dt_created_at >= '2026-09-23'
  GROUP BY 1
),
up AS (
  SELECT e,
    LOGICAL_OR(one_click) AS up1h,
    LOGICAL_OR(NOT one_click AND tipo != 'Outro Apoiador') AS up_dep,
    LOGICAL_OR(com AND lambda AND tipo != 'Outro Apoiador') AS up_lambda,
    LOGICAL_OR(com AND NOT lambda AND tipo != 'Outro Apoiador') AS up_humano
  FROM depois GROUP BY 1
),
pessoa AS (
  SELECT o.e, o.entrada, p.seg, o.t0, o.st0, o.ck0,
    o.t0 <= DATETIME_SUB(CURRENT_DATETIME('America/Sao_Paulo'), INTERVAL 8 DAY) AS tem7d,
    COALESCE(u.up1h, FALSE) AS up1h, COALESCE(u.up_dep, FALSE) AS up_dep,
    COALESCE(u.up_lambda, FALSE) AS up_lambda, COALESCE(u.up_humano, FALSE) AS up_humano,
    COALESCE(v.h7, 0) AS h7
  FROM origem o JOIN perfil p USING (e) LEFT JOIN up u USING (e) LEFT JOIN views v USING (e)
)
