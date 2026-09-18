-- High-ticket: funil do Comercial por campanha — abordagem → conversa → venda.
--
-- Fecha o item "quantos disparos/conversas o comercial tinha e taxa de conversão" do pedido
-- original. O relatório já trazia abordagens e conversas; faltava a conversão.
--
-- Método idêntico ao de `relatorios/comercial-abordagens` (revisado em 03/09/2026), para os
-- números serem comparáveis com o que o time já usa:
--   conversa real = abordagem Zenvia do grupo Comercial com qt_prospect_interactions > 0
--   venda atribuída = venda comercial aprovada da MESMA pessoa (telefone OU e-mail) dentro de
--                     14 dias após o início da conversa
--   ⚠️ é atribuição por proximidade temporal, não por vínculo de CRM — mede "conversou e
--      comprou", não "comprou por causa da conversa". Mesmo viés do relatório de referência.
--
-- Duas taxas, porque respondem coisas diferentes:
--   pct_conv_conversa — % das conversas reais que viram venda (eficiência da conversa)
--   pct_conv_abordagem — % das abordagens que viram venda (eficiência do disparo, inclui
--                        quem nunca respondeu). É a que compara esforço bruto entre campanhas.

WITH win AS (
  SELECT 'TRA'   AS sigla, DATE '2023-04-01' AS dt_ini, DATE '2023-05-31' AS dt_fim, 1 AS ord UNION ALL
  SELECT 'TRA2',          DATE '2024-04-01', DATE '2024-05-31', 2 UNION ALL
  SELECT 'BNO24',         DATE '2024-11-01', DATE '2024-11-30', 3 UNION ALL
  SELECT 'BIT',           DATE '2025-04-09', DATE '2025-05-31', 4 UNION ALL
  SELECT 'BNO25',         DATE '2025-11-01', DATE '2025-11-30', 5 UNION ALL
  SELECT 'DBI',           DATE '2026-02-04', DATE '2026-03-31', 6 UNION ALL
  SELECT 'CDL',           DATE '2026-05-05', DATE '2026-06-30', 7 UNION ALL
  SELECT 'BP10',          DATE '2026-06-11', DATE '2026-09-15', 8 UNION ALL
  SELECT 'ODI',           DATE '2026-07-17', DATE '2026-09-16', 9
),

conversas AS (
  SELECT
    w.sigla,
    a.id_approach,
    a.id_prospect,
    DATETIME(a.dt_approach_start)                            AS dt_ini,
    REGEXP_REPLACE(z.cd_cleaned_phone_number, r'[^0-9]', '') AS cd_fone,
    LOWER(z.nm_contact_email)                                AS nm_email,
    a.qt_prospect_interactions > 0                           AS bl_conversa
  FROM win AS w
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_approaches` AS a
    ON DATE(a.dt_approach_start) BETWEEN w.dt_ini AND w.dt_fim
  JOIN `bp-datawarehouse.masterdata.dim_zenvia_contacts` AS z USING (id_prospect)
  WHERE TRIM(z.nm_group) = 'Comercial'
),

vendas AS (
  SELECT
    w.sigla,
    t.id_transaction,
    t.dt_ordered_at,
    t.vl_payment_gross,
    REGEXP_REPLACE(c.cd_cleaned_phone_number, r'[^0-9]', '') AS cd_fone,
    LOWER(c.nm_email)                                        AS nm_email
  FROM win AS w
  JOIN `bp-datawarehouse.masterdata.fct_transactions` AS t
    ON DATE(t.dt_ordered_at) BETWEEN w.dt_ini AND w.dt_fim
  JOIN `bp-datawarehouse.masterdata.dim_contact` AS c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND t.bl_is_renovation = FALSE
    AND t.bl_is_commercial_channel = TRUE
),

-- conversa que precedeu venda da mesma pessoa em até 14 dias (telefone OU e-mail)
casadas AS (
  SELECT DISTINCT c.sigla, c.id_approach
  FROM conversas AS c
  JOIN vendas AS v
    ON v.sigla = c.sigla
   AND LENGTH(c.cd_fone) >= 10
   AND v.cd_fone = c.cd_fone
  WHERE c.dt_ini BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 14 DAY) AND v.dt_ordered_at
    AND c.bl_conversa
  UNION DISTINCT
  SELECT DISTINCT c.sigla, c.id_approach
  FROM conversas AS c
  JOIN vendas AS v
    ON v.sigla = c.sigla
   AND c.nm_email LIKE '%@%'
   AND v.nm_email = c.nm_email
  WHERE c.dt_ini BETWEEN DATETIME_SUB(v.dt_ordered_at, INTERVAL 14 DAY) AND v.dt_ordered_at
    AND c.bl_conversa
)

SELECT
  w.ord,
  w.sigla,
  COUNT(*)                                                          AS qt_abordagens,
  COUNTIF(c.bl_conversa)                                            AS qt_conversas,
  COUNT(DISTINCT IF(k.id_approach IS NOT NULL, c.id_approach, NULL)) AS qt_conversas_com_venda,
  ROUND(100 * COUNTIF(c.bl_conversa) / COUNT(*), 1)                 AS pct_resposta,
  ROUND(100 * COUNT(DISTINCT IF(k.id_approach IS NOT NULL, c.id_approach, NULL))
        / NULLIF(COUNTIF(c.bl_conversa), 0), 1)                     AS pct_conv_conversa,
  ROUND(100 * COUNT(DISTINCT IF(k.id_approach IS NOT NULL, c.id_approach, NULL))
        / COUNT(*), 2)                                              AS pct_conv_abordagem
FROM win AS w
JOIN conversas AS c USING (sigla)
LEFT JOIN casadas AS k ON k.sigla = c.sigla AND k.id_approach = c.id_approach
GROUP BY 1, 2
ORDER BY w.ord;
