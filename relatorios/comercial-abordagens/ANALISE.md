# Análise — Abordagens do Comercial: o que o time oferece e o que fecha (jul–ago/2026)

Evolução in-place do "Pulso do Comercial" (13/08, janela 14d) para uma leitura de ~2 meses. O snapshot do pulso está em `archive/2026-08-13/`.

## Pergunta original

"Como estão as abordagens do Comercial nos últimos dois meses — o que estão tentando vender, o que estão conseguindo vender?" (André, 27/08/2026, na sequência da análise Odisseia). Meta verificável, janela 29/06–26/08/2026 (9 semanas, última parcial):
(a) volume de abordagens vs conversas reais por semana; (b) que temas o time oferece (menção na transcrição) e como isso mudou; (c) o que vendeu (produto, receita, ticket) e quanto disso passou por conversa; (d) **conversão real por tema** (conversa → compra da mesma pessoa em 14d), inclusive "ofertado × comprado"; (e) foco Odisseia; (f) etapas, motivos de fechamento, concentração por vendedor.

## Decisões de abordagem

- **"Conversa real" = `qt_prospect_interactions > 0`.** 87% das linhas de `dim_zenvia_approaches` são disparo sem resposta (`nm_lead_source` FLOW 75% / N8N 10%). Todas as taxas usam conversas reais como denominador; o volume bruto aparece só como contexto de ritmo.
- **Tema = regex na transcrição** (método validado em `odisseia-lancamento`). Temas ampliados: vitalício, black, CDL, Odisseia, Mecenas, aniversário (Aniv26), Imersão Cabral. Descartados por baixo sinal: Travessia (6k menções, 2 vendas), Big Picture, BP Clube, Cruzada (<30).
- **Conversão real** em vez de "vendas ÷ menções": conversa respondida → `dim_zenvia_contacts` (telefone normalizado / e-mail) → `dim_contact` → `fct_transactions` comercial aprovada em até 14 dias. Joins por telefone e e-mail **separados + UNION DISTINCT** (regra `fluxo-comercial.md`). Duas visões: conversas → venda (taxa) e vendas → tinha conversa (cobertura).
- **Classificação de produto** em 10 classes (Black / Premium / Básico Vitalício separados; CDL físico vs ebook; Eventos high-ticket = Imersão Cabral + Retiro + CEC; Black/Premium recorrente; entrada). Vitalício por `bl_lifetime_offer` OU produto com "vital", restrito aos planos GBB (evita o combo Odisseia+Travessia).
- **Vendedores sem nome no data.json** (repo público): só contagem, top-10 share, mediana e recorte Lambda (`gustavo.koetz` = deals automatizados/IA).
- Paleta categórica de 6 slots validada com `validate_palette.js` (claro e escuro); "Outros" em cinza. Tema "vitalício" herda o azul do Black Vitalício, "aniversário" o laranja do Básico (são a mesma oferta).

## Achados principais (29/06–26/08/2026)

1. **Funil:** 774.887 abordagens → 99.868 conversas reais (12,9%) → 9.936 com venda em 14d (**9,9%**, R$ 13,2M). Volume enviado oscila 2× (57k–134k/sem); conversas reais ficam em 9–13k/sem — disparar mais não abriu mais conversas.
2. **Vendas do canal:** 16.805 / **R$ 16,97M** (ticket R$ 1.010). Jul R$ 8,30M; ago (até 26) R$ 6,57M. Vitalício = **46% da receita** (R$ 7,79M: Black R$ 3,97M / 1.099, Premium R$ 2,04M / 1.228, Básico+outros R$ 1,78M / 1.496). CDL R$ 4,25M (25%, quase todo nas 2 primeiras semanas — fechamento Lote 2/3). Mecenas R$ 1,77M / 507. Odisseia R$ 1,03M / 887 (6%). Eventos high-ticket 15 / R$ 342k.
3. **Script:** Vitalício em **42%** das conversas reais, CDL 27%, aniversário 25%, Black 24%, Odisseia **5,1%**, Mecenas 5,0%, Cabral 0,7%. Tendência (média semanal das 4 semanas completas da 2ª metade vs 4 da 1ª): CDL −52%, aniversário −28%, Black −10%, Vitalício +5%, Mecenas +258% (246 → 881/sem), Odisseia +167% (entra na semana de 20/07, pico 1.673 na semana de 27/07, ~590/sem em agosto), Cabral 34 → 143/sem.
4. **Conversão real por tema (no produto ofertado / em qualquer produto):** Odisseia **14,2% / 18,9%**; Vitalício 7,8% / 11,8%; CDL 6,8% / 13,4%; Mecenas 6,3% / 13,8%; Black 4,0% / 12,5%; média do canal 9,9%. A leitura do pulso (Odisseia 24%, vendas ÷ menções) estava inflada — pendência resolvida.
5. **Ofertado × comprado:** conversa de Black fecha mais Premium/Básico Vitalício (971) do que Black (939); conversa de CDL puxou 685 Black Vitalício (oferta Ouro) e 399 Odisseia; conversa de Odisseia puxou 130 Black Vitalício (R$ 472k, bundle "Black Vitalício + Odisseia R$ 4.782").
6. **Cobertura:** 92% das vendas de Black Vitalício, 87% Premium, 82% Básico Vit, 80% CDL físico, 82% Odisseia tiveram conversa real nos 14d anteriores. Exceções: eventos high-ticket 13% (telefone/relacionamento) e assinaturas de entrada 46% (Lambda = 2.987 das 6.428).
7. **Odisseia:** 5.074 conversas reais / 4.692 pessoas; 65% na etapa `carteiraMecenas`; 59% das menções são só Odisseia, 35% coladas ao CDL, 11% ao Black. Oferta padrão "12x de 97" (693 vendas); tiers Bronze/Prata/Ouro de agosto = ~100 vendas. R$ 328 gerados por conversa de Odisseia em 14d vs R$ 132 na média do canal.
8. **Higiene CRM:** 56% das conversas reais sem `nm_closing_reason`; "ganho" marcado em 1,8% (venda real 9,9%); "semContato" em 11% de conversas em que o cliente respondeu.
9. **Time:** 47 vendedores humanos, R$ 15,75M; top-10 = 38%; mediana R$ 415k/vendedor no período. Lambda 3.734 vendas / R$ 1,07M (ticket R$ 287, 6,3% da receita).

## Pendências / próximos passos

- Se a Odisseia for virar pauta: testar oferta ativa fora da carteira Mecenas (hoje 65% ali) — a taxa por conversa (14–19%) sustenta escalar.
- Registro de desfecho no Zenvia (56% sem motivo) — levar ao time; sem isso conversão só sai por cruzamento.
- Cadência de refresh: o relatório é janela móvel de 9 semanas; decidir se roda semanal.
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

- `wiki-brasil-paralelo/pages/odisseia.md` — conversão real por conversa (14,2%/18,9%), Odisseia como porta para Black, 65% na carteira Mecenas.
- `wiki-bp/pages/metricas-referencia.md` — seção "Comercial jul–ago/2026" (funil, mix, conversão por tema).
- `wiki-bp/pages/queries-referencia.md` — método conversa ↔ venda (14d, telefone/e-mail UNION DISTINCT) e gotcha "conversa real".

## Relação com outros relatórios

- `odisseia-campanha/`, `odisseia-perfil/`, `odisseia-lancamento/` — visão da campanha e do comprador; este é a visão do canal.
- `lambda-conteudo-bloqueado/` — as vendas Lambda aparecem aqui só como recorte agregado.
