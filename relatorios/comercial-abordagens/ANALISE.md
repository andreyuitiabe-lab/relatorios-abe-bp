# Análise — Abordagens do Comercial: o que o time oferece e o que fecha (jul–ago/2026)

Evolução in-place do "Pulso do Comercial" (13/08, janela 14d) para uma leitura de ~2 meses. O snapshot do pulso está em `archive/2026-08-13/`.

⚠️ **Método revisado em 03/09/2026** após auditoria por dois agentes revisores (data-analyst + analytics-data-analysis), com os pontos críticos re-verificados manualmente no BQ. O que mudou: (1) denominador restrito ao grupo Comercial do Zenvia (`TRIM(nm_group)='Comercial'` — Retenção/Suporte/CS eram 21% das conversas e convertem pela metade); (2) conversão por tema **estratificada por etapa** (carteiraMecenas vs fora), porque a etapa domina a taxa e o headline anterior da Odisseia era efeito de mix; (3) receita 14d por transação distinta (antes dupla-contava venda ligada a 2+ conversas, −9%); (4) taxa também por pessoa; (5) removido o `+1 DAY` que contava conversa pós-venda como "antecedida"; (6) reescrito o achado sobre elasticidade do disparo (corr disparos×respostas = 0,8 — disparar mais **abre** mais conversas, com retorno marginal ~1/3 do médio). Números abaixo re-gerados na janela 06/07–02/09/2026.

## Pergunta original

"Como estão as abordagens do Comercial nos últimos dois meses — o que estão tentando vender, o que estão conseguindo vender?" (André, 27/08/2026, na sequência da análise Odisseia). Meta verificável, janela móvel de 9 semanas (snapshot desta revisão: 06/07–02/09/2026):
(a) volume de abordagens vs conversas reais por semana; (b) que temas o time oferece (menção na transcrição) e como isso mudou; (c) o que vendeu (produto, receita, ticket) e quanto disso passou por conversa; (d) **conversão real por tema** (conversa → compra da mesma pessoa em 14d), inclusive "ofertado × comprado"; (e) foco Odisseia; (f) etapas, motivos de fechamento, concentração por vendedor.

## Decisões de abordagem

- **"Conversa real" = `qt_prospect_interactions > 0` E `TRIM(dim_zenvia_contacts.nm_group) = 'Comercial'`.** ~87% das linhas de `dim_zenvia_approaches` são disparo sem resposta (`nm_lead_source` FLOW/N8N) e ~21% das respondidas eram de grupos não-comerciais (Retenção/Suporte/CS 8D, conversão 5–8%) — ambos fora do denominador. O volume bruto aparece só como contexto de ritmo.
- **Conversão estratificada por etapa** (carteiraMecenas vs fora): a etapa domina a taxa (22,5% vs 5,4% em qualquer produto) — taxa agregada por tema é enganosa quando o tema se concentra na carteira (caso Odisseia).
- **Receita 14d por transação distinta** (venda ligada a 2+ conversas conta uma vez) e **taxa também por pessoa** (23% das pessoas têm 2+ conversas).
- **Tema = regex na transcrição** (método validado em `odisseia-lancamento`). Temas ampliados: vitalício, black, CDL, Odisseia, Mecenas, aniversário (Aniv26), Imersão Cabral. Descartados por baixo sinal: Travessia (6k menções, 2 vendas), Big Picture, BP Clube, Cruzada (<30).
- **Conversão real** em vez de "vendas ÷ menções": conversa real → `dim_zenvia_contacts` (telefone normalizado / e-mail) → `dim_contact` → `fct_transactions` comercial aprovada em até 14 dias (janela validada: 87% das vendas em 60d caem em ≤14d; mediana 0,5 dia). Joins por telefone e e-mail **separados + UNION DISTINCT** (regra `fluxo-comercial.md`). Duas visões: conversas → venda (taxa) e vendas → tinha conversa nos 14d anteriores (cobertura, sem contar conversa pós-venda).
- **Classificação de produto** em 10 classes (Black / Premium / Básico Vitalício separados; CDL físico vs ebook; Eventos high-ticket = Imersão Cabral + Retiro + CEC; Black/Premium recorrente; entrada). Vitalício por `bl_lifetime_offer` OU produto com "vital", restrito aos planos GBB (evita o combo Odisseia+Travessia).
- **Vendedores sem nome no data.json** (repo público): só contagem, top-10 share, mediana e recorte Lambda (`gustavo.koetz` = deals automatizados/IA).
- Paleta categórica de 6 slots validada com `validate_palette.js` (claro e escuro); "Outros" em cinza. Tema "vitalício" herda o azul do Black Vitalício, "aniversário" o laranja do Básico (são a mesma oferta).

## Achados principais (snapshot 06/07–02/09/2026)

1. **Funil:** 741.791 abordagens (grupo Comercial) → 78.280 conversas reais (10,6%) → 8.727 com venda em 14d (**11,1% das conversas; 12,4% das pessoas**; R$ 11,5M em transações distintas). Disparar mais **abre** mais conversas (corr semanal 0,84), mas com retorno decrescente: taxa de resposta ~14% nas semanas leves → ~8% no pico de 127k — retorno marginal ~1/3 do médio; o teto é capacidade de atendimento (~57 vendedores, 8–11k conversas/sem).
2. **Vendas do canal:** 16.075 / **R$ 16,40M** (ticket R$ 1.020). Vitalício = **53% da receita** (R$ 8,68M: Black R$ 4,23M / 1.169, Premium R$ 2,34M / 1.423, Básico+outros R$ 2,11M / 1.786). Mecenas R$ 1,94M / 567. CDL R$ 1,90M (12%, em queda — fim do Lote 3). Odisseia R$ 1,50M / 1.294 (9%). Eventos high-ticket 16 / R$ 357k.
3. **Script:** Vitalício em **53%** das conversas reais, aniversário 31,5%, Black 30,5%, CDL 25,7%, Odisseia **8,8%**, Mecenas 6,4%, Cabral 1,0%. Tendência (média semanal 2ª metade vs 1ª): CDL −50%, aniversário −45%, Vitalício −5%, Black −3%, Odisseia +11%, Mecenas +181%, Cabral +141%.
4. **A etapa domina a conversão** — qualquer conversa: carteira Mecenas 22,5% vs fora 5,4%. Por tema, no produto ofertado (carteira / fora): Odisseia **21,9% / 2,0%**, Vitalício 26,6% / 0,8%, Black 10,1% / 0,2%, CDL 8,3% / 0,9%, Mecenas 9,9% / 0,9%. **O headline anterior da Odisseia (14–19% agregado) era efeito de mix de etapa** — dentro da carteira ela ainda é a melhor oferta-produto depois do Vitalício; fora, não move a taxa.
5. **Ofertado × comprado (tx distintas):** conversa de Black fecha mais Premium/Básico Vitalício (1.128) do que Black (986); conversa de CDL puxa 698 Black Vitalício (oferta Ouro) e 467 Odisseia; conversa de Odisseia puxa 164 Black Vitalício (R$ 587k, bundle).
6. **Cobertura (conversa real nos 14d anteriores):** Black Vitalício 88%, Premium 83%, Odisseia 79%, Básico 74%, Mecenas 71%, CDL físico 66%. Exceções: eventos high-ticket 13% (telefone/relacionamento) e assinaturas de entrada 33% (Lambda = 2.980 das 6.638).
7. **Odisseia:** 6.853 conversas reais / 6.281 pessoas; 66% na carteira Mecenas; 74% das menções (com disparos) são só Odisseia, 21% coladas ao CDL. Oportunidade mapeada: **21,1k conversas de carteira sem menção à Odisseia** — é onde a oferta comprovadamente rende (21,9% no livro); fora da carteira, só piloto controlado (expectativa ~2–3%).
8. **Higiene CRM:** 56% das conversas reais sem `nm_closing_reason`; "ganho" marcado em 2,1% (venda real 11,1%); "semContato" em 13% de conversas em que o cliente respondeu.
9. **Time:** 48 vendedores humanos, R$ 15,27M; top-10 = 38%; mediana R$ 400k/vendedor no período. Lambda 3.656 vendas / R$ 968k (ticket R$ 265). Auditoria apontou dispersão 8–60% de conversão na carteira entre vendedores — vale relatório interno próprio.

## Pendências / próximos passos

- **Carteira sem oferta**: quantificar/listar as ~21k conversas de carteira sem menção à Odisseia (e ~13k sem Vitalício) — é a alavanca sustentada pelos dados. Fora da carteira, Odisseia só via piloto com controle (expectativa 2–3%).
- Registro de desfecho no Zenvia (56% sem motivo) — levar ao time; sem isso conversão só sai por cruzamento.
- Da auditoria (03/09), candidatas a relatório próprio: eficácia de templates de disparo (broadcast ~1,7% de resposta vs saudação pessoal ~41%) + higiene de lista (carência de reabordagem, comprador digital ≤7d, vitalício ativo recebendo oferta de vitalício); conversão por vendedor na carteira (interno, com nomes; dispersão 8–60%); ranking de CTAs do chatbot; base vitalícia como carteira. Achados exploratórios ainda não re-verificados manualmente.
- Cadência de refresh: janela móvel de 9 semanas; decidir se roda semanal.
- Bundles Odisseia+Black entram como 2 transações — receita do Black creditada ao Black (correto para "o que vende"); para contar livros usar `lista_odisseia_livros.sql`.

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/semana_temas.sql](queries/semana_temas.sql) | Série semanal: abordagens, contatos, vendedores, respondidas, menções por tema (total e respondidas) |
| [queries/vendas_semana.sql](queries/vendas_semana.sql) | Vendas comerciais por semana × produto (10 classes) |
| [queries/conversao_tema.sql](queries/conversao_tema.sql) | Conversão real: conversa respondida com tema → compra da mesma pessoa em 14d |
| [queries/venda_conversa.sql](queries/venda_conversa.sql) | Vendas: % antecedidas por conversa real e temas citados |
| [queries/tema_produto.sql](queries/tema_produto.sql) | Matriz ofertado × comprado |
| [queries/stages_motivos.sql](queries/stages_motivos.sql) | Etapa e motivo de fechamento por tema (conversas reais) |
| [queries/odisseia.sql](queries/odisseia.sql) | Co-ocorrência de temas com Odisseia; ofertas vendidas por mês |
| [queries/vendedores.sql](queries/vendedores.sql) | Concentração por vendedor (sem nomes) e recorte Lambda |

Os `.sql` são gerados a partir das strings do `refresh.py` (janela dinâmica) — editar lá e regenerar.

## Wiki atualizada

- `wiki-brasil-paralelo/pages/odisseia.md` — conversão por conversa corrigida (carteira 21,9% / fora 2,0%; agregado era mix), Odisseia como porta para Black.
- `wiki-bp/pages/metricas-referencia.md` — seção "Comercial — abordagens e conversão" (corrigida 03/09: grupo Comercial, estratificação por carteira, receita distinta).
- `wiki-bp/pages/queries-referencia.md` — método conversa ↔ venda (grupo Comercial, estratificação por etapa, UNION DISTINCT tel/e-mail, receita distinta).
- `wiki-bp/pages/fluxo-comercial.md` — nota C0113: em jul–ago/26, 100% das vendas Lambda saem com vendedor preenchido (gotcha dos 67% NULL ficou histórico).

## Relação com outros relatórios

- `odisseia-campanha/`, `odisseia-perfil/`, `odisseia-lancamento/` — visão da campanha e do comprador; este é a visão do canal.
- `lambda-conteudo-bloqueado/` — as vendas Lambda aparecem aqui só como recorte agregado.
