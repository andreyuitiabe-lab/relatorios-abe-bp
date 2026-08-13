# Análise — Pulso do Comercial: abordagens dos últimos dias (13/ago/2026)

## Pergunta original

"Como está a abordagem do Comercial nos últimos dias?" (André, 13/08/2026, na sequência do update do relatório `odisseia-lancamento`). Meta verificável: nos últimos 14 dias completos, (a) qual o volume de abordagens e vendedores; (b) que temas o time oferece nas conversas; (c) o que está vendendo (produto, receita, ticket); (d) qual a conversão por conversa por tema; (e) em que etapas do funil as conversas acontecem — tudo comparado aos 14 dias anteriores.

## Decisões de abordagem

- **Janela móvel**: últimos 14 dias completos (até ontem) vs 14 anteriores, calculada dinamicamente no `refresh.py` — o relatório é um "pulso" que se atualiza rodando só o refresh.
- **"O que o time oferece" = menção ao tema na transcrição** (`dim_zenvia_approaches.nm_conversation`, regex) — método validado na análise `odisseia-lancamento` (Zenvia/Pipedrive não marcam o produto da abordagem). Temas: odisseia, clube do livro, "10 anos/aniversário" (=BP10), vitalício, mecenas. Uma conversa pode citar mais de um tema.
- **Vendas**: `fct_transactions` com `nm_status='approved'`, `bl_is_renovation=FALSE`, `bl_is_commercial_channel=TRUE`; classificação de produto igual à do mix do `odisseia-lancamento`.
- **Conversão por conversa** = vendas do produto ÷ conversas que mencionam o tema (aproximação; venda não é vinculada à conversa individual).
- Página segue a skill dataviz: paleta categórica validada (5 slots, cor fixa por entidade), janela atual em ênfase vs anterior em cinza, tabela como vista de dados.

## Achados principais (janela 30/07–12/08 vs 16/07–29/07)

1. **Ritmo estável**: 48,6k abordagens (+7%), pico de 52 vendedores/dia. Fim de semana ~900/dia, dias úteis 3–6k.
2. **O script do time está no Vitalício**: 15,5k conversas mencionam vitalício (32% das abordagens) e o produto faz 56% da receita comercial (R$ 2,26M de R$ 4,02M). O tema "BP10/aniversário" está esvaziando (−44% de menções) — a campanha de aniversário perde tração, mas picos de disparo ainda acontecem (11/08: 2,7k menções).
3. **A carteira Mecenas voltou ao script**: menções 3,4× (947 → 3.187), 168 vendas / R$ 471k (ticket ~R$ 2,8k).
4. **Odisseia é nicho com a melhor conversão**: 3% das conversas (1.570 menções, −34% vs quinzena anterior — o pico da oferta ativa ficou no fim de julho), mas converte 24,2% por conversa (vs 8,2% vitalício, 5,3% mecenas, 4,0% CDL) e vendeu 380 unidades / R$ 443k (+71%). É vendida sobretudo dentro da etapa `carteiraMecenas` (538 das ~1,6k conversas); a etapa `odisseia` do Zenvia quase não é usada (14).
5. **CDL em cauda de campanha**: 8,3k menções mas −53% em vendas (700 → 329) e a pior conversão.
6. **Receita total do canal caiu 8%** (R$ 4,37M → R$ 4,02M) apesar de +8% em vendas — mix deslocou para itens de ticket menor (Assinaturas/outros +32% em vendas, ticket R$ 257).

## Pendências / próximos passos

- Se o pulso for útil recorrente, decidir cadência de refresh (manual sob demanda vs agendado).
- A taxa de conversão da Odisseia (24%) pode estar inflada por vendas de lista/telefone sem conversa Zenvia — se virar métrica de decisão, refinar o vínculo venda↔conversa (telefone/email).
- Temas são fixos no `refresh.py` (dict `TEMAS`) — adicionar tema novo é uma linha.

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/diario_temas.sql](queries/diario_temas.sql) | Abordagens/dia, vendedores e menções por tema (regex na transcrição) |
| [queries/vendas_por_produto.sql](queries/vendas_por_produto.sql) | Vendas comerciais por dia × produto |
| [queries/stages.sql](queries/stages.sql) | Etapas do funil das abordagens (geral e só Odisseia) |

## Wiki atualizada

- Nenhuma página nova — o método (menção na transcrição) já está em `queries-referencia.md`; os números desta janela são perecíveis (janela móvel), referências duráveis ficam em `metricas-referencia.md` via análise odisseia-lancamento.

## Relação com outros relatórios

- `odisseia-lancamento/` — comparativo estrutural CDL vs Odisseia (D1–Dn alinhados); este aqui é o pulso operacional corrente do canal.
