-- Leads da campanha Odisseia + oferta ativa do Comercial (menções no Zenvia).
-- Janela dinâmica no refresh.py. Snapshot: 13/08/2026.

-- 1) Leads por dia e fonte (captação começou em 08/08/2026; não há campanha [LEAD] no Meta)
SELECT DATE(dt_registered_at_br) AS dia,
       COALESCE(NULLIF(TRIM(LOWER(utm_source)),''),'(vazio)') AS fonte, COUNT(*) AS leads
FROM datamart.dtm_analytics_lead_conversion
WHERE REGEXP_CONTAINS(UPPER(CONCAT(COALESCE(nm_tag,''),' ',COALESCE(utm_campaign,''))), r'ODI\]|ODISSEIA')
GROUP BY 1,2 ORDER BY 1;

-- 2) Conversas do Zenvia mencionando a Odisseia, por dia (método da análise odisseia-lancamento)
SELECT DATE(dt_approach_start) AS dia,
       COUNTIF(REGEXP_CONTAINS(LOWER(nm_conversation), r'odiss[eé]ia')) AS mencoes
FROM masterdata.dim_zenvia_approaches
WHERE DATE(dt_approach_start) >= '2026-07-17'
GROUP BY 1 ORDER BY 1;
