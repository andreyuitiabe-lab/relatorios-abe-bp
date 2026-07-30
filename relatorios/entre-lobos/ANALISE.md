# Análise: ELB26 (relançamento Entre Lobos) — Públicos-semente para Lookalike

**Data:** 2026-07-30
**Status:** estudo concluído; exports de listas pendentes de decisão
**Relatório:** [index.html](index.html) (template padrão: `data.json` + `refresh.py`)
**Contexto:** ELB26 em aquecimento desde 14/07/2026 (82,6k leads até 30/07, acelerando); venda ainda não abriu.
Original: ELB (mai–jun/2022). Houve também relançamento ELB24 (36,7k leads, jun–dez/2024).
Listas com PII saem fora do repo.

---

## Pergunta original

Replicar para o relançamento do Entre Lobos o estudo de públicos do ELS, para gerar sementes
de lookalike (LKL) para a fase de venda do ELB26.

## Base de aprendizado (testes de segmentação ELS, fase de venda)

| Semente | ROAS | Lição |
|---|---|---|
| "Sinal forte" | 2,13 | melhor teste |
| LKL compradores ELS 1% | 1,90 | comprador da campanha é semente forte |
| LKL viewers do doc | 1,68 | CPA maior, ticket maior (R$344) |
| LKL 1% genérico | 0,98 | semente genérica não funciona |
| Remarketing "Viu o Doc" | 0 vendas | viewer em geral já comprou (96% assistem pós-compra) |

## Decisões de abordagem

- Compradores ELB22: união `tracking_name ∪ utm_campaign ∪ utm_content` com fronteira de
  não-letra (`(^|[^a-z])elb([^a-z0-9]|$)|entre[-_ ]?lobos`), janela 17/05→31/07/2022,
  `approved` + `bl_is_renovation=FALSE`; e-mail via `dim_contact` (`id_gateway_customer`)
- Viewers: `obt_kafka__view_sessions`, `nm_playlist LIKE 'Entre Lobos%'` (série + episódios), ≥5min
- Compradores ELS incluídos como semente candidata por proximidade temática (segurança pública)
- Perfil: decil (`dtm_purchasing_power`), cartão (`int_credit_card_level`), gênero inferido (`dim_user`)

## Resultado — sementes dimensionadas e perfiladas

| Semente | N | Decil | % decil7+ | % cartão premium | % masc |
|---|---|---|---|---|---|
| 1. Compradores ELB 2022 | 18.538 | **5,63** | **41,2%** | 53,8% | 74,6% |
| 2. Viewers ELB (todos, ≥5min) | 462.553 | 5,30 | 36,6% | 49,8% | 73,1% |
| 3. Viewers ELB últimos 12m | 59.977 | 5,17 | 34,2% | 51,6% | 73,6% |
| 4. Viewers ELB ≥1h | 295.941 | 5,33 | 37,0% | 50,0% | 74,8% |
| 5. Compradores ELS | 35.143 | 5,47 | 38,3% | **57,0%** | 68,7% |
| 6. Compradores ELS ∩ viewers ELB | 4.826 | 5,46 | 38,9% | **60,2%** | **76,8%** |

Sub-tamanhos úteis: viewers decil7+ = 135k; viewers cartão premium = 184k;
compradores ELB22 decil7+ = 6,4k.

## IQL integrado (30/07)

Seção de qualidade dos leads adicionada ao relatório, lendo `bp-staging.dbt_abe.fct_lead_iql`
(agregados por faixa apenas — governança D20). 59,5k leads escorados até 29/07: **21,3% A+/A**
(12.657). O % A+/A diário caiu de ~50% (dia 1, base quente) para platô de ~20% com a mídia escalada.
Os leads A+/A entraram como **semente nº 7** ("sinal forte" da própria campanha, recência máxima) —
perfil de renda menor por construção (decil 5,03 / 38% cartão premium): o IQL qualifica por
probabilidade de conversão, não por renda. ⚠️ Pré-merge da MR !2426 o fct atualiza só com dbt run
manual (ver `wiki-bp/iql.md`).

## Achados

- **Compradores ELB22 são a semente de melhor perfil** (decil 5,63 / 41,2% decil7+ — acima até
  dos compradores ELS) e tamanho ideal para seed Meta (18,5k). Risco: recência (compra há 4 anos).
- **13,7% dos compradores ELS assistiram Entre Lobos** — afinidade temática real. O overlap
  (4,8k) é o segmento mais premium (60,2% cartão) e mais masculino (76,8%).
- Viewers da série têm perfil ~= base (decil 5,30) — semente de volume, não de qualidade.
  Recorte de qualidade: viewers decil7+ (135k) reproduz a lógica do "sinal forte" do ELS.
- Público ELB é o mais masculino já medido (73–77% vs 68,5% ELS).

## Recomendação de sementes para a fase [VENDA] do ELB26

1. **LKL compradores ELB22** (18,5k) — análogo direto do que deu ROAS 1,90 no ELS
2. **LKL viewers decil7+ / cartão premium** (135k/184k) — análogo do "sinal forte" (ROAS 2,13)
3. **LKL compradores ELS** (35,1k) — semente temática já validada, sem custo de montagem
4. Opcional: overlap ELS∩ELB (4,8k) — pequeno mas premium; testar com spend marginal
5. **Não usar viewers ELB para remarketing de venda** — lição ELS: viewer em geral já é membro

## Pendências / próximos passos

- [ ] Decidir quais sementes exportar (listas de e-mail hasheadas para upload no Meta — fora do repo)
- [ ] Quando a venda abrir: acompanhar ROAS por semente vs Advantage amplo (benchmark ELS 1,40)
- [ ] Proxy de qualidade dos 51k leads ELB26 por criativo (metodologia `relatorios/campanhas/`)

## Queries

| Arquivo | O quê |
|---|---|
| [queries/elb26_sementes_lookalike.sql](queries/elb26_sementes_lookalike.sql) | Dimensiona e perfila as 6 sementes candidatas |

## Wiki atualizada

- (pendente) criar página `wiki-brasil-paralelo/pages/entre-lobos.md` se o tema virar recorrente
