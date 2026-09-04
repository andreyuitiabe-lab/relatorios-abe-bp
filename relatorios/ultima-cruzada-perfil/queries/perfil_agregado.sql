-- Perfil agregado dos compradores UC: renda, cartao, genero, pagamento, tempo de casa, engajamento
-- Requer tb_uc_compradores (ver base_compradores.sql)
WITH b AS (SELECT * FROM `bp-staging.dbt_abe.tb_uc_compradores`)
SELECT 'Decil renda' AS dim, CAST(cd_income_decile AS STRING) AS valor, COUNT(*) AS n
FROM b WHERE cd_income_decile > 0 GROUP BY 2
UNION ALL SELECT 'Nivel cartao', COALESCE(nivel_cartao,'sem dado'), COUNT(*) FROM b GROUP BY 2
UNION ALL SELECT 'Genero inferido', COALESCE(nm_gender_inferred,'sem dado'), COUNT(*) FROM b GROUP BY 2
UNION ALL SELECT 'Pagamento', nm_payment_method, COUNT(*) FROM b GROUP BY 2
UNION ALL SELECT 'UF', COALESCE(uf_contato,'sem dado'), COUNT(*) FROM b GROUP BY 2
ORDER BY dim, n DESC
