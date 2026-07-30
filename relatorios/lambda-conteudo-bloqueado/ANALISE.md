# Lambda · Campanha Conteúdo Bloqueado

## Pergunta original

O que aconteceu com os leads da campanha "Conteúdo Bloqueado" (upsell por clique em
conteúdo bloqueado, conduzidos pela ferramenta de IA **Lambda**, venda pelo link do
Gustavo Koetz / **C0113**)? O funil da campanha no `dtm_seller_conversion_rate` parecia
desconfigurado — mostrava vendas que não eram da Lambda. Pedido: entender os casos,
identificar as causas e especificar o que o time de implementação precisa mudar para
os resultados serem acompanháveis. (MM via Bárbara Olivieri, jul/2026.)

## Decisões de abordagem

- **Identificação da lista**: `nm_title LIKE 'UPSELL |%'` na fonte
  (`staging.int_pipedrive_analytics`) — mais robusto que `nm_label = 'Conteúdo bloqueado'`
  (hoje 100% coincidem; o label só passou a ser preenchido em 20/07/2026).
- **Venda Lambda**: regra canônica do Dashboard Lambda sobre `fct_transactions`
  (tracking `%C0113%` OU produto/oferta `%lambda%`), com `COALESCE(..., FALSE)` para o
  gotcha de NULL em LIKE.
- **Match lead × venda por pessoa** (email e telefone em joins separados + UNION), **não**
  pela atribuição do modelo — porque a atribuição do modelo é exatamente o que está quebrado.
- **Timing vs entrada na lista** (`MIN(dt_created_at)` do deal CB da pessoa) para separar
  compras antes/depois — é o corte que muda a interpretação.
- **Período**: desde 2026-07-15 (primeiras vendas C0113 da base; cards começam em 20/07 —
  as conversas rodam dias antes dos cards).

## Achados principais (30/jul/2026)

- **2.9k leads** na lista, criados em lotes (20, 24, 28, 29, 30/07), todos com owner
  `wellington.santos` / stage `9. OUTROS`. ~88% não comprou nada no período.
- **Funil oficial invertido**: o `dtm_seller_conversion_rate` mostra ~R$ 13k / 9 vendas na
  campanha — **nenhuma é da Lambda** (são de outros vendedores/links: C0034, C0086, C0088,
  C0104…, atribuídas por proximidade de data). As ~27 vendas reais da Lambda (~R$ 5,4k)
  caíram em outros deals ou fora do modelo.
- **Causa (código do modelo)**: o match venda↔deal prioriza owner do deal = vendedor da
  venda e desempata por recência. A campanha viola as premissas: owner errado
  (wellington ≠ gustavo.koetz), 67% das vendas C0113 sem `nm_salesman_email` (links
  "(Disparo/IA)"), e cards criados dias depois da conversa (22/25 vendas anteriores ao card).
- **Higiene da lista**: R$ ~140k comprados pela base ANTES de entrar na lista (65 vendas
  comerciais R$ 64k + 285 digitais R$ 76k — Aniversário/Clube do Livro, 53 vitalícios).
  Das 17 vendas comerciais humanas pós-lista (R$ 25k), **100% tinham vendedor humano na
  conversa** (14 já em abordagem antes da lista — carteira Mecenas, LINK ENVIADO; 3 atendidas
  entre a lista e a compra, verificadas por transcrição Zenvia). Não existe venda "de link
  frio" competindo com a Lambda.
- **Padrão de ticket**: humanos fecham vitalícios de R$ 1,5–5k nas mesmas pessoas em que a
  Lambda fecha Apoiador/Básico de R$ 120–228.
- **Cenário na geração dos leads (30/jul)**: no dia em que entraram na lista, cerca de metade
  da base tinha alguma pendência. Definição validada com o André: **abordagem humana ativa =
  deal humano aberto criado ≤60d OU contato Zenvia em `followUp` no grupo Comercial** (estado
  atual; followUp de Suporte/Retenção/CS não conta); deals abertos há +60d ficam separados
  como "zumbi" de propósito, para clareza. Números no `data.json`/relatório (seção 2). Flags
  com sobreposição: 402 (14%) em outra lista Lambda aberta (Abandono de Carrinho, Compra
  Negada, Oportunidade de Venda — 511 deals), 321 (11%) com compra nos 7 dias anteriores.
- **Conversas da IA nesta frente começaram só em 29/07** (origem `Conteúdo Bloqueado |
  <plano>` no `conversation_report_bp`: 127 conversas, 36 respondidas até 30/07) — as vendas
  C0113 de 15–28/07 vieram das outras automações da Lambda acima, atingindo as mesmas pessoas.
- **Contexto de operação**: o script de abertura dos vendedores humanos ("você NÃO está
  falando com um robô nem com uma IA") explodiu de ~1k para ~15k conversas/mês exatamente
  quando a Lambda entrou em operação (abr–mai/2026) — humanos e IA disputam a mesma base
  e o time sabe.
- **Efeito colateral a monitorar**: upgrade com "100% cashback" gerou refund de venda
  digital (Premium R$ 1.908 reembolsado ao fechar Black R$ 4.976) — infla o Comercial e
  penaliza o digital.

## O que tem que ser feito (handoff para implementação)

1. **Filtrar leads já em abordagem** na geração da lista: deal aberto, Zenvia
   followUp/carteira, outra lista Lambda ativa.
2. **Período de garantia de 7 dias**: excluir quem comprou em qualquer canal nos últimos
   7 dias.
3. **Regras de owner/stage**: deals da lista criados com `gustavo.koetz` /
   `10. AWSALES LISTA` para o `dtm_seller_conversion_rate` funcionar.

(Itens complementares — vendedor preenchido no checkout C0113 e card criado no disparo +
id de campanha no tracking — retirados do relatório a pedido do André em 30/jul para focar
a discussão nos 3 essenciais; seguem documentados na wiki `fluxo-comercial.md`.)

## Pendências / próximos passos

- Passar as correções ao time de implementação (Bárbara/Fred no loop — item na AGENDA).
- Após os fixes: **dashboard no marketing-bp** para acompanhamento contínuo (leads por
  lista, conversas, vendas C0113, receita, conversão, corte por campanha).
- Ponta aberta: cruzar o log de conversas da Lambda
  (`lambdalabs-gcp.iasmin_analytics.conversation_report_bp`, fora da região US — exige
  materializar) para medir influência da IA em vendas fechadas por outros canais.

## Queries

| Query | O que faz |
|-------|-----------|
| [desfecho_leads_conteudo_bloqueado.sql](queries/desfecho_leads_conteudo_bloqueado.sql) | Desfecho de compra de toda a base (Lambda / outro comercial / digital / nada) |
| [vendas_lambda_conteudo_bloqueado.sql](queries/vendas_lambda_conteudo_bloqueado.sql) | Vendas C0113 da base e onde cada uma caiu no modelo |
| [vendas_outros_vendedores_leads_cb.sql](queries/vendas_outros_vendedores_leads_cb.sql) | Vendas comerciais não-Lambda com timing vs entrada na lista |
| [dtm_seller_conversion_rate_cb_corrigida.sql](queries/dtm_seller_conversion_rate_cb_corrigida.sql) | Atribuição corrigida (venda Lambda → deal CB) + auditoria do modelo |

O `refresh.py` reimplementa os agregados dessas queries para gerar o `data.json`.

## Wiki atualizada

- `wiki-bp/pages/fluxo-comercial.md` — seção "Campanha Conteúdo bloqueado": identificação,
  lógica de atribuição do modelo (com código), desfecho da base, config quebrada dos links,
  gotcha das vendas anteriores ao card.

## Para retomar

- **Próximo passo**: apresentar este relatório + dossiê (artifact `e894772f`) e cobrar os
  5 fixes; depois especificar o dashboard no marketing-bp.
- **Wiki a carregar**: `fluxo-comercial.md` (tudo está lá) + `bq-regras.md`.
- **Contexto fora da wiki**: dossiê visual com timelines e os 14 casos documentados:
  artifact `https://claude.ai/code/artifact/e894772f-aa3c-45cb-9fc5-c6037a28e28c`.
