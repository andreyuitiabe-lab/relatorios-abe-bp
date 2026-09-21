-- High-ticket: as mesmas métricas em DOIS RECORTES, para o toggle do relatório.
--
-- PEDIDO DO ANDRÉ (21/09/2026): "nos gráficos, você consegue adicionar um toggle para ver dados da
-- campanha e dos produtos de alto ticket". É a formalização de uma dúvida que ele já tinha
-- levantado ao ver o gráfico de perfil: os gráficos contavam TODOS os compradores da campanha, e
-- nas campanhas com muita venda de entrada isso descreve outra pessoa.
--
-- Recortes:
--   campanha    — todo comprador da campanha (o que o relatório mostrava até aqui)
--   alto_ticket — só quem teve transação acima de R$ 1.000 (mesmo corte da faixa "alto")
--
-- ⚠️ O QUE ESTE ARQUIVO NÃO FAZ, de propósito: não reparte disparo de CRM nem abordagem do
--    Comercial por faixa de preço. Uma mensagem enviada não tem ticket — quem recebeu ainda não
--    comprou. Por isso os gráficos de esforço de CRM e de funil do Comercial NÃO ganham toggle:
--    o recorte não existe no dado, e fabricá-lo por rateio seria inventar.
--
-- ⚠️ O CAC do recorte de alto ticket usa rateio da verba POR RECEITA (convenção oficial, decisão
--    do André em 17/09) — é o mesmo número de `15_cac_por_faixa_valor.sql` na faixa 'alto', e por
--    construção o ROAS fica igual nos dois recortes. Quem compara recorte deve olhar o CAC.

WITH base AS (
  SELECT
    ord, sigla, id_comprador, vl_receita, vl_maior_tx, nm_canal,
    st_status_compra, bl_vitalicio_previo
  FROM `bp-staging.dbt_abe.tb_ht_compradores`
  WHERE bl_universo_principal
    AND sigla <> 'BNO25'   -- fora do escopo desde 21/09 (ver ANALISE.md)
),

-- verba de mídia por campanha: a mesma do consolidado
midia AS (
  SELECT 'TRA' AS sigla, 869815.77 AS vl_midia UNION ALL
  SELECT 'TRA2',  178663.00 UNION ALL SELECT 'BNO24', 5466226.02 UNION ALL
  SELECT 'BIT',  1282908.90 UNION ALL
  SELECT 'DBI',   170108.69 UNION ALL SELECT 'CDL',   5071111.74 UNION ALL
  SELECT 'BP10', 7938719.68 UNION ALL SELECT 'ODI',   1690931.03
),

total_camp AS (
  SELECT sigla, SUM(vl_receita) AS vl_receita_total
  FROM base GROUP BY 1
),

-- o mesmo conjunto duas vezes: inteiro e filtrado
recorte AS (
  SELECT 'campanha' AS nm_recorte, b.* FROM base AS b
  UNION ALL
  SELECT 'alto_ticket', b.* FROM base AS b WHERE b.vl_maior_tx > 1000
)

SELECT
  r.ord,
  r.sigla,
  r.nm_recorte,
  COUNT(*)                                                       AS qt_compradores,
  ROUND(SUM(r.vl_receita))                                       AS vl_receita,
  ROUND(AVG(r.vl_receita))                                       AS vl_ticket,

  -- perfil do comprador
  ROUND(100 * COUNTIF(r.st_status_compra = 'membro' AND r.bl_vitalicio_previo)     / COUNT(*), 1) AS pct_membro_vitalicio,
  ROUND(100 * COUNTIF(r.st_status_compra = 'membro' AND NOT r.bl_vitalicio_previo) / COUNT(*), 1) AS pct_membro_assinante,
  ROUND(100 * COUNTIF(r.st_status_compra = 'ex_membro')  / COUNT(*), 1)            AS pct_ex_membro,
  ROUND(100 * COUNTIF(r.st_status_compra = 'nao_membro') / COUNT(*), 1)            AS pct_nao_membro,

  -- origem do comprador
  ROUND(100 * COUNTIF(r.nm_canal = 'midia_paga')      / COUNT(*), 1)               AS pct_comp_midia,
  ROUND(100 * COUNTIF(r.nm_canal = 'comercial')       / COUNT(*), 1)               AS pct_comp_comercial,
  ROUND(100 * COUNTIF(r.nm_canal = 'crm')             / COUNT(*), 1)               AS pct_comp_crm,
  ROUND(100 * COUNTIF(r.nm_canal NOT IN ('midia_paga','comercial','crm')
                      OR r.nm_canal IS NULL)          / COUNT(*), 1)               AS pct_comp_organico,

  -- custo por comprador do recorte, com a verba rateada por receita
  ROUND(m.vl_midia * SUM(r.vl_receita) / t.vl_receita_total / COUNT(*), 2)         AS vl_cac,
  ROUND(SUM(r.vl_receita) / NULLIF(m.vl_midia * SUM(r.vl_receita) / t.vl_receita_total, 0), 2) AS vl_roas,
  ROUND(100 * SUM(r.vl_receita) / t.vl_receita_total, 1)                           AS pct_receita_da_campanha
FROM recorte AS r
JOIN total_camp AS t USING (sigla)
LEFT JOIN midia  AS m USING (sigla)
GROUP BY r.ord, r.sigla, r.nm_recorte, m.vl_midia, t.vl_receita_total
ORDER BY r.ord, r.nm_recorte DESC;
