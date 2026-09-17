# Performance diária — de onde veio o dia (desenho, 15/09/2026)

**Pedido (André, 14/09):** um relatório que meça o impacto de cada dia, mostre de onde veio a
diferença de performance e quais alavancas estão funcionando, para sair do achismo — ou pelo
menos dar um caminho claro para essas análises.
**Origem:** rodada 9a do `relevancia-marca` mostrou que discutimos "por que vendeu" sem antes ter
"de onde veio" contabilizado. Este relatório fecha a primeira pergunta e aponta onde testar a segunda.

## O que ele responde e o que não responde

| Responde (contabilidade) | Não responde (causalidade) |
|---|---|
| Quanto do dia veio de cada canal de atribuição | Se o canal **causou** a venda |
| Quanto da variação em ads foi **gasto** e quanto foi **eficiência** | Se a eficiência veio da criatividade, do público ou do dia |
| Quanto foi **volume** e quanto foi **ticket/mix** | — |
| Em que **fase de campanha** o dia estava e quanto isso costuma valer | Efeito causal do fechamento de lote |
| Que **contexto exógeno** o dia tinha (YT orgânico, demanda não-mídia, estreias) | Se o contexto moveu a venda |
| Quais alavancas **andaram junto** com dias acima do esperado nos últimos 90 dias | Quais alavancas **fazem** o dia — isso é geo holdout / teste |

Regra de leitura no topo do relatório: **atribuição não é incrementalidade.** O relatório diz onde a
venda foi contada; a incrementalidade do gasto vem do custo marginal por evento (harness do MMM) e
de experimento.

## O modelo — decomposição em cascata

Para cada dia *d*: `real − esperado = Σ contribuições`, com o **esperado** = mesmo dia da semana nas
4 semanas anteriores na mesma fase de campanha (mediana), o baseline que o harness de overspend do
MMM já validou no evento 09–10/05. Baseline alternativo (para sensibilidade): MM28 pareada por
quintil de spend, como no `teste_pareado_spend.py`.

```
receita real
  = esperado
  + [1] volume × ticket ........ Δtx × ticket_base  |  tx × Δticket (mix de produto)
  + [2] por canal de atribuição . ads Meta · ads Google/PMax · CRM · Comercial · orgânico/portal · YouTube · influs · outros
  + [3] dentro de ads ........... Δspend ÷ CPA_base  (gastou mais)  |  spend × Δ(1/CPA)  (converteu melhor)
                                  por campanha (sigla) → mostra "escalou mantendo eficiência?" por dia
  + [4] fase de campanha ........ aquecimento · abertura (±3d) · meio · fechamento (−2..0) · sem campanha
                                  → efeito histórico médio da fase, dado o baseline
  + [5] contexto (não entra na soma; fica ao lado)
        YT orgânico ÷ MM28 · busca orgânica ÷ MM28 · Wikipedia MM7 · índice de demanda não-Meta ·
        estreias na plataforma no dia (mídia, playlist, audiência D0, IAC da playlist) ·
        abordagens Comercial (esforço) · leads do dia
```

[1] e [2]/[3] são decomposições **exatas** (fecham no real). [4] e [5] são **explicativas**.

### Alavancas — o que anda com dias acima do esperado

Tabela mensal, últimos 90 dias: para cada alavanca (spend por campanha, fase, YT orgânico alto,
estreia na plataforma, abordagens, disparos CRM), a diferença média do **resíduo** (real − esperado)
entre dias com e sem a alavanca, pareado por spend, com IC por bootstrap **e MDE declarado**.
Gate de honestidade: só entra como "alavanca que está funcionando" o que tiver IC fora de zero em
≥ 60 dias de observação e sobreviver à exclusão de dias de lançamento. O resto aparece como
"inconclusivo (MDE = x)".

## Fontes e o que já existe

| Bloco | Fonte | Já existe? |
|---|---|---|
| Vendas por canal/campanha/produto | `masterdata.fct_transactions` (publisher, utm_campaign, plano) | query 02 do relevancia-marca (estender por sigla + produto) |
| Spend e vendas por campanha | `dtm_analytics_facebook_ads_funnel`, `_google_ads_funnel`, `_pmax_ads_funnel` | query 30 do relevancia-marca |
| Fase de campanha | **`api-mappings/campaign_dashboards`** (pendente de deploy) → `dbt_abe.tb_campaign_period` corrigida | doc em `marketing-bp/docs/api-mappings.md` |
| Índice de demanda não-Meta | `mmm_project/scripts/09_bidding/06_demand_index.py` | sim, validado |
| Custo marginal por evento | `mmm_project/scripts/09_bidding/05_overspend_event.py` | sim, validado |
| YT orgânico, busca, referral | GA4 (MCP `ga4`, property 378996649) | série até 20/08; automatizar fetch diário |
| Wikipedia | API Wikimedia | `avaliar_fontes.py` |
| Estreias e audiência na plataforma | `obt_user_media_interactions`, `obt_kafka__view_sessions` | queries 09/21 do relevancia-marca |
| IAC por playlist | query 15 do relevancia-marca (com n mín. de compradores, rodada 9a) | sim |
| Abordagens Comercial | `dim_zenvia_approaches` (⚠️ recarga de 08/09 perdeu 72% de 01–04/09) | query 04 |

⚠️ Dois sistemas de atribuição: vendas por campanha do Meta (`qt_total_sales`) ≠ publisher da
`fct_transactions`. O relatório usa a `fct_transactions` como verdade do total e o Meta só dentro
do bloco [3]; a diferença aparece como linha própria ("atribuição Meta acima/abaixo do publisher").

## Entrega

Padrão template do portal: `index.html` + `data.json` + `refresh.py` + `queries/` + `ANALISE.md`.

- **Página 1 — o dia:** seletor de dia; cascata esperado → contribuições → real; ao lado, o contexto
  do dia e as estreias. Uma frase gerada: "13/09: +R$ 380k vs esperado; 71% gasto BP10, 18%
  eficiência BP10, 9% Comercial; YT orgânico 0,9× MM28".
- **Página 2 — a semana/mês:** mesma cascata agregada; tabela por campanha com gasto × eficiência;
  volume × ticket.
- **Página 3 — alavancas (90d):** tabela com efeito, IC, MDE e veredito (funciona / inconclusivo /
  não funciona), atualizada mensalmente.
- Refresh diário 9h (launchd, como o Zenvia), lendo D-2 fechado (CPA matura em D+2 — regra da wiki).

## MVP e ordem

1. Tabela diária `dbt_abe.tb_performance_diaria` (dia × canal × sigla × produto: spend, tx, receita)
   + `tb_contexto_diario` — 1 dia.
2. Decomposição [1]–[3] + baseline mesmo-DOW-4-semanas + cascata na página 1 — 1 dia.
3. Fase [4] quando a API estiver no ar (até lá, calendário hardcoded da wiki) — 0,5 dia.
4. Contexto [5] + página de alavancas com IC/MDE — 1 dia.
5. Validar em 3 dias conhecidos antes de publicar: 09–10/05 (overspend), 14/08 (Renan), 13/09
   (fechamento BP10). Os três têm veredito independente já medido.

## Decisões do André

1. Baseline: mesmo DOW × 4 semanas × mesma fase (proposta) ou MM28 pareada por spend?
2. Granularidade de canal: os 7 grupos acima ou o mapa de 10 canais do `canais.md`?
3. Publicar no portal (Mídia Paga) ou como card no marketing-bp?
4. Quem consome no dia a dia (squad CAC?) — define se a página 1 vale o esforço ou se a semanal basta.
