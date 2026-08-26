-- Receita realizada acumulada por dia (data da compra), dos leads da campanha.
DECLARE tag STRING DEFAULT 'ENE';
DECLARE dt_inicio DATE DEFAULT '2026-07-27';

WITH tx AS (
    SELECT DATE(t.dt_ordered_at) AS dt, t.vl_payment_gross AS vl
    FROM `bp-datawarehouse.datamart.cbo_lead_conversion_iql` AS c, UNNEST(c.arr_st_approved_transactions) AS t
    WHERE c.nm_tag = tag AND DATE(c.dt_registered_at_br) >= dt_inicio
      AND t.vl_payment_gross IS NOT NULL AND t.days_to_purchase >= 0
)

SELECT dt, COUNT(*) AS qt_vendas, ROUND(SUM(vl), 2) AS vl_receita,
       ROUND(SUM(SUM(vl)) OVER (ORDER BY dt), 2) AS vl_receita_acum
FROM tx GROUP BY dt ORDER BY dt
