-- Períodos de campanha (dummies de fase para o contrafactual)
-- ⚠️ Datas podem derivar da realidade (ver campanhas-calendario.md) — uso como controle, não como verdade
SELECT *
FROM bp-staging.dbt_abe.tb_campaign_period
ORDER BY 1
