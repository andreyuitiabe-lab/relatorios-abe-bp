-- RODADA 9b (16/09/2026) — case 11 de Setembro NA PLATAFORMA: mídia 'As Consequências do 11 de Setembro após 25 Anos'
-- (playlist Temas em alta). ⚠️ A 'estreia' de 07/09 era 1 usuário (QA); a audiência real começa em 11/09, dia seguinte à live no YouTube (mesmo gotcha do Technocracia). Máquina da query 22: membro leve/médio (1–8 dias ativos/30d), sem compra 60d,
-- controle = top-8 playlists nos MESMOS dias. Exposição 11/09–12/09; compras até 15/09 → D+1..D+3 completo. D+7 fecha em 19/09, D+14 em 26/09.
-- ⚠️ MDE declarado antes de rodar: com ~1.000 pessoa-dias e taxa base ~0,4% em D+3, só detecta lift ≥ ~2,5×.
WITH sessoes AS (
  SELECT LOWER(nm_email) AS email, DATE(dt_created_at) AS dia, nm_playlist, nm_media, nm_plan
  FROM datamart.obt_kafka__view_sessions
  WHERE vl_watch_time_seconds >= 300 AND nm_email IS NOT NULL
    AND DATE(dt_created_at) BETWEEN '2026-08-01' AND '2026-09-12'
),
janela AS (SELECT * FROM sessoes WHERE dia BETWEEN '2026-09-11' AND '2026-09-12'),
top_playlists AS (
  SELECT nm_playlist FROM janela WHERE nm_playlist IS NOT NULL AND nm_playlist != 'Temas em alta'
  GROUP BY 1 ORDER BY COUNT(DISTINCT email) DESC LIMIT 8
),
pessoa_dia AS (
  SELECT email, dia,
    MAX(IF(REGEXP_CONTAINS(LOWER(nm_media), r'11 de setembro'), 1, 0)) AS viu_11set,  -- igualdade literal falhava (unicode do título)
    MAX(IF(nm_playlist IN (SELECT nm_playlist FROM top_playlists), 1, 0)) AS viu_top,
    MAX(IF(nm_plan IN ('free', 'fake-free'), 1, 0)) AS eh_freemium
  FROM janela GROUP BY 1, 2
),
engaj AS (
  SELECT pd.email, pd.dia, COUNT(DISTINCT s.dia) AS dias_ativos_30d
  FROM pessoa_dia pd LEFT JOIN sessoes s ON s.email = pd.email
   AND s.dia BETWEEN DATE_SUB(pd.dia, INTERVAL 30 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)
  GROUP BY 1, 2
),
compras AS (
  SELECT LOWER(c.nm_email) AS email, DATE(t.dt_ordered_at) AS dia_compra, t.vl_payment_gross AS vl
  FROM masterdata.fct_transactions t JOIN masterdata.dim_contact c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND DATE(t.dt_ordered_at) BETWEEN '2026-07-01' AND '2026-09-15'
),
base AS (
  SELECT pd.email, pd.dia, pd.viu_11set, pd.viu_top, pd.eh_freemium,
    CASE WHEN e.dias_ativos_30d <= 2 THEN '1_leve' WHEN e.dias_ativos_30d <= 8 THEN '2_medio' ELSE '3_heavy' END AS faixa,
    (SELECT COUNT(*) FROM compras c WHERE c.email = pd.email AND c.dia_compra BETWEEN DATE_SUB(pd.dia, INTERVAL 60 DAY) AND DATE_SUB(pd.dia, INTERVAL 1 DAY)) AS compra_60d,
    (SELECT COUNT(*) FROM compras c WHERE c.email = pd.email AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 3 DAY)) AS pos6,
    (SELECT SUM(c.vl) FROM compras c WHERE c.email = pd.email AND c.dia_compra BETWEEN DATE_ADD(pd.dia, INTERVAL 1 DAY) AND DATE_ADD(pd.dia, INTERVAL 3 DAY)) AS rec6
  FROM pessoa_dia pd JOIN engaj e USING (email, dia)
  WHERE e.dias_ativos_30d >= 1
)
SELECT IF(eh_freemium = 1, 'freemium', 'membro') AS status,
       IF(faixa = '3_heavy', 'heavy', 'leve_medio') AS faixa,
       CASE WHEN viu_11set = 1 THEN '11set' WHEN viu_top = 1 THEN 'CONTROLE_top8' ELSE 'outro' END AS grupo,
       dia, COUNT(*) AS pessoa_dias, COUNTIF(pos6 > 0) AS com_compra_d3, ROUND(SUM(COALESCE(rec6, 0)), 2) AS receita_d3
FROM base WHERE compra_60d = 0
GROUP BY 1, 2, 3, 4 ORDER BY 1, 2, 3, 4
