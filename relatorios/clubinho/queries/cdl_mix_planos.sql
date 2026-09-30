-- Mix de planos do Clube do Livro por comprador (benchmark para o Clubinho BP, 30/09/2026)
-- Nível 1 = só físico | Nível 2 = físico + digital (ebook+audiobook, "Prata") | Nível 3 = Ouro (físico + Black Vitalício)
-- Pessoa = e-mail (dim_contact), fallback id_gateway_customer. Só transações aprovadas (posse atual).
-- "direto" = perna do nível comprada até 1 dia da 1ª compra do físico; "upgrade" = depois.
WITH tx AS (
  SELECT COALESCE(LOWER(TRIM(c.nm_email)), t.id_gateway_customer) pessoa,
         t.dt_ordered_at, t.bl_is_commercial_channel, t.nm_gateway_offer, t.vl_payment_gross,
         CASE
           WHEN t.nm_gateway_plan IN ('clube-do-livro','clube-do-livro-basico') THEN 'fisico'
           WHEN t.nm_gateway_plan LIKE 'ebooks-%clube%' THEN 'digital'
           WHEN t.nm_gateway_plan = 'black' THEN 'ouro'
         END perna
  FROM `bp-datawarehouse.masterdata.fct_transactions` t
  LEFT JOIN `bp-datawarehouse.masterdata.dim_contact` c USING (id_gateway_customer)
  WHERE t.nm_status = 'approved'
    AND NOT REGEXP_CONTAINS(t.nm_gateway_offer, r'(?i)teste')
    AND NOT (t.nm_gateway_plan = 'clube-do-livro' AND t.nm_gateway_product LIKE '%Bundle Audiobook%')
    AND (t.nm_gateway_plan IN ('clube-do-livro','clube-do-livro-basico')
         OR t.nm_gateway_plan LIKE 'ebooks-%clube%'
         OR (t.nm_gateway_plan = 'black' AND (LOWER(t.nm_gateway_product) LIKE '%clube do livro%'
                                              OR LOWER(t.nm_gateway_offer) LIKE '%clube do livro%')))
), p AS (
  SELECT pessoa,
         MIN(IF(perna = 'fisico', dt_ordered_at, NULL)) dt_fisico,
         MIN(IF(perna = 'digital', dt_ordered_at, NULL)) dt_digital,
         MIN(IF(perna = 'ouro', dt_ordered_at, NULL)) dt_ouro,
         MIN(dt_ordered_at) dt_entrada,
         ARRAY_AGG(bl_is_commercial_channel ORDER BY dt_ordered_at LIMIT 1)[OFFSET(0)] comercial,
         SUM(vl_payment_gross) receita
  FROM tx GROUP BY 1
)
SELECT
  IF(comercial, 'Comercial', 'Digital') canal,
  CASE WHEN dt_ouro IS NOT NULL THEN '3 Ouro (físico + Black Vitalício)'
       WHEN dt_digital IS NOT NULL THEN '2 Físico + Digital'
       ELSE '1 Só físico' END nivel,
  CASE WHEN dt_ouro IS NOT NULL THEN IF(DATE_DIFF(DATE(dt_ouro), DATE(dt_entrada), DAY) <= 1, 'direto', 'upgrade')
       WHEN dt_digital IS NOT NULL THEN IF(DATE_DIFF(DATE(dt_digital), DATE(dt_entrada), DAY) <= 1, 'direto', 'upgrade')
       ELSE 'direto' END como,
  COUNT(*) pessoas,
  ROUND(AVG(receita)) receita_media
FROM p
WHERE dt_fisico IS NOT NULL OR dt_ouro IS NOT NULL   -- exclui quem comprou só o digital
GROUP BY 1, 2, 3
ORDER BY 1, 2, 3
