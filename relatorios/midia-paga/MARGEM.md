# Margem% para o teto do recomendador — levantamento 2026-09-10

O teto do desenho final (H5) é `margem% × ticket_30d × demand_index`. Este documento fixa a margem% com o que existe no dado, deixando explícito o que é cenário.

## Componentes medidos (BQ + planilha Custos Variáveis 2026)

| Componente | Valor | Fonte |
|---|---|---|
| Reembolso | **−6,5%** do valor cobrado | `financial.fct_charges` abr–set/2026: R$8,6mi refunded (incl. parciais) vs R$123,1mi approved |
| Comissão comercial | **−10,5%** da receita comercial (estável 9,5–11,4% em 2026) | planilha comissão diária ÷ receita `bl_is_commercial_channel` |
| Share comercial na receita | 37–64% no total; para venda **marginal de mídia digital** assumido ~25–35% (checkout abandonado recuperado) | fct_transactions 2026 + análise freemium 10/09 |
| Gross-up de spend | 1,1383 (entra no CUSTO, não na margem) | wiki metricas-referencia |

## Componentes NÃO medidos (pedir ao financeiro)

1. **Impostos sobre receita + taxas de gateway** — cenário 12–18%
2. **Custo unitário de produto físico** (livros/coleções, ticket R$1.000–1.200) — cenário 15–25% do ticket
3. Custo marginal de CRM/infra por venda — imaterial (<1%)

## Margem marginal por classe (cenários)

| Classe | Cálculo | Faixa | Central |
|---|---|---|---|
| **Assinatura digital** (venda self-checkout de mídia) | 1 − 6,5% reemb − ~3% comissão efetiva (10,5%×30%) − 12–18% impostos/gateway | 0,70–0,80 | **0,75** |
| **Produto físico** (livro/coleção) | idem − 15–25% custo+frete | 0,45–0,62 | **0,55** |
| **Blend campanhas [VENDA] atuais** (mix ~80/20 digital/físico) | ponderado | 0,65–0,76 | **0,71** |

## Implicação imediata (com b=0,70, β EWMA7 = 64, spend atual R$183k/dia)

- Margem breakeven implícita no nível atual: **85%** → acima de qualquer cenário plausível.
- Ótimo com m=0,75 (digital): **I* ≈ R$122k/dia** — o portfólio opera ~50% acima do ponto onde a margem começa a ser perdida.
- Ótimo com m=0,71 (blend): **I* ≈ R$102k/dia**.
- Teto de receita (mCAC=receita): R$312–319k/dia — ainda longe; o problema não é prejuízo bruto, é margem marginal negativa entre R$~120k e R$486k.

⚠️ Tudo sobre receita **atribuída** (pixel BP) e agregado de portfólio — campanhas individuais têm ótimos próprios (o recomendador trata). Confirmar impostos/gateway e custo físico com o financeiro transforma as faixas em ponto.
