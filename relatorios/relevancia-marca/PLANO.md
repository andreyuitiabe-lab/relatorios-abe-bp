# Plano — Programa de medição de relevância → vendas

**Criado:** 25/08/2026 · **Base:** 4 rodadas de análise (`ANALISE.md`) + bibliografia (`REFERENCIAS.md`)

## O que já sabemos (não redescobrir)

- Não existe fator único de relevância; indicadores aprovados até aqui: **YouTube orgânico,
  busca orgânica (GA4), Wikipedia** (+ direto/referral com ressalvas). Social orgânico descartado.
- O efeito medido é **coincidente** (lag ≥1 ns) e **direcional, não causal** (teto de Gordon 2023).
- O efeito causal individual existe e é de **ativação da base**, não aquisição (sabatinas 1,44–1,65×).
- Nosso Trends é só **numerador** — sem denominador de categoria, confunde com spend.

## Fases

### Fase 1 — Share of Search com denominador de categoria  ⭐ ✅ EXECUTADA 25/08 — veredito: **coincidente forte (+0,58* controlado por spend), SEM lead** (o lead aparente era spend futuro: SoS antecede nossa escala de mídia +0,62*). Não move eficiência. Ver ANALISE.md rodadas 5–6
*A métrica validada de mercado (IPA/Binet/Hankins: ~83% do market share, lead 6–12m). Barata.*

| Passo | Detalhe | Esforço |
|---|---|---|
| 1.1 Lista de categoria | **DECISÃO DO ANDRÉ/TIME**: quem compõe a categoria? Proposta inicial a validar: Jovem Pan, Revista Oeste, O Antagonista, Gazeta do Povo, Pleno.News (+sugestões do time de marketing). Critério: marcas que disputam a mesma atenção/assinatura, não só "concorrentes ideológicos" | 1 conversa |
| 1.2 Coleta via pytrends | ⚠️ Gotcha: Trends normaliza pelo máximo do grupo e aceita 5 termos/payload → usar **BP como âncora fixa em todos os grupos** e re-escalar. Semanal, 5 anos, BR | 0,5 dia |
| 1.3 Backtest | SoS_BP (%) vs receita/vendas mensais 2021→2026; testar lead de 0–6 meses. ⚠️ Não temos market share externo — o alvo é a **nossa** receita (nível e crescimento) | 0,5 dia |
| 1.4 Métrica | Se lead confirmar: SoS mensal entra em `metricas-referencia.md` + acompanhamento; se não, documentar e encerrar | — |

**Critério de sucesso:** SoS com correlação ≥0,4 com vendas em algum lead 0–6m, robusta a subperíodos **e ao spend do mês alvo**. ⚠️ Lição: controlar só o spend do mês do indicador não basta — o SoS antecede spend.
**Kill:** sem sinal em nenhum lead → arquivar; ficamos com os indicadores diários da rodada 4.

### Fase 2 — Destravar fontes primárias (paralelo à Fase 1)

| Fonte | Ação | Quem destrava | Esforço |
|---|---|---|---|
| GA4 `newUsers` | Rodar no `avaliar_fontes.py` (acesso já existe) | eu | 30 min |
| **Search Console** | Pedir acesso à propriedade do site (impressões/cliques **por query** de marca — o volume real de busca, sem depender de budget) | André → time tech/SEO | pedido + 0,5 dia |
| **YouTube Analytics** | Permissão de Visualizador no Studio (integração pronta, `youtube-analytics/README.md`); ao chegar: `fetch` + rodar `mcac_vs_audiencia.py --audiencia yt_diario.csv` | André → time de conteúdo | pedido + 1h |
| Instagram/Meta Insights | Alcance orgânico e seguidores/dia via Graph API — só se as acima não bastarem | opcional | 1 dia |

**Entregável:** `data/painel_relevancia.csv` + script único de refresh com todos os indicadores
aprovados; re-rodar a tabela da rodada 4 com as fontes novas.

### Fase 3 — Métrica operacional no dia a dia

1. **Termômetro de eficiência para mídia**: YouTube orgânico (ou views reais do YT, quando chegarem)
   como desvio da MM28 dentro da faixa de spend — regra de leitura junto ao mCAC de referência.
   **DECISÃO**: entra como card no dash de mídia do marketing-bp? (item já na AGENDA)
2. **Relatório HTML no portal** (padrão template: `index.html` + `data.json` + `refresh.py`) com o
   painel de relevância + IAC-14 mensal — só se o time for consumir recorrentemente.

### Fase 4 — Geo lift (o salto para causal) — condicionada a sponsor

*Único desenho que supera o teto de Gordon 2023. Custo real: variar mídia por região.*

| Passo | Detalhe |
|---|---|
| 4.1 Viabilidade | Checar granularidade regional: vendas por UF temos (`dim_contact`); **spend Meta por região não está no dtm** — exigiria breakdown via API. Sem isso, GeoLift não roda |
| 4.2 Desenho | GeoLift (open source da Meta) com holdout de 2–4 UFs médias por 4–6 semanas, medindo vendas orgânicas + eficiência |
| 4.3 Decisão de negócio | Reduzir mídia em praças = custo de receita no trimestre. Precisa de sponsor (mídia/diretoria). Levar proposta com estimativa de custo do teste |

**Gate:** só desenhar 4.2 se 4.1 confirmar viabilidade E houver sponsor.

### Fase 5 — MMM/UCM com componente de marca (médio prazo)

*Destino metodológico (Cain/Marketscience): marca eleva baseline + eficiência da ativação; medir
via Unobserved Components, nunca métrica de marca direto na equação.*

- **Insumos que já existem**: Wikipedia e Trends têm histórico retroativo completo (a série de
  marca NÃO é o limitador); spend BQ desde ago/2025 + planilhas 2022–2026 já extraídas na
  calculadora de público (`ads_spend_dia_campanha.csv`, ⚠️ subreporta até −32% — usar como piso).
- **Conexão**: aproveitar o `mmm_project` (curva de resposta bayesiana já rodada) — adicionar
  componente de marca ao desenho em vez de projeto novo.
- **Quando**: após Fases 1–2 definirem QUAL série de marca entra; alvo 2026Q4.

### Pendências herdadas das rodadas (não perder)

- Formato vs pauta: comparar as 9 sabatinas por notoriedade do entrevistado (BP Entrevista 2,70× > sabatina 1,98×)
- Horizonte D+14 → D+60/90 no efeito de ativação (não-membro converte em ~421d)
- Recheck do freemium negativo em ~out/2026 (n pequeno)
- mCAC × audiência com views reais do YT (destrava com a Fase 2)
- Portal Mixpanel: reavaliar 2026Q4

## Ordem e dependências

```
Semana 1:  [1.1 decisão categoria] → [1.2 coleta] ─┐        [2: pedidos SC + YT]
Semana 2:  [1.3 backtest] → [1.4 métrica]          ├→ [2: painel consolidado]
Semana 3:  [3.1 decisão termômetro no dash] ← ─────┘
Depois:    [4 geo lift, se sponsor]   [5 MMM, 2026Q4]
```

## Decisões que só o André/time podem tomar

1. **Lista da categoria** (Fase 1.1) — bloqueia a fase-prioridade.
2. **Pedidos de acesso**: Search Console e YouTube Studio (Fase 2).
3. **Termômetro no dash de mídia** — sim/não e onde (Fase 3).
4. **Apetite para geo test** — envolve reduzir mídia em praças (Fase 4).
