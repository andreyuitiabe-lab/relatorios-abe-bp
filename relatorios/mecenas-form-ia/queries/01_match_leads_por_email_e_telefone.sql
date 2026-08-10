-- Casa leads de um formulário externo (planilha) com contas do gateway, por e-mail E telefone.
-- ⚠️ Os literais de e-mail/telefone foram trocados por parâmetros: este repo é PÚBLICO.
--    Passar @emails e @fones como ARRAY<STRING> (telefone em E.164 sem '+', ex: 5522998749558).
--
-- ⚠️ GOTCHA que motivou os filtros de sujeira: um lead informou "(11) 99999-9999", que casa com
--    1.234 contas na base. Sem os dois filtros abaixo o match inflava de 90 para 1.324 contas:
--      1. regex de dígito repetido 6+ vezes  → número fake
--      2. telefone com >= 10 e-mails distintos → linha compartilhada / lixo
--    São as mesmas regras que o identity graph aplica (ver wiki dbt-identity-graph.md).
--
-- Match de telefone é tolerante ao nono dígito: compara DDD + os 8 últimos dígitos.


CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_form_ia_leads` AS
WITH lead_email AS (SELECT e AS email FROM UNNEST(@emails) e),

lead_fone_raw AS (SELECT f FROM UNNEST(@fones) f),

-- mesmas regras de sujeira do identity graph: sequência repetida = número fake
lead_fone AS (
  SELECT CONCAT(SUBSTR(f,3,2), RIGHT(f,8)) AS fone_key, f AS fone
  FROM lead_fone_raw
  WHERE NOT REGEXP_CONTAINS(f, r'(0{6,}|1{6,}|2{6,}|3{6,}|4{6,}|5{6,}|6{6,}|7{6,}|8{6,}|9{6,})')
    AND LENGTH(f) BETWEEN 12 AND 13
),

fone_bq AS (
  SELECT id_gateway_customer, LOWER(nm_email) AS email_bq, cd_cleaned_phone_number AS fone_bq,
         CONCAT(SUBSTR(cd_cleaned_phone_number,3,2), RIGHT(cd_cleaned_phone_number,8)) AS fone_key
  FROM `bp-datawarehouse.masterdata.dim_contact`
  WHERE LENGTH(cd_cleaned_phone_number) BETWEEN 12 AND 13
),

-- e telefone compartilhado por muita gente também sai (>=10 e-mails distintos)
fone_sujo AS (
  SELECT fone_key FROM fone_bq
  GROUP BY 1 HAVING COUNT(DISTINCT email_bq) >= 10
),

por_email AS (
  SELECT c.id_gateway_customer, LOWER(c.nm_email) AS email_bq, c.cd_cleaned_phone_number AS fone_bq,
         le.email AS match_email, CAST(NULL AS STRING) AS match_fone
  FROM `bp-datawarehouse.masterdata.dim_contact` c
  JOIN lead_email le ON le.email = LOWER(c.nm_email)
),

por_fone AS (
  SELECT b.id_gateway_customer, b.email_bq, b.fone_bq,
         CAST(NULL AS STRING) AS match_email, lf.fone AS match_fone
  FROM fone_bq b
  JOIN lead_fone lf USING (fone_key)
  WHERE b.fone_key NOT IN (SELECT fone_key FROM fone_sujo)
),

uniao AS (
  SELECT id_gateway_customer, ANY_VALUE(email_bq) AS email_bq, ANY_VALUE(fone_bq) AS fone_bq,
         MAX(match_email) AS match_email, MAX(match_fone) AS match_fone
  FROM (SELECT * FROM por_email UNION ALL SELECT * FROM por_fone)
  GROUP BY id_gateway_customer
)

SELECT
  COALESCE(m.id_person, CONCAT('gw::', u.id_gateway_customer)) AS id_person,
  u.*
FROM uniao u
LEFT JOIN `bp-staging.dbt_abe.tb_mecenas_person_map` m USING (id_gateway_customer)
