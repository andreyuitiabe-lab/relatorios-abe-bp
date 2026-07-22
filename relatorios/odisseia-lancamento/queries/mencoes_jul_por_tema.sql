-- Para onde o script do Comercial aponta em julho: menções por tema nas conversas Zenvia.
-- BP10 aproximado por regex ("10 anos" / "dez anos" / "aniversário") — pode ter falsos positivos.
SELECT DATE(dt_approach_start) AS dia,
       COUNT(*) AS abordagens_total,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')) AS odisseia,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'clube do livro')) AS cdl,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'10 anos|dez anos|anivers[aá]rio')) AS bp10
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) >= '2026-07-14'
GROUP BY 1
ORDER BY 1
