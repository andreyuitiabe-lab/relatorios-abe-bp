-- Curva de referência de receita acumulada por idade do lead (R$/lead, dia 0..60),
-- mediana entre campanhas maduras recentes, SÓ compras antes da abertura de venda
-- (pré-venda) — é o que uma campanha em aquecimento deveria estar realizando.
-- Datas de abertura: campanhas-calendario.md. ELB26 nunca abriu → todas as compras contam.
WITH ref AS (
    SELECT * FROM UNNEST([
        STRUCT('EVG' AS nm_tag, DATE '2026-07-08' AS dt_venda),
        STRUCT('BP10', DATE '2026-07-16'),
        STRUCT('DOM', DATE '2026-04-09'),
        STRUCT('ELB26', NULL)
    ])
),

leads AS (
    SELECT c.nm_tag, c.nm_email, DATE(c.dt_registered_at_br) AS dt_lead, r.dt_venda, c.arr_st_approved_transactions
    FROM `bp-datawarehouse.datamart.cbo_lead_conversion_iql` AS c
    INNER JOIN ref AS r USING (nm_tag)
),

base AS (SELECT nm_tag, COUNT(*) AS qt_leads FROM leads GROUP BY 1),

rec AS (  -- receita por idade, só pré-abertura
    SELECT l.nm_tag, t.days_to_purchase AS idade, SUM(t.vl_payment_gross) AS vl
    FROM leads AS l, UNNEST(l.arr_st_approved_transactions) AS t
    WHERE t.vl_payment_gross IS NOT NULL
      AND t.days_to_purchase BETWEEN 0 AND 60
      AND (l.dt_venda IS NULL OR DATE(t.dt_ordered_at) < l.dt_venda)
    GROUP BY 1, 2
),

grid AS (SELECT nm_tag, idade FROM base, UNNEST(GENERATE_ARRAY(0, 60)) AS idade),

cum AS (
    SELECT g.nm_tag, g.idade,
           SUM(IFNULL(r.vl, 0)) OVER (PARTITION BY g.nm_tag ORDER BY g.idade) / b.qt_leads AS rpl_cum
    FROM grid AS g
    INNER JOIN base AS b USING (nm_tag)
    LEFT JOIN rec AS r USING (nm_tag, idade)
)

SELECT idade,
       ROUND(APPROX_QUANTILES(rpl_cum, 2)[OFFSET(1)], 4) AS rpl_cum_mediana,
       ROUND(MIN(rpl_cum), 4) AS rpl_cum_min,
       ROUND(MAX(rpl_cum), 4) AS rpl_cum_max,
       STRING_AGG(nm_tag ORDER BY nm_tag) AS tags
FROM cum
GROUP BY idade
ORDER BY idade
