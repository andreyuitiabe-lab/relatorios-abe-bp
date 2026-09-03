# Análise — Fechamento Mensal de Influenciadores

## Pergunta original

Pedido da Bárbara Olivieri (Slack, grupo com Thais Schönerwald e Isabella Antunes, 31/08/2026):
relatório de resultado de agosto de influenciadores — *"quanto gastamos, quanto voltou, desempenho,
destaques"*, com o custo alinhado ao que o time mandou para o controle de custo marginal.

Rotina mensal a partir daqui. O ranking histórico de influs (jan/2025+) é outro relatório:
[`relatorios/influenciadores/`](../influenciadores/).

## Estrutura

| Arquivo | O que é |
|---|---|
| `index.html` | Versão resumida — os 4 tópicos do pedido. É a peça de apresentar. |
| `detalhado.html` | Versão completa — método, validações, cascata, série do ano. |
| `data.json` | Gerado pelo `refresh.py`. Alimenta gráficos e tabelas das duas páginas. |
| `custo_manual.json` | **Cachê e contexto da BP — preenchido à mão.** Não existe no BigQuery. |
| `refresh.py` | Queries BQ → `data.json`. Usa `bqq` (nunca `bq query`). |

### Como rodar um mês novo

1. Pedir a aba INFLUENCIADORES do controle de custo variável e preencher `custo_manual.json`
   com a chave do mês (`cache_peca_venda`, `acao_de_marca`, `contexto_bp`, `pendencias`).
   Sem isso o `refresh.py` para e avisa — de propósito.
2. `python refresh.py --mes AAAA-MM`
3. **Revisar o texto das duas páginas.** O `data.json` alimenta números de gráfico e tabela;
   as frases de análise são escritas à mão. As páginas trazem uma guarda que avisa no console
   do navegador se a soma do `data.json` divergir dos totais declarados no texto.
4. Conferir o aviso de anúncios sem influ identificado e completar o `MAPA` do `refresh.py`.

## Decisões de abordagem

- **Duas contas de custo, nunca somadas numa só rubrica.** No controle de custo marginal, cachê de
  influenciador e verba de tráfego são linhas diferentes; juntar dupla-conta o mês.
- **Mídia e receita saem da mesma tabela** (`dtm_analytics_facebook_ads_funnel`), para que spend e
  retorno sejam divisíveis. Ad é de influ quando o `nm_ad_name` traz o nome do influ ou a marcação
  `influ`/`inlfu` — mesmo critério do dashboard de Fluxo Contínuo.
- **Contar anúncio por `id_advertising`, nunca por `nm_ad_name`** — o mesmo nome roda em campanhas
  diferentes. Em ago/2026: 164 anúncios únicos contra 118 nomes distintos.
- **"Dias no ar" = `COUNTIF(qt_impressions > 0)`**, não `COUNT(DISTINCT reference_date)`. A tabela
  grava linha mesmo com o anúncio pausado.
- **Três recortes de receita, apresentados como cascata** — ver achados.

## Achados de agosto/2026

- **Gasto R$ 155.631** (anúncio R$ 143.631 + cachê R$ 12.000) → **retorno R$ 1,23** contando só as
  peças que rodaram; **R$ 1,54** no caixa do mês. Ação de marca (Première John Money) R$ 5.151 fora
  da conta; evento de R$ 35.280 excluído a pedido.
- **Venda atrasada é 20,5% da receita do canal** (R$ 49.054), contra **3,8%** na média da BP. As
  peças de influ são pausadas cedo e continuam vendendo; junho (R$ 703 mil) deixou muito resíduo.
- **A vantagem sobre a média da casa só existe na visão caixa.** Na régua justa (só peças que
  rodaram, dos dois lados): influs **1,33** contra **1,40** da empresa — abaixo, não acima.
- **39% da receita do anúncio foi fechada pelo time comercial** (R$ 93.690, 137 vendas, publisher
  `Sales Team`). Varia muito: Pedro Alaer 71%, Fran Otto 63%, Arthur Schreiber 56%, Diego Del Rio 9%.
  Essa venda paga comissão que não entra em nenhuma conta de retorno.
- **A verba por influ é decisão do algoritmo da Meta**, não do time. De 164 peças no ar, 22 receberam
  R$ 500+ e 82 ficaram com menos de R$ 1. O algoritmo escalou Josué Aragão (R$ 25,2 mil, 12× o cachê)
  e Alam Carrion (R$ 20,0 mil), ambos abaixo de R$ 1,00, e quase não usou Fran Otto (28 peças, 1
  escalada) nem Arthur Schreiber (27, 3).
- **3 dos 5 com cachê não se pagaram** — Alam Carrion R$ 0,79, Josué Aragão R$ 0,89, Mayara Ranni
  R$ 0,79 (só peças que rodaram). Levaram R$ 8.500 dos R$ 12.000.
- **Murillo Capellozzi e Diego Del Rio** entregaram R$ 1,55 por real **sem cachê registrado**, e são
  os únicos cujo número não muda entre as duas visões — resultado feito em agosto, sem cauda.
- **Venda por link/cupom do influ: R$ 1.774 em 4 transações.** O caminho acabou na prática.

## Validações feitas (03/set)

Queries em `queries/check_*.sql`:
- Sem dupla contagem — cada venda aparece em um único anúncio (137 vendas comerciais = 137 pares).
- Zero renovação nas 805 transações; todas aprovadas.
- Receita reconstruída venda a venda no `fct_transactions` = **R$ 239.784,65**, idêntica.
- Zero sobreposição entre os três caminhos de venda.
- Nenhum falso positivo de "influência"/"sem influs".
- Não verificável por natureza: a atribuição venda→anúncio é do modelo da casa.

## Pendências

1. Planilha de custo: linhas somam R$ 52.431,10, total declarado R$ 46.931,10 — **R$ 5.500** de
   diferença. Adotada a soma das linhas.
2. **R$ 84.031 de anúncio sem cachê registrado** (Murillo Capellozzi, Diego Del Rio, BR Explora,
   Pedro Alaer, Julliene Salviano). Se receberam, o retorno deles está superestimado.
3. **Comissão** das 137 vendas do comercial — pedir ao Comercial para a próxima edição.
4. **Gross-up de 12,15%**: se aplicável, retorno vai de R$ 1,23 para R$ 1,10 (a média da casa cai junto).
5. Levar à mídia o teste de isolar as peças de Fran Otto e Arthur Schreiber em conjunto próprio.
6. UTM/link próprio por influenciador — recomendação repetida desde julho.

## Wiki atualizada

- `wiki-brasil-paralelo/influenciadores.md` — rotina do fechamento, regra das duas contas de custo,
  cauda estrutural, verba decidida pelo algoritmo, decomposição direta × comercial, funil de peças.
- `wiki-bp/metricas-referencia.md` — números de agosto/2026.
