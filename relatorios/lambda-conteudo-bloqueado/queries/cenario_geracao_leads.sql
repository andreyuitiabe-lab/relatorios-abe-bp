-- Cenário da base CB no momento da entrada na lista
-- Flags + corte exclusivo por prioridade:
--   abordagem humana ativa > outra lista Lambda > comprou ≤7d > deal humano zumbi > limpo
WITH cb AS (
  SELECT LOWER(nm_person_email) email,
         REGEXP_REPLACE(cd_person_cleaned_phone_number, r'[^0-9]','') tel,
         MIN(dt_created_at) dt_entrou
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics`
  WHERE nm_title LIKE 'UPSELL |%'
  GROUP BY 1,2
),
cbp AS (
  SELECT COALESCE(NULLIF(email,''), tel) pessoa, email, tel, dt_entrou FROM cb
),
outros_deals AS (
  SELECT LOWER(d.nm_person_email) email,
         REGEXP_REPLACE(d.cd_person_cleaned_phone_number, r'[^0-9]','') tel,
         d.dt_created_at, d.dt_closed_at,
         IF(d.nm_salesman_email = 'gustavo.koetz@brasilparalelo.com.br'
            OR d.nm_stage = '10. AWSALES LISTA', 'lambda', 'humano') tipo
  FROM `bp-datawarehouse.staging.int_pipedrive_analytics` d
  WHERE d.nm_title NOT LIKE 'UPSELL |%'
),
deals_abertos AS (
  SELECT p.pessoa, d.tipo,
         d.dt_created_at >= p.dt_entrou - INTERVAL 60 DAY AS recente
  FROM cbp p JOIN outros_deals d ON p.email = d.email AND p.email != ''
  WHERE d.dt_created_at < p.dt_entrou
    AND COALESCE(d.dt_closed_at, DATETIME '9999-01-01') >= p.dt_entrou
  UNION DISTINCT
  SELECT p.pessoa, d.tipo,
         d.dt_created_at >= p.dt_entrou - INTERVAL 60 DAY
  FROM cbp p JOIN outros_deals d ON p.tel = d.tel AND p.tel != ''
  WHERE d.dt_created_at < p.dt_entrou
    AND COALESCE(d.dt_closed_at, DATETIME '9999-01-01') >= p.dt_entrou
),
zenvia_ativa AS (
  SELECT DISTINCT p.pessoa
  FROM cbp p JOIN `bp-datawarehouse.datamart.dtm_sales_by_zenvia` z
    ON z.cd_cleaned_phone_number = p.tel AND p.tel != ''
  WHERE z.dt_approach_start < p.dt_entrou
    AND z.dt_approach_start >= p.dt_entrou - INTERVAL 60 DAY
    AND COALESCE(z.dt_approach_end, CURRENT_DATETIME()) >= p.dt_entrou - INTERVAL 7 DAY
),
tx AS (
  SELECT t.dt_ordered_at, LOWER(c.nm_email) email,
         REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]','') tel
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved' AND t.bl_is_renovation = FALSE
    AND t.dt_ordered_at >= '2026-06-01'
),
compra_7d AS (
  SELECT DISTINCT p.pessoa FROM cbp p JOIN tx ON p.email = tx.email AND p.email != ''
  WHERE tx.dt_ordered_at >= p.dt_entrou - INTERVAL 7 DAY AND tx.dt_ordered_at < p.dt_entrou
  UNION DISTINCT
  SELECT DISTINCT p.pessoa FROM cbp p JOIN tx ON p.tel = tx.tel AND p.tel != ''
  WHERE tx.dt_ordered_at >= p.dt_entrou - INTERVAL 7 DAY AND tx.dt_ordered_at < p.dt_entrou
),
flags AS (
  SELECT
    p.pessoa,
    p.pessoa IN (SELECT pessoa FROM deals_abertos WHERE tipo = 'lambda') AS f_lambda,
    p.pessoa IN (SELECT pessoa FROM deals_abertos WHERE tipo = 'humano' AND recente) AS f_humano_60d,
    p.pessoa IN (SELECT pessoa FROM deals_abertos WHERE tipo = 'humano' AND NOT recente) AS f_humano_antigo,
    p.pessoa IN (SELECT pessoa FROM zenvia_ativa) AS f_zenvia,
    p.pessoa IN (SELECT pessoa FROM compra_7d) AS f_compra7
  FROM cbp p
)
SELECT
  -- flags (com sobreposição)
  COUNT(*) base,
  COUNTIF(f_lambda) outra_lista_lambda,
  COUNTIF(f_humano_60d OR f_zenvia) abordagem_humana_ativa,
  COUNTIF(f_humano_antigo) deal_humano_zumbi,
  COUNTIF(f_compra7) comprou_7d_antes,
  -- corte exclusivo (prioridade)
  COUNTIF(f_humano_60d OR f_zenvia) ex_abordagem_humana,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND f_lambda) ex_outra_lista_lambda,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND NOT f_lambda AND f_compra7) ex_comprou_7d,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND NOT f_lambda AND NOT f_compra7 AND f_humano_antigo) ex_deal_zumbi,
  COUNTIF(NOT (f_humano_60d OR f_zenvia) AND NOT f_lambda AND NOT f_compra7 AND NOT f_humano_antigo) ex_limpo
FROM flags
