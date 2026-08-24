# Plano — Recomendador diário de budget Meta Ads (validado)

**Data:** 2026-07-23 (substitui a proposta de 06/jul)
**Status:** aprovado para execução; hipóteses validadas em [VALIDACOES.md](VALIDACOES.md)
**Bibliografia:** [REFERENCIAS.md](REFERENCIAS.md) (4 rodadas de pesquisa, 8 teses)

---

## Decisão estrutural

Unificar os dois esforços paralelos: a lógica vive no **`mmm_project/src/bidding/`**
(Etapas 1–4b já implementadas e validadas no evento 09-10/mai); esta pasta
(`midia-paga/`) vira o **front** — dashboard, ANALISE, validações. O sistema é um
**guardrail** (freio ABS), não um otimizador: evita os eventos caros (R$31–73k por
episódio tipo 09-10/mai) e captura headroom óbvio. Direção em 1–3 dias; magnitude
confiável só do lado REDUZIR.

## Desenho do recomendador (cada linha validada — ver VALIDACOES.md)

```
por campanha [VENDA], toda manhã, com dados D-2..D-4 (H2: dado estabiliza em D+2):
  teto_dia = margem% × ticket_30d(campanha) × demand_index(ontem)
             (H5: teto segue ticket, não segmento · H3: ontem vence qualquer modelo
              · override manual p/ transição de calendário)
  LAN com MA3 de spend subindo → SEM recomendação; nunca "reduzir" se ROAS_3d > 1
             (H4: nenhum sinal discrimina no ramp)
  LAN pós-pico → Abordagem C: ratio CPA_3d/CPA_acum (>1.30 reduzir · <0.85 aumentar)
             (H4: pós-pico discrimina forte — 1.09/0.92/0.69)
  PPT → mCAC do pooling por segmento×faixa vs teto_dia
             (H1: mCAC medido, placebo limpo — não curva ajustada)
  passo máx ±20-25% (H1 dose-resposta: 25-50% → R$132; >50% → R$196, cruza o teto)
  reavaliar mudanças só com ≥48h (pacing da plataforma)
  registrar TUDO no decision log (recomendação vs ação do gestor vs resultado)
```

## Números de calibração já medidos (pooling, 307 eventos, fev/2024–jul/2026)

| Segmento | mCAC mediano | IC90 | Leitura |
|---|---|---|---|
| LAN-up | R$145 | 129..196 | escalar LAN vinha sendo eficiente |
| LAN-down | R$250 | 193..304 | os cortes em LAN aconteceram certos |
| PPT-up | R$188 | 151..261 | escalar PPT está no limite do teto |
| PPT-down | R$188 | 144..274 | — |

## Execução

### Semana 1 — guardrail em shadow mode

| Entregável | Detalhe | Gate |
|---|---|---|
| Fase 0: unificação | Reconciliar adstock 8d vs 14d (walk-forward decide); ANALISE.md aponta pro backbone; re-verificar campanhas "com espaço" sob desconfundimento | Documento canônico único |
| Recomendador v1 | Estender `08_recomendar_orcamento.py` com as rotas acima (portar `signal_C`, janela D-2..D-4, teto por ticket com margem% provisória, silêncio no ramp) | — |
| Decision log | Tabela BQ `dbt_abe.tb_budget_decisions` + escrita no cron; D+1 preenche ação real e resultado | Ativo desde o dia 1 |
| Dashboard | Padrão `index.html` + `data.json` + `refresh.py`; 1 linha por campanha: gasto atual → recomendado → ação → confiança | — |
| **Walk-forward completo** (jan/2026–jul/2026) | Critérios: corta 09-10/mai; NÃO corta 21-27/mai; ordem ROAS por bucket ≥ backtest C (1.45/1.15/0.75) | **Se falhar, não entra nem em shadow mode** |
| Snapshots diários do extract | Confirma bucket D+0-1 do H2 (n era 46) | — |

### Semana 2 — calibração

| Entregável | Detalhe | Gate |
|---|---|---|
| Pooling produtizado | `pooling_placebo_test.py` → módulo com refresh mensal; granularidade segmento×faixa de gasto | Placebo continua limpo a cada refresh |
| Margem% via `08_ltv` | Fecha o teto por ticket (única pendência de dado do H5); valida se R$180 deriva de margem (Dorfman-Steiner) | — |
| Calibração lift | Incorporar `pdf_meta_conversion_lift.pdf` existente como âncora causal inicial | — |

### Shadow mode (2-4 semanas)

Sistema recomenda, gestor decide livre, decision log registra ambos. Métricas de saída:
**adesão** (% recomendações seguidas) e **acerto** (ROAS 3d de seguidas vs ignoradas —
as divergências do gestor são quasi-experimentos de graça). Critério pra "valer":
adesão >50% e dias seguidos ≥ dias ignorados em resultado. Se adesão baixa, o problema
é interface/confiança (critério do Little) — redesenhar o front, não o modelo.

### Contínuo (pós shadow mode)

- **Micro-experimentos**: rodízio de ±15-20% × 3-4 dias em 2-3 PPT estáveis, agendado
  pelo pipeline, analisado pelo mesmo estimador do pooling. Mata a endogeneidade
  "escalar no calor" dos saltos naturais.
- **Lift test**: 1-2/ano nos picos de gasto (Gordon 2023: pooling é direcional; a âncora
  causal é experimento).
- Refresh mensal do pooling; monitorar drift do mCAC por segmento.

## O que foi descartado (com evidência — não reabrir)

| Ideia | Por quê | Onde está o teste |
|---|---|---|
| Curvas por campanha como gatilho de decisão | 58% de acerto vs 60% do chute; Spearman 0.14 | `scripts/identification_test.py` |
| Ajuste por CPM (LiftLab) | CPM explica 5% da var do CAC; spend fita melhor que impressões em 14/16 | `scripts/cpm_decomposition.py` |
| Camada bayesiana hierárquica | Poliria curvas sem validade por evento | VALIDACOES.md + REFERENCIAS.md (Dew 2024) |
| Modelo de previsão de demanda | Ontem vence (MAE 0.243 vs 0.289) | VALIDACOES.md H3 |
| Curva de maturação de conversões | Dado estabiliza em D+2; basta lag de 2 dias | VALIDACOES.md H2 |
| Teto fixo por segmento | Razão de tickets instável (1.06–2.25/tri) | VALIDACOES.md H5 |
| TVP/Kalman, bandits formais, granularidade ad set, mais formas funcionais | Sem throughput/decisão que justifique; côncava resolvido (Simon & Arndt 1980) | REFERENCIAS.md |

## Decisões que precisam do time (antes ou durante semana 1)

1. **Teto dinâmico** — aceitar `margem% × ticket × demanda` no lugar do R$180 fixo?
   (No evento de maio, teto efetivo teria sido ~R$129.)
2. **Micro-experimentos** — gestores topam variações programadas de ±15-20% em PPT estáveis?
3. **Adesão ao shadow mode** — combinar com os gestores o rito (olhar o dashboard de manhã,
   registrar quando divergirem e por quê).

## Esforço

Semana 1 + Semana 2 = **~2 semanas de construção**, depois shadow mode (2-4 semanas de
operação assistida, sem custo de desenvolvimento relevante).
