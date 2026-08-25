-- Tempo de casa na BP até a compra da Odisseia
-- Gerada por refresh.py (fonte canônica das CTEs) — relatorios/odisseia-perfil
WITH 
  odi_tx AS (
    SELECT
      t.id_gateway_customer,
      t.id_transaction,
      t.dt_ordered_at,
      t.vl_payment_gross,
      t.bl_is_commercial_channel,
      dpi.id_person,
      CASE
        WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'black vitalício \+ odisseia|odisseia - ouro')
          THEN 'Odisseia + Black Vitalício'
        WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'odisseia.*travessia')
          THEN 'Odisseia + Travessia'
        WHEN REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'clube do livro \+ odisseia')
          THEN 'Odisseia + Clube do Livro'
        WHEN t.nm_gateway_plan = 'odisseia-curso-avulso'
          THEN 'Odisseia - Curso Avulso'
        WHEN REGEXP_CONTAINS(LOWER(t.nm_gateway_product), r'odisseia - digital')
          OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'odisseia - bronze')
          THEN 'Odisseia - Digital'
        WHEN t.nm_gateway_plan IN ('livro-odisseia-edicao-colecionador','livro-odisseia')
          THEN 'Odisseia - Livro Físico'
      END AS nm_categoria
    FROM `bp-datawarehouse.masterdata.fct_transactions` t
    JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    WHERE t.nm_status = 'approved'
      AND t.bl_is_renovation = FALSE
      AND c.nm_email IS NOT NULL
      AND (t.nm_gateway_plan IN ('livro-odisseia-edicao-colecionador','livro-odisseia','odisseia-curso-avulso')
           OR REGEXP_CONTAINS(LOWER(t.nm_gateway_product), r'odis')
           OR REGEXP_CONTAINS(LOWER(COALESCE(t.nm_gateway_offer,'')), r'odis'))
  ),
  odi_tx_cat AS (
    SELECT
      *,
      CASE WHEN nm_categoria IN ('Odisseia + Black Vitalício','Odisseia + Clube do Livro')
           THEN 0 ELSE 1 END AS bl_core,
      CASE WHEN nm_categoria IN ('Odisseia - Livro Físico','Odisseia + Travessia',
                                 'Odisseia + Black Vitalício','Odisseia + Clube do Livro')
           THEN 1 ELSE 0 END AS bl_livro_fisico
    FROM odi_tx
    WHERE nm_categoria IS NOT NULL
  ),
  odi_compradores AS (
    SELECT
      id_person,
      MIN(dt_ordered_at)                                        AS dt_compra_odi,
      SUM(IF(bl_core = 1, vl_payment_gross, 0))                 AS vl_pago_odisseia,
      MAX(bl_livro_fisico)                                      AS bl_livro_fisico,
      MAX(CAST(bl_is_commercial_channel AS INT64))              AS bl_comercial
    FROM odi_tx_cat
    GROUP BY id_person
  ),
  subscription_history AS (
    SELECT
      dpi.id_person,
      s.dt_started_at,
      s.dt_expires_in,
      s.nm_subscription_recurrence
    FROM `bp-datawarehouse.masterdata.dim_subscriptions` s
    JOIN `bp-datawarehouse.masterdata.dim_contact` c ON c.id_gateway_customer = s.id_gateway_customer
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    WHERE s.nm_type = 'paid'
      AND s.nm_gateway_plan NOT IN ('clube-do-livro','livro-odisseia-edicao-colecionador','livro-odisseia','odisseia-curso-avulso')
      AND dpi.id_person IN (SELECT id_person FROM odi_compradores)
  ),
  vitalicio_fct AS (
    SELECT DISTINCT o.id_person
    FROM `bp-datawarehouse.masterdata.fct_transactions` t
    JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
    JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
      ON dpi.nm_identifier = c.nm_email
      AND dpi.nm_identifier_type = 'email'
    JOIN odi_compradores o USING (id_person)
    WHERE t.bl_lifetime_offer = TRUE
      AND t.nm_status = 'approved'
      AND t.nm_gateway_plan NOT IN ('clube-do-livro','livro-odisseia-edicao-colecionador','livro-odisseia','odisseia-curso-avulso')
      AND DATE(t.dt_ordered_at) < DATE(o.dt_compra_odi)
  ),
  member_classification AS (
    SELECT
      o.id_person,
      CASE
        WHEN COUNTIF(s.nm_subscription_recurrence = 'vitalício' AND s.dt_started_at < o.dt_compra_odi) > 0
          OR MAX(IF(vf.id_person IS NOT NULL, 1, 0)) = 1 THEN 'Vitalício'
        WHEN COUNTIF(o.dt_compra_odi > s.dt_started_at AND o.dt_compra_odi <= s.dt_expires_in) > 0 THEN 'Membro Ativo'
        WHEN COUNTIF(s.dt_started_at < o.dt_compra_odi) > 0 THEN 'Ex-Membro'
        ELSE 'Nunca foi Membro'
      END AS status
    FROM odi_compradores o
    LEFT JOIN subscription_history s USING (id_person)
    LEFT JOIN vitalicio_fct vf USING (id_person)
    GROUP BY o.id_person
  )
,
primeira_compra AS (
  SELECT o.id_person, MIN(t.dt_ordered_at) AS dt_primeira_bp
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  JOIN `bp-datawarehouse.masterdata.dim_contact` dc USING (id_gateway_customer)
  JOIN `bp-datawarehouse.masterdata.dim_person_identity` dpi
    ON dpi.nm_identifier = dc.nm_email AND dpi.nm_identifier_type = 'email'
  JOIN odi_compradores o USING (id_person)
  WHERE t.nm_status = 'approved'
  GROUP BY 1
)
SELECT
  CASE
    WHEN mc.status = 'Nunca foi Membro' AND DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 0
      THEN 'Odisseia como 1ª compra'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 180  THEN '< 6 meses'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 365  THEN '6–12 meses'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 730  THEN '1–2 anos'
    WHEN DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY) <= 1460 THEN '2–4 anos'
    ELSE 'Mais de 4 anos'
  END AS faixa,
  COUNT(*) AS qt,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS pct,
  ROUND(AVG(DATE_DIFF(DATE(o.dt_compra_odi), DATE(p.dt_primeira_bp), DAY))) AS media_dias
FROM odi_compradores o
JOIN primeira_compra p USING (id_person)
JOIN member_classification mc USING (id_person)
GROUP BY 1 ORDER BY media_dias
