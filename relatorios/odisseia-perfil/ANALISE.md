# Análise: Perfil de Compra — Odisseia (+ interseção com o Clube do Livro)

## Pergunta original

Pedido da Manu Celestino (Slack, 25/08/2026, para a reunião do **Box A Última Cruzada** às 12h):
"Quem comprou livros na BP — clube do livro e odisseia. Quais ofertas fizemos em cada e qual o comportamento
delas? Da base do CDL, quantos compraram? Dos compradores, quantos não eram clientes BP e quantos eram?
Dos que eram, eram clientes de quais produtos? Mesma coisa pra base da Odisseia."

Meta verificável: para cada um dos dois livros, responder (a) quantos compradores e quanto faturou,
(b) que fatia já era cliente BP e em que status, (c) quais produtos tinham antes — e (d) o cruzamento
entre as duas bases (quantos compraram os dois), que é o número que informa a decisão do terceiro livro.

## Decisões de abordagem

- **Espelho metodológico do relatório `clube-do-livro`** — mesmas classes de status, mesmas faixas de
  antiguidade, mesmo tratamento de identidade. Sem isso os dois números não são comparáveis.
- **`id_person` como chave** (via `dim_person_identity`), não e-mail: resolve múltiplas contas da mesma
  pessoa. É o que torna a interseção confiável — por e-mail, parte dos "compraram os dois" se perderia.
- **Status no momento da compra**, não status atual — a pergunta é "quem era cliente quando comprou".
- **Universo da Odisseia = a categorização validada em 21/08** (wiki `bq-planos.md` §Odisseia): livro
  colecionador + `livro-odisseia` + curso avulso + os bundles (Ouro/Black, CDL+Odisseia, combo Travessia),
  identificados por `nm_gateway_offer`. Um filtro só por `nm_gateway_plan` perderia os bundles e o curso.
- **Receita pela perna core** (`bl_core`): bundles do Comercial são gravados como duas transações no
  mesmo dia (perna do outro produto + perna do livro). Somar tudo creditaria o Black/CDL à Odisseia.
- **Exclusão de assinaturas-fantasma** — ⚠️ o achado metodológico desta rodada: CDL e Odisseia geram
  registro `paid` em `dim_subscriptions` (25.142 e 2.671). Sem excluir esses planos do histórico de
  membership, **todo comprador do CDL seria classificado como "Membro Ativo"** na análise da Odisseia.
  O combo Odisseia+Travessia ainda vem com `bl_lifetime_offer = TRUE` sem ser vitalício, o que
  contaminaria a classe "Vitalício". Exclusão aplicada nos dois relatórios (no CDL o efeito é 0,2pp).

## Achados principais

**Odisseia (17/07–25/08/2026):** 2.829 compradores · R$ 3,45M · ticket R$ 1.218 · 93,1% levam o livro impresso.

**Status no momento da compra — 87,0% já eram clientes BP:**

| Status | Odisseia | Clube do Livro |
|---|---|---|
| Vitalício | **46,2%** (1.307) | 30,5% (7.539) |
| Membro Ativo | 31,4% (889) | 36,5% (9.028) |
| Ex-Membro | 9,4% (266) | 15,4% (3.817) |
| Nunca foi Membro | 13,0% (367) | 17,7% (4.369) |

→ A Odisseia é **muito mais dependente do vitalício** (46% vs 30%). Faz sentido: quem já pagou pelo acesso
máximo não tem próximo passo na assinatura — o objeto físico é o upgrade possível.

**Interseção CDL × Odisseia (por `id_person`):**

| Grupo | Pessoas | % | Receita em livros |
|---|---|---|---|
| Só Clube do Livro | 23.170 | 89,1% | R$ 29,7M |
| **Comprou os dois** | **1.583** | **6,1%** | R$ 4,0M |
| Só Odisseia | 1.246 | 4,8% | R$ 1,5M |
| **Total de pessoas** | **25.999** | 100% | R$ 35,2M |

- **Recompra CDL → Odisseia: 6,3%** (1.569 dos 24.753 compradores do CDL compraram a Odisseia depois).
  Sobe dos 4,0% medidos em 12/08 — a curva ainda estava rodando.
- **55,5% dos compradores da Odisseia vieram do CDL.** Metade da demanda do 2º livro é a base do 1º.
- Quem comprou os dois gasta **R$ 2.517 em livros** por pessoa, contra R$ 1.283 de quem só comprou o CDL.

**Antiguidade — a Odisseia vende para quem tem mais casa:**
- 2+ anos de BP: 67,3% (CDL: 62,2%) · mais de 4 anos: 46,7% (CDL: 39,3%)
- Entrou na BP pela Odisseia: 10,3% (290) — no CDL foram 17,7%. **Livro caro capta menos gente nova.**

**Produtos que tinham antes (% da base Odisseia):**
- **Clube do Livro 53,8%** (1.521) — mais frequente que qualquer plano de assinatura
- Básico 39,6% · Premium GBB 36,6% · Núcleo 24,1% · Patriota 23,6% · Black Vitalício 23,5%
- Acesso Total 23,4% · Premium GBB Vitalício 22,9% · Ebooks/Audiolivros CDL 14,6% · Mecenas 13,3%

**Consumo histórico — comprador da Odisseia é 2× mais valioso que o do CDL:**
- Gasto médio antes: **R$ 6.170** (mediana R$ 3.177) vs R$ 3.072 (mediana R$ 1.200) do CDL
- 3,9 planos distintos por pessoa (CDL: 2,8) · 89% tinham histórico de compra anterior

**Canal:** Digital 72,2% (2.042) · Comercial 27,8% (787) — invertido em relação ao CDL (51,2% Comercial).
Consistente com o diagnóstico do `odisseia-lancamento`: o Comercial nunca recebeu a Odisseia como pauta fixa.

**Ofertas e comportamento** (detalhe em `bq-planos.md` §Odisseia e §Clube do Livro):
- CDL: lotes, order bumps e bundles (Black, audiobook), 18x — ticket médio R$ 1.274, 51% via Comercial.
- Odisseia: 3 tiers de preço (R$ 1.500 não-membro / R$ 1.350 vitalício-mecenas / R$ 1.200 comprador CDL),
  sem lotes; combo com Travessia (R$ 1.548) desde 26/07; tiers do Comercial Bronze/Prata/Ouro;
  curso avulso desde 05/08. O pacote **só-digital é 6,9% dos compradores a ticket R$ 498** — existe
  demanda por versão barata, mas ela não é o produto.

## O que isso diz sobre o Box A Última Cruzada

1. **A carteira de "compradores de livro caro" é pequena e se repete.** 26 mil pessoas ao todo nos dois
   livros, e a recompra de um para o outro roda a 6,3%. Um terceiro livro disputa majoritariamente a
   mesma base — o forecast do SSR (~7.000) precisa dessa régua: seria 4,4× o volume da Odisseia.
2. **O núcleo é vitalício + antiguidade + alto LTV**, não "leitor". A oferta mais eficiente é a mesma
   lista de sempre; o que muda é o preço.
3. **Preço é a alavanca de ampliação.** O Box a R$ 850 fica abaixo do teto da média renda (R$ 800 no PSM
   — ainda acima, mas muito mais perto que os R$ 1.200–1.500 da Odisseia), e o IP é de massa. É a chance
   de sair da carteira de 26 mil — mas isso é hipótese do SSR, não dado observado.
4. **Captação de público novo por livro é baixa** (10,3% na Odisseia). Se o objetivo do Box for aquisição,
   a régua tem que ser outra; se for monetizar base, o histórico dos dois livros sustenta.

## Pendências / próximos passos

- A recompra de 6,3% ainda não estabilizou (Odisseia vende há 5 semanas) — remedir em out/2026 para ter
  a taxa madura antes de fechar o forecast do Box.
- Não medido aqui: **quantos dos compradores compraram por causa da oferta CDL a R$ 1.200** (o desconto
  de recompra) vs preço cheio — sai de `nm_gateway_offer`, vale se a discussão do Box for de precificação.
- Perfil de renda/cartão dos 1.583 que compraram os dois: insumo natural para o lookalike do Box
  (padrão em `personas_ssr/`, usa `dim_card_bin_details`).

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/totais.sql](queries/totais.sql) | Universo e receita (perna core, sem creditar Black/CDL) |
| [queries/status_momento_compra.sql](queries/status_momento_compra.sql) | Status de membership no momento da compra |
| [queries/antiguidade.sql](queries/antiguidade.sql) | Tempo de casa na BP até a compra |
| [queries/produtos_antes.sql](queries/produtos_antes.sql) | Produtos comprados antes da Odisseia |
| [queries/canal.sql](queries/canal.sql) | Compradores, ticket e receita por canal |
| [queries/consumo_historico.sql](queries/consumo_historico.sql) | Gasto e planos anteriores |
| [queries/tipo_produto.sql](queries/tipo_produto.sql) | Livro físico × só digital |
| [queries/recompra_cdl.sql](queries/recompra_cdl.sql) | Recompra CDL → Odisseia sobre a base do CDL |
| [queries/interseccao_cdl_odisseia.sql](queries/interseccao_cdl_odisseia.sql) | Venn por `id_person` |

Fonte canônica das CTEs é o `refresh.py`; os `.sql` são materializados a partir dele.

## Wiki atualizada

- `wiki-bp/bq-planos.md` — gotcha das assinaturas-fantasma de produtos físicos em `dim_subscriptions`
- `wiki-bp/metricas-referencia.md` — perfil dos dois livros e interseção (25/08/2026)
- `wiki-brasil-paralelo/odisseia.md` — recompra atualizada 4,0% → 6,3% + perfil do comprador
- `wiki-bp/queries-referencia.md` — padrão de interseção de duas bases de produto por `id_person`

## Relação com outros relatórios

- `clube-do-livro/` — o espelho deste, mesma metodologia (atualizado na mesma rodada)
- `odisseia-campanha/` — campanha completa: CRM, ads, Comercial
- `odisseia-lancamento/` — comparativo estrutural vs CDL no lançamento
- `odisseia/` — SSR pré-lançamento com o veredicto e o PSM do Box A Última Cruzada
