-- Membros Fundadores Big Picture
-- Quem comprou oferta de "Membro Fundador" / "Founding Member" da linha Big Picture.
-- Uma linha por pessoa (dedup por email). Inclui tier e país/estado para filtro.

WITH

fundadores AS (
  SELECT
    id_gateway_customer,
    STRING_AGG(DISTINCT nm_gateway_product, ' | ') AS produto_big_picture,
    MAX(CASE
      WHEN LOWER(nm_gateway_product) LIKE '%mecenas%' THEN 'Mecenas'
      WHEN LOWER(nm_gateway_product) LIKE '%ouro%'    THEN 'Ouro'
      WHEN LOWER(nm_gateway_product) LIKE '%prata%'   THEN 'Prata'
      WHEN LOWER(nm_gateway_product) LIKE '%bronze%'  THEN 'Bronze'
      ELSE 'Outro/Founding Member' END) AS tier
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND LOWER(nm_gateway_product) LIKE '%big picture%'
    AND (LOWER(nm_gateway_product) LIKE '%membro fundador%'
         OR LOWER(nm_gateway_product) LIKE '%founding member%')
    AND id_gateway_customer IS NOT NULL
  GROUP BY 1
),

acumulado AS (
  SELECT
    id_gateway_customer,
    SUM(vl_payment_gross) AS receita_acumulada,
    COUNT(*)              AS vendas_acumuladas,
    MIN(dt_ordered_at)    AS data_primeira_compra
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
  GROUP BY 1
),

contato AS (
  SELECT
    id_gateway_customer, nm_name, nm_email, cd_cleaned_phone_number, cd_cpf,
    nm_address, nm_address_neighborhood, cd_address_zipcode,
    cd_address_state, nm_address_city, cd_address_country
  FROM `bp-datawarehouse.masterdata.dim_contact`
)

SELECT
  'Fundador Big Picture' AS classificacao,
  f.tier,
  c.nm_name              AS nome,
  c.nm_email             AS email,
  c.cd_cleaned_phone_number AS telefone,
  c.cd_cpf               AS cpf,
  c.nm_address           AS endereco,
  c.nm_address_neighborhood AS bairro,
  c.nm_address_city      AS cidade,
  c.cd_address_state     AS estado,
  c.cd_address_zipcode   AS cep,
  c.cd_address_country   AS pais,
  f.produto_big_picture,
  a.receita_acumulada,
  a.vendas_acumuladas,
  a.data_primeira_compra
FROM fundadores f
JOIN contato c USING (id_gateway_customer)
LEFT JOIN acumulado a USING (id_gateway_customer)
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY c.nm_email
  ORDER BY a.receita_acumulada DESC NULLS LAST, a.data_primeira_compra ASC
) = 1
ORDER BY a.receita_acumulada DESC NULLS LAST
