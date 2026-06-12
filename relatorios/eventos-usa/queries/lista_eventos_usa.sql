-- Lista única para eventos presenciais nos EUA
-- Uma linha por pessoa (dedup por email), com coluna `classificacao`.
-- Big Picture é tratado em lista separada (fora desta query).
-- Prioridade quando a pessoa cai em mais de um grupo: Membro ativo > Ex-membro.
-- (Leads fora desta lista por enquanto.)

WITH

-- Quem tem acesso ativo hoje: assinatura recorrente ativa OU vitalício
membros_ativos AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_status IN ('active', 'wo renewal')
    AND nm_type = 'paid'
    AND dt_started_at <= CURRENT_DATETIME()
    AND dt_expires_in >= CURRENT_DATETIME()
    AND id_gateway_customer IS NOT NULL
  UNION DISTINCT
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.fct_transactions`
  WHERE nm_status = 'approved'
    AND bl_lifetime_offer = TRUE
    AND id_gateway_customer IS NOT NULL
),

-- Qualquer pessoa que já teve assinatura paga (para derivar ex-membros)
todos_assinantes AS (
  SELECT DISTINCT id_gateway_customer
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_type = 'paid'
    AND id_gateway_customer IS NOT NULL
),

-- Receita / nº de compras / primeira compra por cliente
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

-- Cadastro de contato (nome, email, telefone, endereço)
contato AS (
  SELECT
    id_gateway_customer,
    nm_name,
    nm_email,
    cd_cleaned_phone_number,
    cd_cpf,
    nm_address,
    nm_address_neighborhood,
    cd_address_zipcode,
    cd_address_state,
    nm_address_city,
    cd_address_country
  FROM `bp-datawarehouse.masterdata.dim_contact`
),

-- Membros ativos residentes nos EUA (Florida x outros estados)
membros_eua AS (
  SELECT
    1 AS prioridade,
    CASE WHEN c.cd_address_state = 'FL'
      THEN 'Membro ativo - Florida'
      ELSE 'Membro ativo - Outros estados EUA' END AS classificacao,
    c.nm_name AS nome, c.nm_email AS email, c.cd_cleaned_phone_number AS telefone, c.cd_cpf AS cpf,
    c.nm_address, c.nm_address_neighborhood AS bairro, c.nm_address_city AS cidade,
    c.cd_address_state AS estado, c.cd_address_zipcode AS cep, c.cd_address_country AS pais,
    a.receita_acumulada, a.vendas_acumuladas, a.data_primeira_compra
  FROM contato c
  JOIN membros_ativos m USING (id_gateway_customer)
  LEFT JOIN acumulado a USING (id_gateway_customer)
  WHERE c.cd_address_country = 'US'
),

-- Ex-membros (assinou no passado, sem acesso ativo hoje) residentes nos EUA
ex_membros_eua AS (
  SELECT
    2 AS prioridade,
    'Ex-membro' AS classificacao,
    c.nm_name, c.nm_email, c.cd_cleaned_phone_number, c.cd_cpf,
    c.nm_address, c.nm_address_neighborhood, c.nm_address_city,
    c.cd_address_state, c.cd_address_zipcode, c.cd_address_country,
    a.receita_acumulada, a.vendas_acumuladas, a.data_primeira_compra
  FROM contato c
  JOIN todos_assinantes t USING (id_gateway_customer)
  LEFT JOIN membros_ativos m USING (id_gateway_customer)
  LEFT JOIN acumulado a USING (id_gateway_customer)
  WHERE c.cd_address_country = 'US'
    AND m.id_gateway_customer IS NULL
),

uniao AS (
  SELECT * FROM membros_eua
  UNION ALL SELECT * FROM ex_membros_eua
)

SELECT
  classificacao, nome, email, telefone, cpf,
  nm_address AS endereco, bairro, cidade, estado, cep, pais,
  receita_acumulada, vendas_acumuladas, data_primeira_compra
FROM uniao
-- 1 linha por pessoa: mantém a classificação de maior prioridade
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY email
  ORDER BY prioridade ASC, receita_acumulada DESC NULLS LAST, data_primeira_compra ASC
) = 1
ORDER BY prioridade, receita_acumulada DESC NULLS LAST
