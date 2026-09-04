-- Falas do cliente e do vendedor nas conversas do CBR, com desfecho (comprou / não comprou)
--
-- ⚠️ O resultado contém PII (nome e às vezes telefone dentro do texto da conversa).
--    NUNCA exportar para o repo público nem para o data.json. Uso local apenas.
--
-- O `nm_conversation` é um log corrido com os prefixos `seller: ` e `prospect: `.
-- RE2 não tem lookahead, então a separação de turnos é feita marcando cada prefixo
-- com `~~` (via REPLACE, mais previsível que backreference) e filtrando os segmentos.

WITH conv AS (
  SELECT
    a.id_prospect, a.id_approach, a.dt_approach_start,
    a.qt_seller_interactions, a.qt_prospect_interactions, a.nm_closing_reason,
    REGEXP_REPLACE(a.nm_conversation, r'\s+', ' ') AS c
  FROM `bp-datawarehouse.masterdata.dim_zenvia_approaches` a
  WHERE DATE(a.dt_approach_start) >= '2026-09-01'
    AND REGEXP_CONTAINS(LOWER(COALESCE(a.nm_conversation, '')), r'[uú]ltima cruzada|cole[cç][aã]o brasil')
    AND a.qt_prospect_interactions > 0
),

turnos AS (
  SELECT *,
    SPLIT(REPLACE(REPLACE(c, 'seller: ', '~~seller: '), 'prospect: ', '~~prospect: '), '~~') AS partes
  FROM conv
),

falas AS (
  SELECT * EXCEPT (partes),
    ARRAY_TO_STRING(ARRAY(
      SELECT TRIM(REPLACE(x, 'prospect: ', ''))
      FROM UNNEST(partes) AS x WHERE STARTS_WITH(x, 'prospect: ')
    ), ' || ') AS fala_cliente,
    ARRAY_TO_STRING(ARRAY(
      SELECT TRIM(REPLACE(x, 'seller: ', ''))
      FROM UNNEST(partes) AS x WHERE STARTS_WITH(x, 'seller: ')
    ), ' || ') AS fala_vendedor
  FROM turnos
),

ab AS (
  SELECT id_prospect, bucket, etapa_atual, bl_comprou_apos_abordagem, vl_uc
  FROM `bp-staging.dbt_abe.tb_uc_abordagens`
)

SELECT
  f.id_prospect, f.dt_approach_start,
  f.qt_seller_interactions, f.qt_prospect_interactions, f.nm_closing_reason,
  ab.bucket, ab.etapa_atual,
  COALESCE(ab.bl_comprou_apos_abordagem, FALSE) AS bl_comprou,
  ab.vl_uc,
  f.fala_cliente,
  f.fala_vendedor
FROM falas f
LEFT JOIN ab USING (id_prospect)
WHERE LENGTH(f.fala_cliente) > 0
