-- Mapa conta do gateway -> pessoa real. Apoio para qualquer query que precise agregar
-- por pessoa em vez de por conta. Recriar junto com a base de qualificação.
CREATE OR REPLACE TABLE `bp-staging.dbt_abe.tb_mecenas_person_map` AS
WITH ident AS (
  SELECT nm_identifier, nm_identifier_type, id_person
  FROM `bp-datawarehouse.masterdata.dim_person_identity`
)
SELECT
  c.id_gateway_customer,
  LOWER(c.nm_email) AS email,
  c.cd_address_state AS uf,
  COALESCE(pe.id_person, pp.id_person, pc.id_person,
           CONCAT('email::', LOWER(c.nm_email))) AS id_person
FROM `bp-datawarehouse.masterdata.dim_contact` c
LEFT JOIN ident pe ON pe.nm_identifier_type='email' AND pe.nm_identifier = LOWER(c.nm_email)
LEFT JOIN ident pp ON pp.nm_identifier_type='phone' AND pp.nm_identifier = c.cd_cleaned_phone_number
LEFT JOIN ident pc ON pc.nm_identifier_type='cpf'   AND pc.nm_identifier = c.cd_cpf
WHERE c.nm_email IS NOT NULL
