-- Mensagens na Zenvia dos compradores de vitalício da BNO26 em qualquer conversa (inclusive aberta antes
-- da janela), casando a pessoa por todos os e-mails E telefones do identity graph. Complementa
-- conversas_zenvia.sql: quem não iniciou conversa nos 30 dias antes pode estar numa conversa antiga.
-- Saída sem PII (só contagens e datas por transação). Parâmetros: {ini_bno26} {fim_bno26}

WITH vit AS (
  SELECT t.id_transaction, t.dt_ordered_at, t.nm_salesman, LOWER(TRIM(c.nm_email)) nm_email, c.cd_cleaned_phone_number phone
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status='approved' AND NOT t.bl_is_renovation AND t.bl_lifetime_offer
    AND DATE(t.dt_ordered_at) BETWEEN '{ini_bno26}' AND '{fim_bno26}'
    AND (t.nm_gateway_plan IN ('good','better','best','black') OR LOWER(t.nm_gateway_product) LIKE '%vital%')
    AND NOT REGEXP_CONTAINS(t.nm_gateway_plan, r'^(livro-odisseia|odisseia-|clube-do-livro|black-clube-do-livro|ebooks-|analises-clube-livro|educacao-literaria|colecao-brasil-a-ultima-cruzada|teller$)')
    AND NOT LOWER(t.nm_gateway_product) LIKE '%membro fundador%'
),
ids AS (  -- todos os e-mails e telefones da pessoa
  SELECT DISTINCT v.id_transaction, d2.nm_identifier_type tp, d2.nm_identifier idf
  FROM vit v JOIN `bp-datawarehouse.masterdata.dim_person_identity` d1 ON d1.nm_identifier_type='email' AND d1.nm_identifier=v.nm_email
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` d2 ON d2.id_person=d1.id_person AND d2.nm_identifier_type IN ('email','phone')
  UNION DISTINCT SELECT id_transaction,'email',nm_email FROM vit WHERE nm_email IS NOT NULL
  UNION DISTINCT SELECT id_transaction,'phone',REGEXP_REPLACE(phone,r'\D','') FROM vit WHERE phone IS NOT NULL
),
prosp AS (
  SELECT DISTINCT i.id_transaction, zc.id_prospect, i.tp
  FROM ids i JOIN `bp-datawarehouse.masterdata.dim_zenvia_contacts` zc
    ON (i.tp='email' AND LOWER(TRIM(zc.nm_contact_email))=i.idf)
    OR (i.tp='phone' AND REGEXP_REPLACE(zc.cd_cleaned_phone_number,r'\D','')=i.idf)
),
inter AS (
  SELECT p.id_transaction,
    LOGICAL_OR(p.tp='email') via_email, LOGICAL_OR(p.tp='phone') via_phone,
    COUNTIF(z.dt_created_interaction_at BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 30 DAY) AND v.dt_ordered_at) msgs_30d,
    COUNTIF(z.dt_created_interaction_at BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 30 DAY) AND v.dt_ordered_at AND z.bl_seller_interaction=1) msgs_vend_30d,
    COUNTIF(z.dt_created_interaction_at BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 30 DAY) AND v.dt_ordered_at AND z.bl_prospect_interaction=1) msgs_lead_30d,
    MIN(z.dt_approach_start) primeira_abordagem,
    MAX(IF(z.dt_created_interaction_at <= v.dt_ordered_at, z.dt_created_interaction_at, NULL)) ultima_msg_antes,
    COUNTIF(z.dt_created_interaction_at BETWEEN v.dt_ordered_at AND DATETIME_ADD(v.dt_ordered_at, INTERVAL 2 DAY)) msgs_2d_depois
  FROM prosp p JOIN vit v USING (id_transaction)
  JOIN `bp-datawarehouse.staging.int_zenvia_analytics` z ON z.id_prospect=p.id_prospect
  GROUP BY 1
)
SELECT v.id_transaction, v.dt_ordered_at, v.nm_salesman IS NOT NULL tem_vendedor, i.* EXCEPT(id_transaction)
FROM vit v LEFT JOIN inter i USING (id_transaction)
