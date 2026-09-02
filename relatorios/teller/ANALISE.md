# Teller — Análise de vendas, perfil e engajamento (2026 YTD)

## Pergunta original
Quanto vendemos de Teller por mês em 2026; qual o perfil dos compradores (membro / ex-membro / não-membro); se o Teller serve melhor para **aquisição**, **upsell** ou **recuperação**; e como está o **engajamento** de quem ouve e quem são essas pessoas.

## Decisões de abordagem
- **Duas lentes de "venda Teller", separadas** (como o produto opera):
  - **Produto Teller** — `nm_gateway_plan = 'teller'` (Teller **standalone**). Decisão do time: **NÃO** incluir premium-teller nem bundles base+Teller do Comercial (BP Select+Teller, Travessia+Teller etc.) — nesses o Teller é sweetener e o produto principal é outro.
  - **Campanha Teller** — `nm_pptc_utm_campaign` com tag `TLR`/`TLR12`; vende qualquer produto. As próprias tags separam `aquisicao`, `membros_crosssell` e `recuperacao`.
- Comparação de escopo (2026): `nm_gateway_plan='teller'` = 1.464 clientes; incluir premium-teller = 1.915; usar `nm_gateway_product LIKE '%teller%'` (com bundles) = 2.346. Escopo escolhido = **só `teller`**.
- **Perfil do comprador** classificado *no momento da compra*: membro (acesso ativo não-Teller OU vitalício anterior), ex-membro (teve assinatura, já expirada), não-membro (nunca teve). Vitalícios entram como membership permanente (têm `id_subscription IS NULL`).
- **Engajamento**: `events.fct_mixpanel__teller_media_playback_events`. Descoberta-chave: `user_id` = `dim_user.id_user` (17.713/17.714 casam) e `media_id` = `dim_teller__audiobooks.id_book` → dá pra cruzar escuta com membership e catálogo.
- Filtro padrão sempre: `nm_status='approved' AND bl_is_renovation=FALSE`.

## Achados principais
- **Volume 2026 (produto = Teller standalone):** ~1,5 mil transações, **estável ~120–400/mês** (jan e abr os picos). Receita ~R$ 320k YTD.
- **Campanha TLR/TLR12:** ~1,85 mil transações. ⚠️ **Recortadas pelo perfil REAL do comprador** (não pelo nome do UTM, que reflete só a intenção do Marketing): **51% membros (938), 26% não-membros (470), 24% ex-membros (446)**. Ou seja, as campanhas TLR são majoritariamente **cross-sell/reativação** — aquisição de novo cliente é minoria (26%), apesar de a maioria das peças ser nomeada como "aquisição".
- **Perfil dos compradores (Teller standalone, dedup por cliente — 1.464):** **48% membros (697), 32% não-membros (472), 20% ex-membros (295)**. Quase tudo digital (só ~8% via Comercial).
- **Aquisição vs upsell vs recuperação:**
  - **Upsell/cross-sell (membros):** maior fatia (48%), majoritariamente digital.
  - **Recuperação (ex-membros):** 20% do standalone; mais forte quando se olha o Comercial (bundles Premium+Teller, fora do escopo) e as campanhas `tlr_recuperacao` de alto ticket.
  - **Aquisição pura (não-membros):** 32%, MAS **só 7 de 472 não-membros (1,5%) compraram membership plena depois** → Teller **não** está funcionando como funil de entrada para o ecossistema BP. Ressalva: janela de conversão de não-membro é ~421 dias e boa parte comprou há poucos meses — reavaliar no fim de 2026.
- **Não-membros engajam, mas não sobem:** dos 472 não-membros, **87% ouviram algo e 76% ouviram em 2+ dias distintos** — audiência quente. O gargalo é ausência de rota de upgrade Teller→BP, não o produto.
- **Venda redundante (alerta):** dos 699 compradores-membros, **~236 estavam em Premium/Black** — planos que **já incluem Teller** — e o padrão **se repete todo mês** (não é resíduo de pré-inclusão). Para `good`/`supporter` (431) que querem audiolivro, o caminho de maior valor é **upsell para Premium**, não Teller avulso.
- **Teller não "pega carona" nas vendas da empresa (correlação):** vendas diárias Teller × GBB = **−0,23** (semanal −0,49); Teller × empresa = −0,14; controle GBB × empresa = +0,81. Nos maiores dias de venda da empresa o Teller vende quase nada; os picos do Teller são dias de campanha TLR própria. É **elástico à mídia própria**, levemente **contracíclico** ao push geral. (Ressalva: 6 meses; parte é competição por atenção/budget, não causalidade.)
- **Engajamento:** ~6,5–8,3 mil ouvintes/mês, estável; ~40k playbacks/mês. **82% dos compradores standalone efetivamente ouvem** (1.198/1.467) — ótima ativação.
- **Quem ouve:** dos ~17,7 mil ouvintes, **71% são membros plenos ativos**, 26% só-Teller, 3% sem assinatura ativa → Teller é hoje sobretudo um **benefício consumido por membros** (está incluído em básico/premium).
- **Conteúdo:** clássico/filosófico/católico. Top: *Críton* (Platão), *Sobre a Brevidade da Vida* (Sêneca), *Confissões* (Santo Agostinho), *Padre Brown* (Chesterton), *Revolução dos Bichos* (Orwell). Gêneros líderes: Filosofia, Religião, Ficção, Desenvolvimento Pessoal.

## Conclusão de negócio
Teller hoje é **mais retenção/upsell e reativação do que aquisição**. Gera receita incremental de membros e ex-membros (Premium+Teller do Comercial recupera ex-membros; campanhas de alto ticket recuperam winback), e tem alta ativação de escuta. Como **canal de aquisição de novos membros** o desempenho é fraco: quase nenhum não-membro sobe para membership plena (reavaliar com janela maior).

## Entregáveis
- **`index.html` + `data.json` + `refresh.py`** — relatório HTML no padrão do portal (dados externos; `python refresh.py --push` reatualiza). Card adicionado em `relatorios/index.html` (seção Base & Produtos).
- `Teller_analise_2026.xlsx` — planilha consolidada (13 abas: README, vendas produto/mês, vendas campanha/mês, perfil, canal×perfil, **tier_membros**, **retencao_nao_membros**, **correlacao_vendas**, engajamento/mês, **ouvintes_perfil**, top audiolivros, gêneros, **transações granulares**).
- `transacoes_teller_2026.csv` — transação a transação.
- `queries/analise_teller.sql` — queries A–D. `queries/export_transacoes.sql` — base granular.

## Pendências / próximos passos
- Reavaliar conversão de não-membros no fim de 2026 (janela ~421 dias).
- Medir profundidade de escuta (segundos ouvidos / % do audiolivro) — hoje medimos playbacks e ouvintes, não tempo. `vl_watch`/checkpoints não existem nesta tabela Mixpanel; avaliar `dim_teller__audiobooks.vl_duration_second` vs eventos de progresso.
- LTV do comprador Premium+Teller vs Teller standalone (não calculado).

## Wiki atualizada
- `wiki-brasil-paralelo/pages/produtos.md` — seção Teller (planos, footprint de vendas, tabelas de engajamento).
- `wiki-bp/pages/bq-planos.md` — mapeamento dos planos `-teller`.
- `wiki-bp/pages/bq-acesso.md` — tabelas `events.fct_mixpanel__teller_*` e joins (`user_id`=`id_user`, `media_id`=`id_book`).

---

# Recorte 2: Não-membros — universo, upsell e receita (ago/2026)

## Pergunta original
Bárbara Olivieri (24/08/2026): *"pessoas que nunca foram Membros da BP e tem o Teller: quantas temos, quantas fizeram upsell, qual a receita que veio do upsell para essas pessoas. Geral e por mês esse ano."*

## Decisões de abordagem (o que mudou vs. o Recorte 1)
- **Janela = histórico completo (set/2024 → hoje), não 2026 YTD.** O Recorte 1 olhou só 2026 e por isso mediu conversão de gente com poucos meses de maturação. O cohort que importa (lançamento set/2025) estava quase todo fora daquela janela.
- **Resolução por `id_person` (identity graph), não `id_gateway_customer`.** 3.058 dos 20.179 compradores Teller têm e-mail compartilhado com outro `id_gateway_customer`. Por cadastro o universo de "nunca-membro" infla **27%** (4.492 vs 3.285) — gente que já era membro por outra conta.
- **Correção de gotcha de plano.** O Recorte 1 definia membership como `nm_gateway_plan NOT LIKE '%teller%'`, o que excluía indevidamente os combos `essencial-unesco-...-teller` (422 subs), `basico-front-...-teller` (323) e `originais-teller` (2) — todos **incluem** acesso à plataforma. O único plano que dá só Teller é o literal `teller`.
- **Upsell = compra nova (não-renovação) de produto ≠ Teller em data posterior ao dia da compra do Teller.** D0 (mesmo dia) fica fora: é order bump do mesmo checkout (37 pessoas, R$ 14.137).

## Achados principais

**Geral (histórico set/2024 → 24/08/2026)**

| Métrica | Valor |
|---|---|
| Compradores de Teller standalone | 20.143 pessoas |
| **Nunca foram membros da BP** | **3.285 (16,3%)** |
| **Fizeram upsell** | **342 (10,4%)** |
| **Receita do upsell** | **R$ 350.879** |
| Receita por convertido | R$ 1.026 |
| Receita por não-membro na base | R$ 106,81 |
| Viraram membro pleno (assinatura/vitalício) | 368 (11,2%) |

**A taxa de 1,5% do Recorte 1 era artefato de janela, não de identidade.** Recalculado pelo método antigo (por `id_gateway_customer`) no histórico completo dá **11,0%** — praticamente o mesmo 10,4%. O que mudou o número foi olhar cohorts maduros, não a resolução de identidade. Maturação por cohort:

| Cohort (mês da compra Teller) | Não-membros | Upsell | Taxa | Dias de maturação |
|---|---|---|---|---|
| 2025-09 (lançamento) | 2.033 | 261 | **12,8%** | 328 |
| 2025-10 | 451 | 42 | 9,3% | 297 |
| 2025-11 | 90 | 8 | 8,9% | 267 |
| 2025-12 | 129 | 9 | 7,0% | 236 |
| 2026-01 a 2026-08 | 546 | 17 | 3,1% | 1–205 |

**Receita de upsell realizada por mês (é o "por mês esse ano")** — atenção: quase toda vem de cohorts de **2025**, não de quem entrou em 2026.

| Mês do upsell | Pessoas | Receita | Ticket médio | Dias médios pós-Teller |
|---|---|---|---|---|
| 2026-01 | 10 | R$ 5.336 | 485 | 90 |
| 2026-02 | 20 | R$ 9.750 | 406 | 140 |
| 2026-03 | 13 | R$ 14.164 | 1.012 | 158 |
| 2026-04 | 5 | R$ 2.224 | 445 | 148 |
| 2026-05 | 62 | R$ 74.808 | 959 | 228 |
| 2026-06 | 45 | R$ 59.968 | 983 | 214 |
| 2026-07 | 20 | R$ 30.209 | 1.439 | 241 |
| 2026-08 (até 24) | 20 | R$ 25.240 | 1.097 | 296 |
| **2026 YTD** | **179** | **R$ 221.698** | — | — |

Para comparação, o **cohort 2026** (546 não-membros que entraram no Teller este ano) gerou só 17 upsells e **R$ 23.750** — ainda imaturo.

**O upsell não é para assinatura básica — é high-ticket via Comercial.** Produtos vendidos (histórico completo, R$ 350.879):

| Produto | Tx | Pessoas | Receita | % | Ticket médio | % Comercial | Receita 2026 |
|---|---|---|---|---|---|---|---|
| Clube do Livro (+ e-books/análises) | 126 | 103 | R$ 136.550 | 38,9% | 1.084 | 47% | R$ 136.550 |
| Vitalício Black | 27 | 26 | R$ 104.382 | 29,7% | 3.866 | **100%** | R$ 26.437 |
| Assinatura Premium GBB (`best`) | 83 | 83 | R$ 25.127 | 7,2% | 303 | 20% | R$ 7.055 |
| Assinatura Black | 15 | 15 | R$ 21.283 | 6,1% | 1.419 | 80% | R$ 9.871 |
| Livro Odisseia — Colecionador | 9 | 9 | R$ 11.700 | 3,3% | 1.300 | 11% | R$ 11.700 |
| Vitalício Básico | 8 | 8 | R$ 9.949 | 2,8% | 1.244 | 75% | R$ 8.556 |
| Assinatura Básico (`good`) | 50 | 50 | R$ 9.908 | 2,8% | 198 | 26% | R$ 4.841 |
| Mecenas | 7 | 7 | R$ 8.443 | 2,4% | 1.206 | 57% | R$ 1.975 |
| Assinatura Apoiador | 64 | 62 | R$ 6.304 | 1,8% | 98 | 9% | R$ 1.985 |
| Vitalício Premium GBB | 4 | 4 | R$ 6.204 | 1,8% | 1.551 | 50% | R$ 6.204 |
| Vitalício Apoiador | 5 | 5 | R$ 6.012 | 1,7% | 1.202 | 20% | R$ 3.324 |
| Outros (combos, BP Clube, guias) | 16 | 13 | R$ 2.998 | 0,9% | 187 | 0% | R$ 2.878 |
| Certificação completa (Geopolítica) | 1 | 1 | R$ 1.188 | 0,3% | 1.188 | 0% | R$ 0 |
| Funil / entrada de certificação | 18 | 16 | R$ 556 | 0,2% | 31 | 0% | R$ 47 |
| Assinatura Intermediário | 1 | 1 | R$ 276 | 0,1% | 276 | 100% | R$ 276 |

Consolidando por natureza: **produto avulso high-ticket** (Clube do Livro + Livro Odisseia) = **R$ 148,3k (42%)**; **vitalício** = R$ 126,5k (36%); **assinatura recorrente** = R$ 62,9k (18%); Mecenas R$ 8,4k; certificações R$ 1,7k.

**Dois motores distintos, em fases distintas.** O Vitalício Black (26 pessoas, ticket R$ 3.866, **100% Comercial**) é o motor de 2025 — só R$ 26,4k dos R$ 104,4k caíram em 2026. O Clube do Livro é o motor de 2026 e responde por **100% da sua receita neste ano**. Ou seja, o que monetiza o não-membro Teller é sempre a **oferta high-ticket da vez**, empurrada pelo Comercial — não uma escada de produto estável.

**Produto × mês em 2026** (R$ 221.698):

| Mês | Clube do Livro | Vitalício | Assinatura | Livro Odisseia | Mecenas | Outros | Total |
|---|---|---|---|---|---|---|---|
| jan | — | 3.114 | 1.637 | — | — | 586 | 5.336 |
| fev | — | 3.582 | 5.548 | — | — | 619 | 9.750 |
| mar | — | 10.272 | 3.712 | — | 180 | — | 14.164 |
| abr | — | 1.188 | 1.036 | — | — | — | 2.224 |
| mai | **66.854** | — | 7.322 | — | — | 632 | **74.808** |
| jun | **55.896** | — | 3.594 | — | — | 478 | **59.968** |
| jul | 7.968 | 17.205 | 479 | 3.948 | — | 610 | 30.209 |
| ago (até 24) | 5.832 | 9.160 | 701 | 7.752 | 1.795 | — | 25.240 |

A receita de 2026 é **evento-dirigida, não recorrente**: mai–jun é pré-venda do Clube do Livro (R$ 122,8k = 55% do ano), jul–ago é Livro Odisseia + retomada de vitalício. Assinatura recorrente nunca passa de R$ 7,3k/mês — o não-membro Teller praticamente não assina.

**Escuta quase não prediz upsell.** Taxa por intensidade de escuta: nunca ouviu 8,9% → 1 dia 9,4% → 2–5 dias 11,2% → 6–20 dias 8,6% → 21+ dias 13,5%. Gradiente fraco e não monotônico. O "audiência quente" do Recorte 1 é real como engajamento, mas **não é sinal de propensão a comprar** — não serve para priorizar lista.

**Janela crítica: o Teller é anual e o cohort de lançamento vence agora.** Dos 3.285 não-membros, **2.943 nunca compraram nada além do Teller** e 2.903 têm assinatura ativa hoje. Vencimentos:

| Mês de vencimento | Não-membros sem upsell |
|---|---|
| **2026-09** | **1.768** |
| **2026-10** | **417** |
| 2026-11 a 2027-09 | 673 |

**2.185 pessoas (74% do estoque) vencem nas próximas 8 semanas.** É a janela natural de oferta de upgrade — e, pelo mix acima, o veículo com histórico de conversão é o Comercial com high-ticket.

## Pendências / próximos passos
- **Reavaliar o cohort 2026 em jan/2027** — hoje tem 1–205 dias de maturação; a curva de 2025 mostra que a taxa só estabiliza depois de ~300 dias.
- **Lista acionável dos 2.185 que vencem em set–out/2026** não foi gerada (não foi pedida). A query 5 do `.sql` já isola o grupo.
- Não foi medido o **LTV pós-upsell** (retenção de quem virou membro) nem a taxa de renovação do próprio Teller nesses cohorts.

## Queries
| Arquivo | O que faz |
|---|---|
| [queries/nao_membros_upsell.sql](queries/nao_membros_upsell.sql) | CTEs base + 5 recortes (resumo, mês do upsell, cohort, mix de produto, estoque por vencimento) |

## ⚠️ Ressalva sobre o relatório publicado
O card **"1,5% viraram membros plenos depois"** no `index.html` está correto para o escopo em que foi calculado (compradores de 2026, janela curta, e traz a ressalva dos ~421 dias), mas **lido isoladamente induz a conclusão errada** — no histórico maduro a taxa é ~11%. Não foi alterado: decisão de mexer no relatório publicado fica com o André.

---

# Recorte 3: só quem comprou Teller em 2026 (ago/2026)

Mesmo universo do Recorte 2, restrito a quem **comprou o Teller entre jan e ago/2026** (`params.dt_cohort_ini = '2026-01-01'` na query). Pedido do André em 24/08.

⚠️ **Este recorte mede uma população imatura.** A curva do Recorte 2 mostra que a taxa de upsell só estabiliza depois de ~300 dias, e este grupo tem entre 1 e 205 dias. Os números abaixo são um **piso**, não o resultado final desses cohorts.

## Geral

| Métrica | Valor |
|---|---|
| Compradores de Teller standalone em 2026 | 2.150 |
| **Nunca foram membros da BP** | **546 (25,4%)** |
| **Fizeram upsell** | **17 (3,1%)** |
| **Receita do upsell** | **R$ 23.750** (24 transações) |
| Receita por convertido | R$ 1.397 |
| Receita por não-membro na base | R$ 43,50 |
| Ainda sem nenhum upsell | 529 — dos quais 516 com Teller ativo hoje |

A **proporção de não-membros subiu**: 25,4% dos compradores de 2026, contra 16,3% no histórico. O Teller está atraindo relativamente mais gente de fora da base do que atraía no lançamento — mas o ticket por pessoa ainda é baixo justamente porque quase ninguém teve tempo de converter.

## Por mês da compra do Teller (cohort)

| Mês | Não-membros | Upsell | Taxa | Receita | Dias de maturação |
|---|---|---|---|---|---|
| jan | 77 | 4 | 5,2% | R$ 5.508 | 205 |
| fev | 34 | 0 | 0,0% | — | 177 |
| mar | 23 | 2 | 8,7% | R$ 3.274 | 146 |
| abr | 79 | 3 | 3,8% | R$ 2.434 | 116 |
| mai | 62 | 3 | 4,8% | R$ 4.380 | 85 |
| jun | 76 | 2 | 2,6% | R$ 2.976 | 55 |
| jul | 79 | 3 | 3,8% | R$ 5.179 | 24 |
| ago | 116 | 0 | 0,0% | — | 1 |
| **Total** | **546** | **17** | **3,1%** | **R$ 23.750** | — |

Só jan tem maturação relevante (205 dias) e já está em 5,2% — a caminho dos ~9–13% dos cohorts de 2025 na mesma altura da curva.

## Por mês do upsell

| Mês | Pessoas | Tx | Receita | Ticket | Dias pós-Teller |
|---|---|---|---|---|---|
| abr | 1 | 1 | R$ 276 | 276 | 5 |
| mai | 4 | 6 | R$ 4.726 | 788 | 96 |
| jun | 9 | 12 | R$ 11.651 | 971 | 51 |
| jul | 4 | 4 | R$ 6.379 | 1.595 | 41 |
| ago | 1 | 1 | R$ 719 | 719 | 137 |

## Produtos vendidos

| Produto | Tx | Pessoas | Receita | % | Ticket | % Comercial |
|---|---|---|---|---|---|---|
| Clube do Livro | 14 | 11 | R$ 15.084 | 63,5% | 1.077 | 71% |
| Vitalício Black | 1 | 1 | R$ 2.803 | 11,8% | 2.803 | 100% |
| Vitalício Básico | 2 | 2 | R$ 2.376 | 10,0% | 1.188 | 100% |
| Livro Odisseia | 1 | 1 | R$ 1.200 | 5,1% | 1.200 | 0% |
| Mecenas | 1 | 1 | R$ 719 | 3,0% | 719 | 0% |
| Assinaturas (best/good/better/supporter) | 4 | 4 | R$ 1.126 | 4,7% | 282 | 50% |
| Outros | 1 | 1 | R$ 443 | 1,9% | 443 | 0% |

**O padrão do Recorte 2 se mantém, ainda mais concentrado:** Clube do Livro sozinho é **63,5%** da receita, e high-ticket + vitalício somam **90%**. Assinatura recorrente é R$ 1.126 em oito meses. ⚠️ Base pequena — 17 pessoas — então a leitura por produto é direcional, não estatística.

## O que este recorte muda na conclusão

**A janela de set–out/2026 não é deste grupo.** Como o plano é anual e essas pessoas compraram em 2026, os vencimentos caem quase todos em **2027** (jan/2027 em diante); só 7 vencem em set–out/2026. As 2.185 pessoas da oportunidade imediata são do cohort **set–out/2025** — some se o recorte for restrito a 2026.

Ou seja, os dois recortes respondem a perguntas diferentes:
- **"Quanto o Teller de 2026 já rendeu de upsell?"** → R$ 23.750 (recorte 3), e vai crescer.
- **"Quanto vale um não-membro que entra por Teller?"** → R$ 106,81 por pessoa e 10,4% de conversão (recorte 2), medido em cohorts maduros.
- **"Onde está a oportunidade acionável hoje?"** → cohort 2025, 2.185 pessoas vencendo em set–out (recorte 2).

## Correção aplicada na query
O bloco 3 (cohort) usava `COUNT(*)` sobre o LEFT JOIN com `up`, que tem **uma linha por transação** — quem fez mais de um upsell era contado duas vezes (somava 553 em vez de 546). Corrigido para `COUNT(DISTINCT n.id_person)`. As tabelas dos Recortes 1 e 2 não foram afetadas: vieram de uma versão da CTE já agregada por pessoa.

---

# Recorte 3: Assinantes ativos do Teller × acesso à plataforma BP (26/08/2026)

## Pergunta original
Pedido via Slack (26/08/2026): *"de todos os assinantes do Teller, quantos tem acesso a Brasil Paralelo também?"* — foto de hoje, não histórico.

## Decisões de abordagem
- **Assinante Teller = assinatura PAGA ativa do plano standalone `teller`** (`active`/`wo renewal`, não vencida): 19.914 assinaturas → **19.696 pessoas** (`id_person`). Teller `manual`/`promo` (~8,2k users) ficou **fora**: 93% deles já são membros BP que receberam o Teller incluído no plano — contá-los responderia "sim" trivialmente. Vitalício Teller (74 clientes) também fora (não é assinatura).
- **Acesso BP = assinatura ativa de plano de membership OU vitalício GBB.** Whitelist de planos (`good/better/best/black/supporter/mecenas`, combos `bp-*`/`essencial`/`economico`/`apoiador`/`originais`, `extensao-assinatura-*`, `premium-teller`, `*-teller` combos). **Não** basta `plano ≠ 'teller'`: `dim_subscriptions` tem produtos avulsos como assinatura — Clube do Livro (2.260 dos assinantes Teller!), Travessia (910), cursos (`dialetica-aristoteles`…), `funil-bitcoin`, Livro Odisseia — que não dão acesso à plataforma.
- **Role de membership sem assinatura ativa reportada em linha separada** (864 pessoas): investigado, são quase todas assinaturas `canceled` vencidas há 90d–1a com a role `good/best/supporter` ainda em `arr_roles` → role residual, não acesso confiável. Fica fora do número principal.
- `bl_has_platform_access` é TRUE em 100% das assinaturas ativas — não serve para discriminar.

## Achados principais

| Acesso BP hoje | Pessoas | % |
|---|---|---|
| **Com assinatura/vitalício BP ativo** | **11.049** | **56,1%** |
| — Vitalício | 3.882 | 19,7% |
| — Básico/Essencial | 3.210 | 16,3% |
| — Premium | 2.296 | 11,7% |
| — Apoiador/Econômico | 1.022 | 5,2% |
| — Intermediário | 278 | 1,4% |
| — Black | 245 | 1,2% |
| — Mecenas | 77 | 0,4% |
| — outros planos membership | 39 | 0,2% |
| Só role residual (assinatura vencida) | 864 | 4,4% |
| **Só Teller (sem acesso BP)** | **7.783** | **39,5%** |
| **Total assinantes Teller pagos ativos** | **19.696** | 100% |

- Resposta curta: **~11 mil dos 19,7 mil assinantes do Teller (56%) também têm acesso à BP**; **7,8 mil (40%) têm só o Teller**. Teto de 60% se contar a role residual.
- Coerente com o Recorte 1 (48% membros + parte dos ex-membros que voltaram) e com o Recorte 2 (o "só Teller" de hoje ≈ 2.943 nunca-membros sem upsell + ex-membros que não renovaram).
- Lente alternativa (plataforma, por role): 201.883 users têm a role `teller`, 94% com role de membership — porque Teller está incluído em básico/premium. Não é a pergunta feita.

## Pendências
- `queries/nao_membros_upsell.sql` (Recorte 2) define membership como "qualquer plano ≠ teller" em `dim_subscriptions` — inclui CDL/Travessia/cursos. Impacto pequeno (a maioria desses produtos é comprada depois do Teller), mas vale alinhar à whitelist se for rerodado.

## Queries
| Arquivo | O quê |
|---|---|
| [queries/assinantes_teller_x_acesso_bp.sql](queries/assinantes_teller_x_acesso_bp.sql) | Tabela acima (✅ rodou 26/08/2026) |

## Wiki atualizada
- `bq-regras.md` — Gotchas Teller: whitelist de membership, `bl_has_platform_access` inútil, `COALESCE(nm_gateway_plan, nm_plan)`, vitalícios em `dim_subscriptions`, Teller manual/promo, role residual.
- `bq-planos.md` — assinatura-fantasma estendida (Travessia, cursos, funil, bp-clube, guia-analises).
- `bq-schema-core.md` / `bq-schema-extra.md` — `bl_has_platform_access` e role residual em `arr_roles`.
- `metricas-referencia.md` + `produtos.md` — bloco "Teller × acesso BP".

---

# Recorte 4: Lista — renovantes de set/2026 com renovação automática desativada (26/08/2026)

## Pergunta original
Pedido (26/08/2026): *"Membros renovantes do Teller de Setembro com renovação automática desativada"*. Lista nominal para ação de retenção antes do vencimento.

## Decisões de abordagem
- Universo = assinatura **paga** do plano standalone `teller` (mesma decisão dos recortes anteriores: premium-teller e bundles fora), `nm_status = 'wo renewal'` (renovação automática desligada, acesso ainda ativo) e `dt_expires_in` em set/2026. 1 linha por pessoa (`id_person`).
- **Sem exclusões de Comercial** (é lista de retenção, não de prospecção): Mecenas/ex-Mecenas, abordagem Zenvia 7d e deal Pipedrive aberto vão como **flags**. Só a blacklist CRM (opt-out) foi removida — aplicada localmente via planilha Drive.
- Enriquecimento: `nm_acesso_bp` (whitelist de membership do Recorte 3 — quem é "só Teller" perde tudo ao não renovar), escuta no app (Mixpanel, 90d + última escuta histórica), forma de pagamento e canal da última cobrança, investido total.

## Achados principais
- **818 pessoas** (819 assinaturas → 819 pessoas → −1 blacklist). Contra **12.958 ativas com renovação ligada** vencendo no mesmo mês: **6% do cohort de set/2025 já desligou a renovação**.
- Pico de vencimento em **16–17/09** (171 pessoas), coerente com o lançamento de set/2025.
- **90% pagaram com cartão** (738) — a renovação está desligada por escolha, não por meio de pagamento (pix/boleto = 29, nupay 33).
- **Acesso BP:** **373 (46%) têm só o Teller** — para essas o não-renovar é churn total; 152 Básico, 145 Vitalício, 79 Premium, 45 Apoiador, 11 Black, 11 Intermediário, 3 Mecenas.
- **Escuta:** só **221 (27%) ouviram algo nos últimos 90 dias** — a maioria desligou a renovação e parou de usar; o argumento de retenção precisa ser de conteúdo, não de "você usa".
- **146 (18%) já foram abordadas via Zenvia nos últimos 7 dias** — provavelmente já existe fluxo de renovação rodando; alinhar antes de disparar. 41 têm deal Pipedrive aberto (antigo, nenhum criado nos últimos 7 dias).
- 54 compraram pelo Comercial (7%); 23 são Mecenas/ex-Mecenas.

## Queries
| Arquivo | O quê | Status |
|---|---|---|
| [queries/lista_renovantes_set26_sem_renovacao.sql](queries/lista_renovantes_set26_sem_renovacao.sql) | Lista completa (pré-blacklist) | ✅ rodou 26/08/2026 — 819 linhas |

Entrega: `~/meu_projeto/BigQuery/listas/lista_teller_renovantes_set26_sem_renovacao_2026-08-26.xlsx` (fora do repo — PII).

## Wiki atualizada
- `bq-regras.md` — Gotchas Teller: números do cohort set/2026 (`wo renewal` vs `active`), Zenvia já abordando.

---

# Recorte 4: vendas para fora da base BP, mês a mês 2026 (28/08/2026)

Pedido via Slack (Thomas Bergman): *"quantidade de vendas para usuários fora da base da BP do Teller mês a mês 2026"*. Mesma base de CTEs do Recorte 2/3 (`id_person`, membership plena = assinatura paga ≠ `teller` ou vitalício não-Teller, antes da compra). Venda = transação approved não-renovação de `nm_gateway_plan='teller'`.

| Mês | Vendas fora da base | Pessoas | Receita | Total vendas Teller | % fora da base |
|---|---|---|---|---|---|
| jan | 77 | 77 | R$ 19.504 | 400 | 19,3% |
| fev | 35 | 34 | R$ 9.358 | 140 | 25,0% |
| mar | 25 | 23 | R$ 6.159 | 119 | 21,0% |
| abr | 79 | 79 | R$ 13.860 | 319 | 24,8% |
| mai | 62 | 62 | R$ 12.535 | 198 | 31,3% |
| jun | 77 | 76 | R$ 16.085 | 232 | 33,2% |
| jul | 80 | 80 | R$ 15.842 | 342 | 23,4% |
| ago (até 28) | 132 | 132 | R$ 25.047 | 491 | 26,9% |
| **2026** | **567** | **563** | **R$ 118.390** | **2.241** | **25,3%** |

Entregue como DM no Slack ao Thomas (28/08). Query: [queries/nao_membros_vendas_mes_2026.sql](queries/nao_membros_vendas_mes_2026.sql).
