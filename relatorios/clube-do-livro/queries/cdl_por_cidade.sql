-- Vendas Clube do Livro (clube-do-livro) por estado e cidade.
-- Cidade: geocodificação por CEP (preferida); fallback p/ nm_address_city de dim_contact.
-- Texto normalizado (sem acento, maiúsculo) para não fragmentar a contagem.
WITH cdl AS (
  SELECT id_gateway_customer
  FROM masterdata.fct_transactions
  WHERE nm_gateway_plan = 'clube-do-livro'
    AND nm_status = 'approved'
    AND bl_is_renovation = FALSE
),
contato AS (
  SELECT id_gateway_customer, cd_address_state, cd_address_zipcode, nm_address_city
  FROM masterdata.dim_contact
),
geo AS (
  SELECT cd_address_zipcode, nm_address_city, nm_address_state
  FROM masterdata.dim_geolocation_of_brazil_addresses
  QUALIFY ROW_NUMBER() OVER (PARTITION BY cd_address_zipcode ORDER BY nm_address_city) = 1
)
SELECT
  COALESCE(g.nm_address_state, c.cd_address_state, '(sem UF)') AS uf,
  INITCAP(COALESCE(
    UPPER(REGEXP_REPLACE(NORMALIZE(g.nm_address_city, NFD), r'\pM', '')),
    UPPER(REGEXP_REPLACE(NORMALIZE(NULLIF(c.nm_address_city, ''), NFD), r'\pM', '')),
    '(NAO IDENTIFICADA)'
  )) AS cidade,
  COUNT(*) AS vendas
FROM cdl
LEFT JOIN contato c USING (id_gateway_customer)
LEFT JOIN geo g ON g.cd_address_zipcode = c.cd_address_zipcode
GROUP BY 1, 2
ORDER BY vendas DESC
