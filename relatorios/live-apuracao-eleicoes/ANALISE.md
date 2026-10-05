# Live da Apuração (04/10/2026) — inserções da Black November

## Pergunta original

André (05/10): na live de apuração do 1º turno, fizemos inserções apresentando a oferta. Qual foi o impacto? Teve pico de views na LP? Quanto converteu? Depois: o que as pessoas compraram?

Meta verificável: para cada fala da oferta, views da LP e vendas nos minutos seguintes; total de vendas e receita da live; mix de oferta × perfil do comprador.

## Decisões de abordagem

- **Identificação da LP pelos dados**: páginas com maior salto de views no domingo 04/10 contra o domingo 27/09 → `vd./seja-membro/black-november-2026` (34,5k views, zero na semana anterior), checkout `go./subscribe/mkt-anual-assine-por-r-1-90…`.
- **Atribuição de venda pela UTM** `utm_content=apuracao_eleicoes_04out` (campaign `lan_bno26`, source `organic_youtube`, medium `programas`), que chega até a `fct_transactions`. Não pelo `nm_pptc_tracking_publisher`, que marca essas vendas como `Adwords Remarketing` (errado).
- **Horários das falas pela transcrição do YouTube**, não pelos picos. A 1ª versão inferiu 12 "inserções" a partir de picos na LP; a transcrição mostrou 9 falas reais — 3 picos não tinham fala (16:00, antes da live; 17:40–17:55; 19:45). Horário = `release_timestamp` (16:09:13) + minutagem da legenda; conferido pela fala "acabou de dar 5 horas", que cai em 17:01. Fica em `falas.json` (dado fora do BQ, versionado).
- **Janela por fala**: vendas do bloco de 5 min da fala até +30 min ou até a fala seguinte; views da LP em 15 min. É janela de tempo, não rastreio individual.
- **Perfil do comprador por e-mail**, 10 min antes da 1ª compra (para não contar a assinatura recém-criada): membro ativo (assinatura `paid` vigente), ex-membro, já comprou sem assinatura, novo na base.
- **Granularidade minuto** via export GA4 no BigQuery (`bp-lake.analytics_378996649.events_*`), não MCP do GA4 (MCP não filtra por página — ver wiki mcp-ga4).

## Achados principais

- **7.130 vendas novas / R$ 438k em 04/10** pelo link da live (+105 / R$ 26k em 05/10; total 7.235 / R$ 463k). O dia teve 8.432 vendas novas contra mediana de 1.117/dia nas 4 semanas antes (7,5×). As vendas fora da live (1.302) ficaram na faixa de um domingo normal.
- **Cada uma das 9 falas gera pico na LP no mesmo bloco de 5 min; 88% das vendas do dia entraram nos 30 min seguintes a uma fala.**
- **Melhor fala: 20:33 — 1.426 vendas, R$ 74k em 30 min**, a primeira que disse o preço (R$ 1,90). Falas com preço: ~20 vendas por 100 views da LP; antes, ~16.
- **Audiência manda**: 16:29 e 17:22 (150–200 mil no ar) venderam 99 e 121; das 18h em diante (465–528 mil) cada fala vendeu 540–1.430.
- **Falas do Clubinho do Livro (17:00, 22:33) não mexem na LP da Black.**
- **O que compraram**: Apoiador 12x R$ 1,90 = 6.168 vendas (85%) e R$ 141k (30% da receita). Essencial R$ 238,80 = 389 (R$ 92k); Premium R$ 478,80 = 179 (R$ 86k); order bump 2º ano = 108 (R$ 34k); Comercial = 356 (R$ 106k).
- **Quem comprou** (7.098 pessoas): 66% novos na base, 25% ex-membros, 8% membros ativos. 8% dos novos e 12% dos ex-membros levaram Essencial ou mais.
- **Membros ativos**: 222 fecharam com o Comercial (upgrade) e 287 compraram o Apoiador de R$ 1,90 já tendo assinatura — a checar (renovação antecipada? outra pessoa da família?).

## Pendências / próximos passos

- **Espectadores simultâneos não estão no relatório** (decisão do André, 05/10: deixar como anotação). A YouTube Analytics API não dá audiência por minuto — só pico/média da live e retenção em 100 pontos (mistura ao vivo e gravação) — e em 05/10 ainda não tinha a live (atraso ~2 dias). A série por minuto só existe no YouTube Studio.

- Explicar os picos sem fala (17:40–17:55 e 19:45): QR na tela sem fala, comentário fixado, post? Perguntar a quem operou a live.
- Investigar os 287 membros ativos que compraram o Apoiador.
- Corrigir na origem o publisher `Adwords Remarketing` para UTM `organic_youtube` (avisar dados/dbt).
- Retenção do Apoiador R$ 1,90: só dá para medir na renovação (out/2027) ou por consumo na plataforma nos próximos 30 dias.
- Se houver live no 2º turno: dizer o preço desde a 1ª fala e concentrar as falas no horário de maior audiência (18h–21h).

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [lp_checkout_5min.sql](queries/lp_checkout_5min.sql) | Views da LP e do checkout por 5 min (GA4) | ✅ |
| [vendas_5min.sql](queries/vendas_5min.sql) | Vendas com a UTM da live por 5 min | ✅ |
| [vendas_diarias.sql](queries/vendas_diarias.sql) | Vendas novas por dia, 06/09–05/10 | ✅ |
| [ofertas.sql](queries/ofertas.sql) | Vendas por degrau de oferta | ✅ |
| [perfil_cesta.sql](queries/perfil_cesta.sql) | Comprador × maior plano × perfil antes da compra | ✅ |
| [funil.sql](queries/funil.sql) | Usuários GA4 na LP e no checkout | ✅ |

`falas.json`: horários e frases das falas (transcrição do YouTube). `refresh.py` → `data.json`.

## Wiki atualizada

- `wiki-brasil-paralelo/pages/campanhas-calendario.md`: linha BNO26 — live de apuração (UTM, números, falas, publisher errado).
- `wiki-bp/log.md`: duas entradas (NEW + CORRECAO das inserções).
