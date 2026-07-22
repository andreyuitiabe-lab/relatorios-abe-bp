# Análise — Lançamento Odisseia vs Clube do Livro (22/jul/2026)

## Pergunta original

A Odisseia (edição colecionador) começou a vender na semana de 17/07 com abordagem do Comercial, mas vende muito pouco comparado ao início do Clube do Livro (que também começou só pelo Comercial). O que está diferente? E a campanha BP10 está tirando o foco do Comercial da Odisseia?

## Decisões de abordagem

- **Janelas alinhadas por dia de campanha**: CDL D1 = 05/05 (abertura Comercial), ODI D1 = 17/07 (primeira venda). Comparação D1–D6.
- **Filtros**: `nm_status='approved'`, `bl_is_renovation=FALSE`; CDL sem Bundles; Odisseia = `nm_gateway_plan='livro-odisseia-edicao-colecionador'` OR produto `%odis%`.
- **Esforço do Comercial medido por menção na transcrição** (`dim_zenvia_approaches.nm_conversation`, regex), porque nem Zenvia (`nm_gateway_plan`) nem Pipedrive (`nm_product_deal`) marcam o produto da abordagem (~sempre NULL). Método acordado com o solicitante.
- BP10 aproximado nas conversas por regex "10 anos|dez anos|aniversário"; nas vendas, pela oferta com sufixo `Aniv26`.

## Achados principais

1. **Placar D1–D6: CDL 915 vendas (R$ 1,09M) vs Odisseia 90 (R$ 109k).** O gap se decompõe em: Comercial **703 vs 5 (141×)**; Digital/CRM **212 vs 85 (2,5×)**. O buraco é o canal Comercial, não o apetite do público.
2. **A premissa "só o comercial está vendendo" estava errada**: 94% das vendas da Odisseia são digitais, quase todas de CRM (`[VENDA] [E-MAIL]/[WHATSAPP] [ODI] Pré-Venda`), com o checkout dominante sendo o de compradores do CDL a R$ 1.200.
3. **Esforço**: no lançamento do CDL, 3,2–5,5 mil conversas/dia ofereciam o produto (29–35 vendedores), começando 4 dias **antes** do D1 (script de pré-venda). Na Odisseia: **53 conversas em 6 dias** (25 vendedores, ~2 conversas cada), zero antes do D1.
4. **Conversão por conversa não é o problema**: ODI ~9,3% vs CDL ~3,6% (vendas comerciais / conversas que mencionam o produto). Quando oferece, vende.
5. **Hipótese BP10: confirmada, com nuance.** O script do time aponta para o BP10 (pico de 3.196 menções em 16/07 vs 0–25 da Odisseia). Mas o "BP10" do Comercial é venda de **Vitalício Aniv26**: 157 vendas / R$ 427k na semana (Vitalício total: 362 vendas / R$ 897k, 31% do mix vs 7% em maio). Está rendendo bem — ticket ~R$ 2,5k vs R$ 1,2k da Odisseia.
6. **Receita total do Comercial ficou estável entre as janelas**: R$ 1,64M na semana do CDL (mai, 2.121 vendas, ticket R$ 775) vs R$ 1,63M na semana BP10/ODI (jul, 1.346 vendas, ticket R$ 1.209 — obs.: último dia parcial no momento da medição). −37% em volume, compensado por +56% de ticket (mix deslocado para Vitalício Aniv26). Ou seja: o time não está rendendo menos dinheiro — a Odisseia é que não entrou na pauta.
7. **Capacidade**: mesmo time (54 vendedores) mas **metade do ritmo** — 2,5k abordagens/dia em jul vs 5k em mai (−50%). Além do redirecionamento, o volume total caiu.
7. **Estrutura**: Odisseia sem captação de leads (0 vs 4.638 do CDL), sem mídia Meta (R$ 0 vs R$ 41k), sem lotes/order bumps. É um lançamento só-CRM.
8. **Contexto que muda a régua**: o relatório SSR de 21/07 (`relatorios/odisseia/`) recomendou lançamento em fases — primeiro só aos ~23,7k compradores do CDL a R$ 1.200 via CRM, medir recompra, depois abrir base+mídia. Os dados são compatíveis com essa fase 1. Se intencional, a comparação com o lançamento full-force do CDL é régua errada.

## Conclusão

A Odisseia não está "vendendo mal" — **ela não foi lançada no Comercial**. Não recebeu lista, script nem meta. Concorrência de campanha não explica sozinha: no lançamento do CDL também rodavam DOM/ELS e o CDL ocupou 39% do mix do time. A decisão pendente é de negócio: manter o time no Vitalício Aniv26 (que rende mais por venda) ou ativar a Odisseia com o playbook do CDL (lista dedicada + script + meta).

## Pendências / próximos passos

- Investigar com o gestor comercial a queda de ~50% no ritmo de abordagens (férias? listas menores?).
- Se a fase 1 do SSR for a estratégia oficial: medir taxa de recompra CDL→Odisseia no CRM antes de acionar o Comercial.
- As 5 vendas comerciais não têm conversa vinculada por `id_transaction` no Zenvia — se precisar de rastreio fino, cruzar por telefone/email.
- Deals Pipedrive com `nm_product_deal='1127'` (1.970 criados a partir de 20/07) não foram identificados — pode ser a lista da Odisseia; verificar com o Comercial.

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/placar_d1_d6.sql](queries/placar_d1_d6.sql) | Vendas/receita por dia de campanha e canal, D1–D6 alinhados |
| [queries/mencoes_zenvia.sql](queries/mencoes_zenvia.sql) | Esforço por menção ao produto na transcrição (D-4 a D6) |
| [queries/mencoes_jul_por_tema.sql](queries/mencoes_jul_por_tema.sql) | Menções ODI/CDL/BP10 por dia em julho |
| [queries/mix_comercial.sql](queries/mix_comercial.sql) | Mix de vendas do Comercial: semana CDL vs semana ODI+BP10 |
| [queries/estrutura_capacidade.sql](queries/estrutura_capacidade.sql) | Capacidade, leads de aquecimento, spend Meta, vitalícios Aniv26 |

## Wiki atualizada

- `wiki-bp/bq-planos.md` — plano `livro-odisseia-edicao-colecionador` + seção Odisseia (checkouts, canais, gotcha fase 1 só-CRM)
- `wiki-brasil-paralelo/campanhas-calendario.md` — campanha ODI (venda 17/07, sem aquecimento)
- `wiki-bp/queries-referencia.md` — método "esforço do Comercial por menção na transcrição Zenvia"
- `wiki-bp/metricas-referencia.md` — baseline D1–D6 CDL vs Odisseia + mix Comercial jul/2026

## Limitações

- Amostra da Odisseia: ~6 dias. Leitura precoce.
- Esforço por menção na transcrição não captura conversas fora do Zenvia (telefone etc.).
- Regex BP10 pode ter falsos positivos ("aniversário" do cliente, por exemplo).
