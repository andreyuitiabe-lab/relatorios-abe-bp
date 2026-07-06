WITH cdl AS (
  SELECT id_transaction, id_gateway_customer
  FROM masterdata.fct_transactions
  WHERE nm_gateway_plan = 'clube-do-livro'
    AND nm_status = 'approved'
    AND bl_is_renovation = FALSE
),
contato AS (
  SELECT id_gateway_customer, cd_address_state, cd_address_zipcode
  FROM masterdata.dim_contact
)
SELECT
  COALESCE(c.cd_address_state, '(sem UF)') AS uf,
  COUNT(*) AS vendas,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM cdl
LEFT JOIN contato c USING (id_gateway_customer)
GROUP BY 1
ORDER BY vendas DESC
