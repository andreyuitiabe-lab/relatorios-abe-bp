# IA (Lambda) vs Comercial — Hotleads (jun/2026)

> ANALISE.md criado retroativamente (jul/2026) na padronização do repo — detalhes de decisão não registrados na época.

## Pergunta original
Comparar conversão de hotleads abordados pela IA de vendas (Lambda) vs pelo time Comercial humano.

## Decisões de abordagem
- Fonte: `datamart.dtm_seller_conversion_rate` (1 linha/deal Pipedrive)
- Definição de venda Lambda: ver `wiki-bp/pages/fluxo-comercial.md` (seção Lambda — `nm_pptc_tracking_name LIKE '%C0113%'`)

## Estrutura
Padrão template completo: `index.html` + `data.json` + `refresh.py`.

## Queries
| Query | O que faz |
|---|---|
| [lista-upsell-lambda.sql](queries/lista-upsell-lambda.sql) | Lista de upsell trabalhada pelo Lambda |

## Pendências
- [ ] Registrar achados principais (não documentados na entrega original)
