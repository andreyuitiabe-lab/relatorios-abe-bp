-- Esforço do Comercial medido por menção ao produto na transcrição da conversa Zenvia.
-- Método: REGEXP_CONTAINS no nm_conversation de masterdata.dim_zenvia_approaches.
-- Janela: D-4 a D+6 de cada campanha (CDL D1=2026-05-05, ODI D1=2026-07-17).
WITH conv AS (
  SELECT 'CDL' AS campanha,
         DATE_DIFF(DATE(dt_approach_start), DATE '2026-05-05', DAY)+1 AS dia_campanha,
         REGEXP_CONTAINS(LOWER(nm_conversation), r'clube do livro') AS menciona,
         id_seller
  FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN '2026-05-01' AND '2026-05-10'
  UNION ALL
  SELECT 'ODI',
         DATE_DIFF(DATE(dt_approach_start), DATE '2026-07-17', DAY)+1,
         REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia'),
         id_seller
  FROM masterdata.dim_zenvia_approaches
  WHERE DATE(dt_approach_start) BETWEEN '2026-07-13' AND '2026-07-22'
)
SELECT campanha, dia_campanha,
       COUNT(*) AS abordagens_total,
       COUNTIF(menciona) AS mencoes,
       COUNT(DISTINCT IF(menciona, id_seller, NULL)) AS vendedores_mencionando
FROM conv
GROUP BY 1,2
ORDER BY campanha, dia_campanha
