-- Ponte device → conta: é o passo que torna a receita mensurável.
-- Sem ele, Firebase e Guru ficam em universos separados e a campanha só tem CPI, não ROAS.
-- O resíduo (entrou na conta − conta criada) dá o piso de quem já era usuário
-- antes do install: >= 671 dos 3.374 no relatório de 13/08/2026.
SELECT
    id_pseudo_user,
    MIN(id_user) AS id_user
FROM `bp-datawarehouse.staging.stg_firebase__bp_platform_events`
WHERE dt_created_at BETWEEN '2026-06-18' AND '2026-08-13'
    AND id_user IS NOT NULL
GROUP BY id_pseudo_user
