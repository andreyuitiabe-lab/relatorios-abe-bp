# Pesquisa de Qualificação de Leads — EVG (Brasil Evangélico)

**Período:** 23/mai → 12/jun/2026 · **Autor:** André Abe
**Base:** `dtm_analytics_lead_conversion` (tag EVG) + `dtm_analytics_facebook_ads_funnel` + GA4

---

## TL;DR para a reunião

- A pesquisa **prediz compra** com força: lead score 5–6 converte **~5%** vs 0,8% do score 0 (separação de 6x).
- O CPL (custo) **não** prediz qualidade (correlação +0,18). O formulário prediz (+0,46). **Otimizar por CPL puro está cego para qualidade.**
- A pesquisa **custa ~R$10–15k de receita** (fricção, –11,5% de completion por 3 perguntas) e derruba o **RPV/visitante de R$1,70 → R$1,54 (–9%)**.
- **Para dar ROI, precisamos melhorar a eficiência de mídia em ~20%** (realocar budget dos piores anúncios para os melhores). É alcançável — os piores anúncios têm CPA 4–8x os melhores.
- **A pesquisa só se paga se AGIRMOS sobre ela.** Coletar sem otimizar = só custo.

---

## 1. Dados da pesquisa de qualificação compilados

35.871 cadastros · 42% responderam o formulário · 404 compradores (1,13%).

### Relação com a BP — maior preditor isolado
| Resposta | Cadastros | Tx compra | CPL ideal* |
|---|---:|---:|---:|
| Assino hoje | 531 | 3,95% | R$10,49 |
| Já assinei no passado | 1.058 | 2,65% | R$7,04 |
| Já ouvi falar, nunca assisti | 1.799 | 1,17% | R$3,11 |
| Consumo conteúdo gratuito | 3.400 | 0,85% | R$2,26 |
| Nunca ouvi falar | 424 | 0,24% | R$0,64 |

### Renda — segundo preditor (monotônico)
| Faixa | Tx compra | CPL ideal* |
|---|---:|---:|
| Acima de R$20.000 | 7,02% | R$18,64 |
| R$10–20.000 | 6,37% | R$16,91 |
| R$5–10.000 | 2,88% | R$7,65 |
| Até R$5.000 | 1,37% | R$3,64 |
| Até R$2.000 | 0,85% | R$2,26 |
| Prefiro não informar | 1,01% | R$2,68 |

\* CPL ideal = mantém o mesmo CAC do cadastro base (R$3 @ tx média 1,13%).

---

## 2. Combinação de streamings × conversão

Ter **"Brasil Paralelo"** entre os streamings é o sinal mais forte. Acumular muitos serviços **sem** BP é o pior perfil (entretenimento mainstream).

| Perfil de streaming | Cadastros | Tx compra |
|---|---:|---:|
| Tem BP + 2 serviços | 269 | **4,09%** |
| Tem BP + 3+ serviços | 356 | 3,65% |
| Tem BP + 1 serviço | 450 | 2,00% |
| Sem BP, 2 serviços | 1.050 | 1,52% |
| Sem BP, 1 serviço | 3.165 | 1,48% |
| Nenhum streaming | 3.809 | 0,81% |
| **Sem BP, 3+ serviços** | 841 | **0,71%** ← pior |

**Combos individuais de maior conversão (vol ≥20):** Brasil Paralelo+Netflix (4,35%) · Netflix+Plataformas educacionais (3,85%) · Prime Video sozinho (2,43%).

---

## 3. Conversão ao longo do tempo

| Semana (cadastro) | Cadastros | Taxa resposta | Tx compra |
|---|---:|---:|---:|
| 18/mai | 2.907 | 5,6% | 1,03% |
| 25/mai | 11.786 | 29,6% | 1,21% |
| 01/jun | 14.569 | 52,0% | 1,39% |
| 08/jun | 6.622 | 64,7% | 0,44%¹ |

¹ Queda aparente é **maturação**, não real: leads recentes ainda não tiveram tempo de comprar. A taxa real desta coorte deve subir nas próximas semanas.

**Observação:** a taxa de resposta subiu de 5,6% → 64,7% — a pesquisa foi ganhando peso/proeminência ao longo da campanha. Útil para comparar fases antes/depois.

---

## 4. Faixas de CPL ideal por tipo de lead

Base: hoje pagamos **R$3 por cadastro** otimizando por cadastro (tx média 1,13%). O CPL ideal por faixa mantém o **mesmo CAC**:

| Faixa de lead | Tx compra | **CPL ideal** |
|---|---:|---:|
| Lead score 5–6 (renda alta + já-membro) | 4,86% | **R$12,90** |
| Lead score 3–4 | 2,71% | R$7,19 |
| Lead score 2 | 2,04% | R$5,42 |
| Lead score 1 | 1,13% | R$3,00 |
| Lead score 0 | 0,79% | R$2,10 |
| Renda 15k+ | 6,50% | R$17,26 |
| Streaming inclui BP | 4,09% | R$10,86 |
| "Nunca ouvi falar" | 0,24% | R$0,64 |
| Muitos streamings sem BP | 0,71% | R$1,88 |

**Leitura:** vale pagar **4–6x mais** por um lead score 5–6 do que por um lead score 0. Hoje pagamos o mesmo CPL para os dois — desperdício.

---

## 5. Quanto perdemos com a pesquisa (referência –4% por pergunta)

Pesquisa EVG = 3 perguntas → **–11,5%** de completion (composto, 0,96³).

| Métrica | Com pesquisa | Sem pesquisa (est.) |
|---|---:|---:|
| Cadastros | 35.871 | 40.544 |
| Leads perdidos pela fricção | — | **4.673** |
| Receita perdida | — | **R$10,6k – R$15,2k** |
| **RPV / visitante** | **R$1,54** | R$1,70 (**–9%**) |
| **RPV / lead** | **R$4,10** | R$4,01 (**+2%**) |

**Insight-chave:** a pesquisa **reduz o RPV por visitante** (fricção no topo) mas **aumenta o RPV por lead** (qualidade) — porque os leads que abandonam são desproporcionalmente de baixa qualidade. O problema não é a qualidade do que sobra; é o **volume que some**.

---

## 6. Respostas diretas ao gestor

**Quanto perdemos de receita ao colocar a pesquisa?**
≈ **R$10–15k** no período (7–10% da receita EVG de R$147k), via ~4,7k leads a menos.

**Diminuímos o RPV depois da pesquisa?**
Sim, **por visitante: –9%** (R$1,70 → R$1,54). Mas **por lead subiu +2%** — a base ficou mais qualificada.

**Que número precisamos buscar para dar ROI?**
A pesquisa custa ~R$15k. O investimento Facebook foi R$77,4k (CAC R$192). **Precisamos melhorar a eficiência de mídia em ≥20%** (≈ baixar o CAC de R$192 → ~R$155) realocando budget. Como os piores anúncios (AD28, AD45) têm CPA R$572–908 vs R$105–145 dos melhores, **cortar/realocar 15–20% do budget dos piores já cobre o custo da pesquisa.**

---

## 7. Recomendações

1. **Trocar a métrica de otimização** de CPL → **CPLQ (custo por lead qualificado, score ≥3).**
2. **Realimentar o Meta com evento de valor** (passar score/renda como valor do evento) em vez de cadastro genérico — algoritmo busca quem se parece com comprador.
3. **Aplicar CPL ideal por faixa** (tabela seção 4) como teto de lance/avaliação por público.
4. **Cortar AD28 e AD45**, realocar para o padrão AD21/AD08.
5. **Reduzir fricção:** testar pesquisa de 2 perguntas (relação BP + renda — os 2 maiores preditores) em vez de 3, recuperando ~4pp de completion sem perder poder preditivo.
6. **Validar com A/B test:** otimização por cadastro vs por lead-qualificado, mesmo budget, comparar **CAC** (não CPL) pós-maturação.

---

## Validação estatística

- Lead score (relação BP + renda): **monotônico**, separação 6x entre topo e base.
- Correlação anúncio-nível com tx de compra: CPL **+0,18** · % qualificado **+0,46** (formulário ~2,5x mais preditivo que CPL).
- Razão de conversão respondente/cadastro: 1,25x bruta, 1,12x pós-cadastro (descontando atribuição inflada por compra simultânea).

**Caveat:** `qt_vendas` atribui por last-click e inclui compras simultâneas/anteriores ao cadastro (~70% das vendas de respondentes). Para medir captação incremental real, filtrar `days_to_purchase >= 1`.
