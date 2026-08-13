-- Mix de vendas do canal Comercial nas janelas D1–Dn de cada campanha:
-- CDL a partir de 05/05 vs Odisseia a partir de 17/07. Vitalícios "Aniv26" = oferta BP10.
-- n é dinâmico no refresh.py (Q_MIX). Snapshot abaixo: D1–D27 (13/08/2026).
WITH v AS (
  SELECT CASE WHEN DATE(dt_ordered_at) BETWEEN '2026-05-05' AND '2026-05-31'
              THEN 'mai' ELSE 'jul' END AS janela,
         CASE
           WHEN nm_gateway_plan='clube-do-livro' OR nm_gateway_plan LIKE 'ebooks%clube%' THEN 'Clube do Livro'
           WHEN nm_gateway_plan='livro-odisseia-edicao-colecionador'
             OR LOWER(nm_gateway_product) LIKE '%odis%' THEN 'Odisseia'
           WHEN LOWER(nm_gateway_plan) LIKE '%bp-10%' OR LOWER(nm_gateway_plan) LIKE '%10-anos%'
             OR LOWER(nm_gateway_product) LIKE '%10 anos%' THEN 'Combos BP10'
           WHEN nm_gateway_plan LIKE 'mecenas%' THEN 'Mecenas'
           WHEN bl_lifetime_offer THEN 'Vitalício'
           ELSE 'Assinaturas/outros'
         END AS produto,
         vl_payment_gross
  FROM masterdata.fct_transactions
  WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
    AND (DATE(dt_ordered_at) BETWEEN '2026-05-05' AND '2026-05-31'
      OR DATE(dt_ordered_at) BETWEEN '2026-07-17' AND '2026-08-12')
)
SELECT janela, produto, COUNT(*) AS vendas, ROUND(SUM(vl_payment_gross),0) AS receita,
       ROUND(100*COUNT(*)/SUM(COUNT(*)) OVER (PARTITION BY janela),1) AS pct_vendas
FROM v
GROUP BY 1,2
ORDER BY janela, vendas DESC;

-- Receita TOTAL do canal Comercial por período (tudo que o time vendeu, qualquer produto).
-- Janelas D1–Dn de cada campanha (n=27 no snapshot): CDL 05/05–31/05 vs ODI 17/07–12/08.
SELECT CASE WHEN DATE(dt_ordered_at) BETWEEN '2026-05-05' AND '2026-05-31' THEN 'periodo CDL' ELSE 'periodo ODI' END AS periodo,
       COUNT(*) AS vendas,
       ROUND(SUM(vl_payment_gross),0) AS receita,
       ROUND(SUM(vl_payment_gross)/27,0) AS receita_dia,
       ROUND(AVG(vl_payment_gross),0) AS ticket_medio,
       COUNT(DISTINCT REGEXP_EXTRACT(LOWER(nm_pptc_tracking_name), r'(c\d{4})')) AS vendedores_com_venda
FROM masterdata.fct_transactions
WHERE nm_status='approved' AND bl_is_renovation=FALSE AND bl_is_commercial_channel=TRUE
  AND (DATE(dt_ordered_at) BETWEEN '2026-05-05' AND '2026-05-31'
    OR DATE(dt_ordered_at) BETWEEN '2026-07-17' AND '2026-08-12')
GROUP BY 1;
