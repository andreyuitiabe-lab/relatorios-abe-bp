# Análise: El Salvador (ELS) — Funil de Campanha

**Data:** mai/2026  
**Status:** concluída (pendências listadas abaixo)  
**Sigla da campanha:** ELS  
**Relatório:** [index.html](index.html)  
**Wiki:** `~/.claude/wiki-brasil-paralelo/pages/els-analise.md`

---

## Pergunta original

Entender o funil completo da campanha ELS: quantos viewers, leads e compradores; qual o perfil socioeconômico de cada grupo; como os dois métodos de atribuição (UTM vs lead_last_tracking) se comparam; e o que o proxy de qualidade de leads consegue ou não prever.

---

## Decisões de abordagem

- Compradores identificados via UTM em `fct_transactions` (mais completo: 4.733) — não via `nm_lead_last_tracking` (só 2.037, perde direto/Comercial/live)
- Viewers: `obt_kafka__view_sessions` com `nm_playlist LIKE 'El Salvador%'` e `vl_watch_time_seconds >= 300`
- Proxy de qualidade de leads: apenas 15% da base de leads tem dados em `dim_user` — usado para ranking relativo entre criativos, não previsão absoluta
- Comparação de perfil via `dtm_purchasing_power` (decil de renda) e `dim_user`

---

## Achados principais

- Funil: 214.861 leads → 32.472 viewers → 4.733 compradores → R$1,51M
- 85% dos compradores são novos clientes (sem histórico anterior)
- Perfil do comprador = perfil do viewer (decil 5,61), não o do lead (decil 4,95) — conversão filtra qualidade
- 71% dos compradores nunca assistiram na plataforma (aquisição líquida, não reengajamento)
- Dois métodos de atribuição capturam públicos distintos — diferença de 2.696 pessoas são compras sem lead registration prévia
- Proxy de leads subestima qualidade real do comprador em ~3–4 pp no decil7+ — válido para ranking entre criativos, inválido para previsão absoluta

---

## Pendências / próximos passos

- [ ] Análise do papel dos leads na fase de aquecimento vs venda (qual semana converte mais?)
- [ ] Comparar perfil dos compradores ELS por criativo (como feito em HID/GOD)
- [ ] Entender os 582 viewers que compraram: upgrade de plano ou novo produto?
- [ ] Análise temporal de conversão de leads semana a semana

---

## Queries

| Arquivo | O que faz |
|---------|-----------|
| [queries/funil_viewers_leads_compradores.sql](queries/funil_viewers_leads_compradores.sql) | Perfil socioeconômico dos 3 grupos do funil |
| [queries/compradores_historico_anterior.sql](queries/compradores_historico_anterior.sql) | % compradores novos vs clientes existentes |
| [queries/vendas_por_canal_produto.sql](queries/vendas_por_canal_produto.sql) | Receita por canal e plano |

## Wiki atualizada

- `wiki-brasil-paralelo/pages/els-analise.md` — análise completa criada
- `wiki-bp/pages/metricas-referencia.md` — métricas ELS adicionadas
- `wiki-bp/pages/queries-referencia.md` — query de funil viewers×leads×compradores
- `wiki-bp/pages/bq-regras.md` — distinção UTM vs nm_lead_last_tracking para atribuição
---

## Checklist de revisão

- [ ] Filtros padrão aplicados: `nm_status = 'approved'`, `bl_is_renovation = FALSE`
- [ ] Exclusões obrigatórias para o tipo de análise (ver `regras-negocio.md`)
- [ ] Resultados batem com benchmarks em `metricas-referencia.md` ou desvio explicado
- [ ] Método de atribuição de campanha correto (UTM vs lead_last_tracking — ver `bq-regras.md`)
- [ ] Métrica principal é a correta para o contexto (não CPL quando deveria ser CAC, etc.)
- [ ] Canal separado onde relevante (Comercial vs Digital)
