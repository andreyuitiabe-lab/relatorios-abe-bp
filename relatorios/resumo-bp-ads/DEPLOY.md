# Deploy — BP Ads (PR #152, mergeado em 16/09 · commit 70637462c)

A página `/bp-ads` só carrega depois dos dois passos abaixo. Antes disso ela mostra erro.

## Passo 1 — Migration no Supabase

Abrir o **SQL Editor** do projeto `fliucnevgcnsellnftgu` e rodar o conteúdo de:

    supabase/migrations/20260828120000_resumo_bp_dominios.sql

Cria a tabela `resumo_bp_dominios` (classificação de domínio: anunciante / fonte externa /
conteúdo BP), com RLS para `authenticated` e seed de **58** domínios já classificados —
incluindo os 4 anunciantes conhecidos (Vimansca, Sendflow, Lídio Carraro, Insider Store).

É idempotente (`CREATE TABLE IF NOT EXISTS`, `ON CONFLICT DO NOTHING`) — rodar duas vezes não quebra.

Conferir:

    select tipo, count(*) from public.resumo_bp_dominios group by tipo;
    -- esperado: anunciante 4 | conteudo_bp 12 | fonte_externa 42

## Passo 2 — Deploy das 2 edge functions pela Lovable

O push NÃO deploya edge function neste repo. Subir pela Lovable, mesmo fluxo do X Ads / Lambda / JOM:

- `fetch-bigquery-resumo-bp`
- `fetch-bigquery-bp-ads-funil`

Conferir se subiram (401 = no ar e exigindo auth, que é o esperado; 404 = não deployada):

    curl -s -o /dev/null -w "%{http_code}\n" -X POST \
      https://fliucnevgcnsellnftgu.supabase.co/functions/v1/fetch-bigquery-resumo-bp
    curl -s -o /dev/null -w "%{http_code}\n" -X POST \
      https://fliucnevgcnsellnftgu.supabase.co/functions/v1/fetch-bigquery-bp-ads-funil

## Passo 3 — Abrir e validar

- `/bp-ads` → aba **Funil de negociações**: deve mostrar 85 negociações ativas e ~R$ 73,5k em carteira,
  com o aviso âmbar sobre o CRM no topo.
- Aba **Resultados dos disparos**: ~430 edições; trocar para "Parceiro: Vimansca" e clicar
  **Exportar PDF** — tem que sair 1 página A4, sem o cabeçalho "BP Ads" e sem a barra de abas.
- `/admin/resumo-bp-anunciantes`: fila de pendências vazia e 4 anunciantes cadastrados.

Se a fila de pendências vier cheia, é sinal de que a migration não rodou (sem a tabela, nada fica
classificado).

## Não precisa de nada além disso

Sem job de refresh: as duas functions consultam o BigQuery na hora, e o mart
`cbo_insider_email_analytics_daily` é reconstruído pelo dbt.

Secrets já existem no projeto (`CL_SERVICE_ACCOUNT_EMAIL`, `CL_PRIVATE_KEY`) — as functions usam
as mesmas das outras `fetch-bigquery-*`.
