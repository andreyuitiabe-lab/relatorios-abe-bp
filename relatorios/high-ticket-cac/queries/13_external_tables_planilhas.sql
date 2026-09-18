-- External tables sobre as planilhas históricas de mídia paga do time de tráfego.
--
-- POR QUÊ: essas planilhas têm nível de ANÚNCIO desde 01/06/2022 — cobertura que nenhuma outra
-- fonte tem. O warehouse só tem nome de anúncio confiável desde mar/2025 e a Marketing API
-- alcança 37 meses (e o token caiu em 18/09). É a única forma de contar e medir anúncio nas
-- campanhas antigas: Travessia, Travessia 2ª turma, BNO24 e Bitcoin 1.
--
-- ⚠️ PRÉ-REQUISITO: a credencial precisa de escopo de Drive/Sheets, senão toda consulta a estas
--    tabelas devolve `403 Permission denied while getting Drive credentials`. Rodar UMA vez:
--
--      gcloud auth application-default login \
--        --scopes=openid,https://www.googleapis.com/auth/cloud-platform,\
--    https://www.googleapis.com/auth/drive.readonly,https://www.googleapis.com/auth/spreadsheets.readonly
--
--    ⚠️ É `application-default login`, NÃO `gcloud auth login` — são armazéns de credencial
--    diferentes e só o primeiro alimenta o `bqq`. Conferir depois com:
--      gcloud auth application-default print-access-token | xargs -I{} \
--        curl -s "https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}"
--    O escopo `drive.readonly` tem que aparecer na lista.
--
-- ⚠️ Colunas de valor entram como STRING de propósito: a planilha usa vírgula decimal
--    (`48,14`) e ponto de milhar, o que quebraria FLOAT64 silenciosamente (viraria NULL).
--    A conversão fica explícita na view abaixo.
--
-- Padrão idêntico ao das external tables Adveronix já em produção
-- (`~/meu_projeto/BigQuery/migracao-adveronix/sql/00_rollback_external_tables.sql`).

-- ── 1) Facebook nível de anúncio, desde 01/06/2022 ──────────────────────────
CREATE OR REPLACE EXTERNAL TABLE `bp-staging.dbt_abe.tb_ht_sheet_meta_ads`
(
  day                        STRING,
  ad_name                    STRING,
  amount_spent               STRING,
  impressions                STRING,
  outbound_clicks            STRING,
  purchases                  STRING,
  purchases_conversion_value STRING,
  three_second_views         STRING,
  thruplays                  STRING,
  ad_id                      STRING,
  ad_set_name                STRING
)
OPTIONS (
  format = 'GOOGLE_SHEETS',
  uris = ['https://docs.google.com/spreadsheets/d/1vpHkpsndC9WhazBDp-WpnSAgUSDA3JJGyYDMcc9DCNU/edit'],
  sheet_range = "'01. Facebook - Ads - Venda'!A:K",
  skip_leading_rows = 1
);

-- ── 2) A planilha VIVA (Google/YouTube/PMax em abas separadas) ──────────────
-- ⚠️ O sheet_range abaixo é uma HIPÓTESE: os nomes exatos das abas não foram confirmados
--    (o MCP do Drive só devolve amostra). Antes de rodar, listar as abas com:
--      TOK=$(gcloud auth application-default print-access-token)
--      curl -s -H "Authorization: Bearer $TOK" \
--        "https://sheets.googleapis.com/v4/spreadsheets/1ZaK74knwbvqQ9UsISiJxWubAW5tEnY3aM9rRUbR_IzM?fields=sheets.properties(title,gridProperties/rowCount)"
--    e ajustar. Deixo a da aba 1 (Facebook), que é a única cujo nome eu vi.
CREATE OR REPLACE EXTERNAL TABLE `bp-staging.dbt_abe.tb_ht_sheet_midia_viva`
(
  day                        STRING,
  ad_name                    STRING,
  amount_spent               STRING,
  impressions                STRING,
  outbound_clicks            STRING,
  purchases                  STRING,
  purchases_conversion_value STRING,
  three_second_views         STRING,
  thruplays                  STRING,
  ad_id                      STRING
)
OPTIONS (
  format = 'GOOGLE_SHEETS',
  uris = ['https://docs.google.com/spreadsheets/d/1ZaK74knwbvqQ9UsISiJxWubAW5tEnY3aM9rRUbR_IzM/edit'],
  sheet_range = "'01. Facebook - Ads - Venda'!A:J",
  skip_leading_rows = 1
);

-- ── 3) View tipada: converte o formato brasileiro e descarta linha sem data ──
CREATE OR REPLACE VIEW `bp-staging.dbt_abe.vw_ht_sheet_meta_ads` AS
SELECT
  PARSE_DATE('%Y-%m-%d', day)                                              AS dt,
  ad_name                                                                  AS nm_anuncio,
  ad_set_name                                                              AS nm_conjunto,
  ad_id                                                                    AS id_anuncio,
  -- "1.234,56" -> 1234.56
  SAFE_CAST(REPLACE(REPLACE(amount_spent, '.', ''), ',', '.') AS FLOAT64)   AS vl_spend,
  SAFE_CAST(REPLACE(impressions, '.', '') AS INT64)                        AS qt_impressoes,
  SAFE_CAST(REPLACE(outbound_clicks, '.', '') AS INT64)                    AS qt_cliques,
  SAFE_CAST(REPLACE(purchases, '.', '') AS INT64)                          AS qt_compras,
  SAFE_CAST(REPLACE(REPLACE(purchases_conversion_value, '.', ''), ',', '.') AS FLOAT64) AS vl_receita_pixel
FROM `bp-staging.dbt_abe.tb_ht_sheet_meta_ads`
WHERE REGEXP_CONTAINS(day, r'^\d{4}-\d{2}-\d{2}$');
