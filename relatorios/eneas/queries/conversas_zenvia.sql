-- Conversas Zenvia dos compradores ENE via Comercial (humano e Lambda C0113)
-- Match por telefone: tb_ene_perfil → dim_zenvia_contacts → dim_zenvia_approaches
-- ⚠️ Output contém PII (transcrições) — usar só para leitura, nunca commitar resultado.
-- ⚠️ Conversas da Lambda NÃO estão no Zenvia (só ~16% dos compradores Lambda têm match).
--    O log próprio (lambdalabs-gcp.iasmin_analytics.conversation_report_bp) está vazio
--    desde ~jun/2026 e o dataset não permite listagem — pedir acesso ao time da Lambda.
WITH compradores AS (
  SELECT DISTINCT nm_canal, cd_cleaned_phone_number, nm_email
  FROM `bp-staging.dbt_abe.tb_ene_perfil`
  WHERE nm_canal LIKE 'Comercial%'
),

contatos AS (
  SELECT id_prospect, cd_cleaned_phone_number
  FROM `bp-datawarehouse.masterdata.dim_zenvia_contacts`
),

conversas AS (
  SELECT
    cp.nm_canal,
    cp.nm_email,
    a.id_approach,
    a.dt_approach_start,
    a.nm_conversation
  FROM compradores cp
  INNER JOIN contatos ct
    ON cp.cd_cleaned_phone_number = ct.cd_cleaned_phone_number
  INNER JOIN `bp-datawarehouse.masterdata.dim_zenvia_approaches` a
    USING (id_prospect)
  WHERE a.dt_approach_start >= '2026-07-20'
)

SELECT
  nm_canal,
  COUNT(DISTINCT nm_email) AS pessoas_com_conversa,
  COUNT(DISTINCT id_approach) AS conversas,
  COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation),
    r'não consegui|nao consegui|não consigo|nao consigo|não passou|nao passou|recusad|não aceit|nao aceit|tentei'
  )) AS conversas_mencao_dificuldade,
  COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'cart[ãa]o')) AS conversas_mencao_cartao
FROM conversas
GROUP BY 1;
