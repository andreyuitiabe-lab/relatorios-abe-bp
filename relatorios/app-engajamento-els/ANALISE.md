# App Engajamento ELS — Google Ads (jun/2026)

> ANALISE.md criado retroativamente (jul/2026) na padronização do repo — detalhes de decisão não registrados na época.

## Pergunta original
Acompanhar o desempenho diário das campanhas de app/engajamento ligadas ao ELS no Google Ads.

## Estrutura
Padrão template completo: `index.html` + `data.json` + `refresh.py` (fonte: `datamart.dtm_analytics_google_ads_funnel`).

## Queries
| Query | O que faz |
|---|---|
| [diario_por_campanha.sql](queries/diario_por_campanha.sql) | Série diária por campanha (spend, cliques, vendas) |

## Pendências
- [ ] Registrar achados principais (não documentados na entrega original)
