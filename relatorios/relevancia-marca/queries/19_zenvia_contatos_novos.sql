-- Demanda espontânea: contatos que CHEGAM sozinhos (inbound), por dia
SELECT DATE(dt_created_contact_at) AS dia,
       COUNT(*) AS contatos_novos,
       COUNTIF(TRIM(nm_group) = 'Suporte') AS suporte,
       COUNTIF(TRIM(nm_group) = 'Comercial') AS comercial,
       COUNT(DISTINCT nm_stage) AS n_stages
FROM masterdata.dim_zenvia_contacts
WHERE DATE(dt_created_contact_at) BETWEEN '2025-08-01' AND '2026-08-20'
GROUP BY 1 ORDER BY 1
