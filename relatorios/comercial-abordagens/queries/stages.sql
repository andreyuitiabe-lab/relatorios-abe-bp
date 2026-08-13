-- Em que etapa do funil as abordagens acontecem (janela atual de 14 dias).
-- Janela dinâmica no refresh.py (Q_STAGES / Q_STAGES_ODI). Snapshot: 30/07–12/08/2026.

-- 1) Todas as abordagens por etapa
SELECT COALESCE(nm_stage, '(sem etapa)') AS stage, COUNT(*) AS abordagens
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '2026-07-30' AND '2026-08-12'
GROUP BY 1 ORDER BY 2 DESC LIMIT 12;

-- 2) Só conversas que mencionam a Odisseia
SELECT COALESCE(nm_stage, '(sem etapa)') AS stage, COUNT(*) AS conversas
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) BETWEEN '2026-07-30' AND '2026-08-12'
  AND REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')
GROUP BY 1 ORDER BY 2 DESC LIMIT 8;
