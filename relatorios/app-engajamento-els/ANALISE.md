# App Engajamento ELS — Google Ads (jun/2026)

> ANALISE.md criado retroativamente (jul/2026) na padronização do repo — detalhes de decisão não registrados na época.

## Pergunta original
Acompanhar o desempenho diário das campanhas de app/engajamento ligadas ao ELS no Google Ads.

## Estrutura
Padrão template completo: `index.html` + `data.json` + `refresh.py` (fonte: `datamart.dtm_analytics_google_ads_funnel`).

## Metodologia (ago/2026)

[metodologia.html](metodologia.html) — diagramas do pipeline de medição das campanhas `[APP]`: as três fontes que não se falam (Firebase, Guru, planilha Adveronix), a cadeia de chaves `id_pseudo_user → id_user → id_subscription → id_transaction` com os três pontos de vazamento, e a reconciliação teto/piso (7.092 conversões reportadas pelo Google vs 3.374 installs atribuídos pelo Firebase).

Pontos que a metodologia deixa explícitos:
- **O funil de cadastro subconta.** O trio de telas `welcome → signup_email → signup_password` não cobre `ios_signup`, `signup`, `signup_form` nem `signup_complete` — âncora mais defensável para "conta criada" é `masterdata.dim_user.dt_created_at`.
- **A receita fecha pela assinatura**, então perde vitalício e compra avulsa (`id_subscription IS NULL`).
- **O ROAS é teto**: ≥ 671 dos 3.374 devices já tinham conta antes do install, logo parte da receita da janela aconteceria sem a campanha.

## Cobertura de atribuição (18/06–13/08/2026)

| SO | first_open | com `medium='cpc'` | com token `[APP]` |
|---|---:|---:|---:|
| Android | 44.203 | 7.985 (18,1%) | 2.274 |
| iOS | 38.460 | 1.731 (4,5%) | 1.089 |

**Meta Ads é o buraco real, não o iOS.** No período o Firebase registrou **1** `first_open` com `apps.facebook.com` — a atribuição de install via Meta não existe sem deep link com UTM ou MMP. O iOS tem atribuição, ~4× pior que o Android.

## Queries
| Query | O que faz |
|---|---|
| [diario_por_campanha.sql](queries/diario_por_campanha.sql) | Série diária por campanha (spend, cliques, vendas) |
| [atribuicao_installs_app.sql](queries/atribuicao_installs_app.sql) | Universo atribuído: devices com `first_open` em campanha `[APP]` |
| [ponte_device_conta.sql](queries/ponte_device_conta.sql) | Ponte `id_pseudo_user → id_user` (habilita a receita) |
| [cobertura_atribuicao_por_so.sql](queries/cobertura_atribuicao_por_so.sql) | Cobertura de atribuição por SO — fact-check de "iOS sem atribuição" |

## Pendências
- [ ] Registrar achados principais da entrega original de jun/2026 (não documentados na época)
- [ ] Trocar a âncora de "conta criada" para `dim_user.dt_created_at` e remedir o funil
- [ ] Refazer a receita por `id_gateway_customer` em vez de `id_subscription`
- [ ] Acompanhar a implementação de deep link + UTM pedida ao time de Tech (doc no Notion: *[Tech] Rastreio de origem de campanha no App*)
