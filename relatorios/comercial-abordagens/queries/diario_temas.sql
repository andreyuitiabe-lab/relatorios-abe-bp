-- Série diária: volume de abordagens do Comercial + menções por tema na transcrição.
-- Janela dinâmica no refresh.py (Q_DIARIO): últimos 28 dias completos
-- (14 atuais + 14 anteriores para comparação). Snapshot: 16/07–12/08/2026.
-- Método: menção ao tema via REGEXP_CONTAINS no nm_conversation
-- (validado na análise odisseia-lancamento). Uma conversa pode citar vários temas.
SELECT DATE(dt_approach_start) AS dia,
       COUNT(*) AS abordagens,
       COUNT(DISTINCT id_seller) AS vendedores,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')) AS odisseia,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'clube do livro')) AS cdl,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'10 anos|dez anos|anivers[aá]rio')) AS bp10,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'vital[ií]cio')) AS vitalicio,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'mecenas')) AS mecenas
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '2026-07-16' AND '2026-08-12'
GROUP BY 1 ORDER BY 1
