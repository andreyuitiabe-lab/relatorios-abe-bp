-- High-ticket: os dois testes de robustez da tese "o motor trocou de canal".
-- Ambos levantados na revisão independente de 17/09 — um sustenta a tese, o outro a limita.
-- Publicar os dois: omitir o segundo deixaria a moldura sem contraprova.
--
-- TESTE 1 (sustenta) — a migração para mídia é artefato da regra de universo?
--   Cada campanha existe em dois universos na tb_ht_compradores ('rastro' e 'janela').
--   Se o salto de share de mídia aparecesse só na regra 'janela' (usada nos Black November)
--   e não na 'rastro', seria efeito da regra. Medindo os dois com a MESMA regra:
--   sob 'janela' o share vai de 19,1% (BNO24) para 49,2% (BP10) — o salto sobrevive.
--
-- TESTE 2 (limita) — o BNO24 é linha de base ou outlier?
--   Mix de canal de TODA venda nova da casa, mês a mês, com a mesma regra de canal da query 01.
--   Resultado: a casa migrou para mídia num DEGRAU em meados de 2024 (ago-set/2024 saltam para
--   48-64%) e opera em ~45-55% desde então. Nov/2024 (BNO24) tem 19,8% de mídia — o MENOR mês
--   de todo 2024. Ou seja: o BNO24 não é o "antes" de uma deriva de três anos, é uma mobilização
--   excepcional do Comercial contra um patamar que já era majoritariamente mídia.
--   Consequência: a pergunta acionável deixa de ser "por que a mídia cresceu" e passa a ser
--   "por que o Comercial não foi mobilizado de novo como em nov/2024".

-- ── TESTE 1 ────────────────────────────────────────────────────────────────
SELECT
  'teste1_universo' AS nm_teste,
  sigla,
  nm_universo,
  COUNT(*)                                                      AS qt_compradores,
  ROUND(100 * COUNTIF(nm_canal = 'midia_paga') / COUNT(*), 1)   AS pct_midia,
  ROUND(100 * COUNTIF(nm_canal = 'comercial')  / COUNT(*), 1)   AS pct_comercial,
  CAST(NULL AS FLOAT64)                                         AS pct_crm,
  CAST(NULL AS FLOAT64)                                         AS pct_sem_rastro
FROM `bp-staging.dbt_abe.tb_ht_compradores`
WHERE nm_universo IN ('rastro', 'janela')
GROUP BY 1, 2, 3

UNION ALL

-- ── TESTE 2 ────────────────────────────────────────────────────────────────
SELECT
  'teste2_serie_casa' AS nm_teste,
  FORMAT_DATE('%Y-%m', DATE(dt_ordered_at))                     AS sigla,
  'casa'                                                        AS nm_universo,
  COUNT(*)                                                      AS qt_compradores,
  ROUND(100 * COUNTIF(canal = 'midia_paga') / COUNT(*), 1)      AS pct_midia,
  ROUND(100 * COUNTIF(canal = 'comercial')  / COUNT(*), 1)      AS pct_comercial,
  ROUND(100 * COUNTIF(canal = 'crm')        / COUNT(*), 1)      AS pct_crm,
  ROUND(100 * COUNTIF(canal = 'sem_rastro') / COUNT(*), 1)      AS pct_sem_rastro
FROM (
  SELECT
    dt_ordered_at,
    CASE
      WHEN bl_is_commercial_channel
        OR STARTS_WITH(LOWER(COALESCE(nm_pptc_tracking_name, '')), 'comercial_') THEN 'comercial'
      WHEN REGEXP_CONTAINS(LOWER(nm_pptc_tracking_name), r'\[fb\+ig\]|\[pmax\]|\[kw\]|\[yt\]|\[publi\]|\[tiktok\]|\[x\]|\[display\]') THEN 'midia_paga'
      WHEN REGEXP_CONTAINS(LOWER(nm_pptc_tracking_name), r'\[e-?mail\]|\[whatsapp\]|\[in-? ?app\]|\[app-? ?push\]|\[web-? ?push\]|\[sms\]|\[custom\]') THEN 'crm'
      WHEN REGEXP_CONTAINS(LOWER(nm_pptc_tracking_name), r'\[canal-yt\]|\[redes sociais\]|\[portal\]|\[programas\]|\[live\]|\[plataforma\]|\[noticias\]|\[assine\]|\[influs\]|\[parceiros\]') THEN 'organico_portal'
      WHEN nm_pptc_tracking_name IS NOT NULL THEN 'outros'
      WHEN REGEXP_CONTAINS(LOWER(nm_pptc_utm_medium), r'facebook_ads|meta_ads|pmax|youtube_ads|google_ads|paid_publi|x_ads|^ads$|tiktok') THEN 'midia_paga'
      WHEN REGEXP_CONTAINS(LOWER(nm_pptc_utm_medium), r'whatsapp|email|push|in_app|sms|architect') THEN 'crm'
      WHEN REGEXP_CONTAINS(LOWER(nm_pptc_utm_medium), r'organic|live_youtube|programas|instaportal|home|descricao') THEN 'organico_portal'
      WHEN nm_pptc_utm_medium IS NULL THEN 'sem_rastro'
      ELSE 'outros'
    END AS canal
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_is_renovation = FALSE
    AND DATE(dt_ordered_at) >= '2023-01-01'
)
GROUP BY 1, 2, 3
ORDER BY nm_teste, sigla, nm_universo;
