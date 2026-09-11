-- Instituições beneficiárias registradas no DW.
-- Só o padrão "Uploaded from Caverna Aluno de instituição parceira <INSTITUIÇÃO> <email op> <id>"
-- carrega o nome da instituição; nos demais formatos do nm_reason o texto restante é o nome do
-- OPERADOR BP, não da instituição — por isso ficam de fora (contam como "sem registro").
-- Limpeza: remove boilerplate, e-mails e ids hex de 24 chars; descarta restos como "não" e
-- "renovação tratado mec".
WITH mecenas AS (
  SELECT id_user, nm_reason
  FROM `bp-datawarehouse.masterdata.dim_subscriptions`
  WHERE nm_create_reason_type = 'mecenas'
),

limpo AS (
  SELECT
    id_user,
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(
      nm_reason,
      r'Uploaded from Caverna\s*', ''),
      r'Aluno de instituição parceira\s*', ''),
      r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+', ''),
      r'\b[0-9a-f]{24}\b', '')) AS inst
  FROM mecenas
  WHERE nm_reason LIKE 'Uploaded from Caverna%'
)

SELECT
  inst,
  COUNT(DISTINCT id_user) AS qt_contas
FROM limpo
WHERE LOWER(inst) NOT IN ('', 'não', 'nao')
  AND LOWER(inst) NOT LIKE 'renova%'
  AND NOT REGEXP_CONTAINS(LOWER(inst), r'^(outro\s+)?bolsista')  -- boilerplate, não instituição
GROUP BY inst
HAVING qt_contas >= 5
ORDER BY qt_contas DESC
