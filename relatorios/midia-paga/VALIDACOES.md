# Validações pré-implementação — 23/jul/2026

Cada hipótese do plano ([PROPOSTA.md](PROPOSTA.md) + plano enxuto) testada **antes** de
implementar, com critério de reprovação definido antes de rodar. Dados:
`dtm_analytics_facebook_ads_funnel` fev/2024–jul/2026 (7.6k campanha-dias VENDA) +
`fct_transactions` (demanda) + snapshot local de 3/jun (restatement).

| # | Hipótese | Veredito | Consequência no desenho |
|---|---|---|---|
| H1 | Pooling de saltos naturais com controles do mesmo dia | ✅ **PASSA** | Vira a fonte de calibração do mCAC |
| H2 | Maturação de conversões exige curva de correção | ⚠️ **SIMPLIFICA** | Correção = usar janela D-2..D-4; sem curva |
| H3 | Regressão prevê demand_index de amanhã | ❌ **REPROVA** | Usar índice de ontem + override manual de calendário |
| H4 | Detector de regime LAN (curva vs C) | ⚠️ **REDESENHA** | C só pós-pico; no ramp o sistema silencia |
| H5 | Teto fixo por segmento (PPT/LAN) | ❌ **REPROVA** | Teto por ticket rolling da campanha (margem% pende do 08_ltv) |

## H1 — Pooling + placebo (`scripts/pooling_placebo_test.py`)

Estimador: por salto (|Δspend|≥25%, base 3d estável), contrafactual = mediana do ratio
vendas_pós/pré das campanhas do **mesmo tipo, estáveis no mesmo dia** (≥3 controles).
mCAC = Δspend / Δvendas_ajustado. Histórico fev/2024–jul/2026: **307 eventos** (mediana
6 controles), 1.377 placebos.

- **Placebo limpo**: Δvendas_adj relativo mediano **+0.000** (IC90 −0.015..+0.025), 50% positivo.
- **Separação**: 79% dos saltos-up com Δvendas_adj>0 vs 50% no placebo.
- **mCAC por segmento** (mediana, IC90 bootstrap):

| Segmento | n | mCAC | IC90 |
|---|---|---|---|
| LAN-up | 86 | **R$145** | 129..196 |
| LAN-down | 114 | R$250 | 193..304 |
| PPT-up | 53 | **R$188** | 151..261 |
| PPT-down | 54 | R$188 | 144..274 |

- **Dose-resposta (concavidade medida quasi-experimentalmente):** saltos moderados
  (25-50%) → mCAC R$132 (n=47); saltos grandes (>50%) → **R$196** (n=61). O step-limit
  de ±20-25% deixou de ser convenção da Meta: é a fronteira medida onde o mCAC cruza o teto.
- Ressalva (Gordon 2023): endogeneidade de seleção da campanha persiste — direcional.

## H2 — Restatement / maturação

Snapshot de 3/jun (2.555 campanha-dias) vs datamart em 23/jul:

| Idade do dado no snapshot | Δspend depois | Δvendas depois | CPA snapshot/final |
|---|---|---|---|
| D+0-1 | +135% | +83% | **0.78×** |
| D+2-3 | 0% | −2% | 0.98× |
| D+4+ | 0% | −1..−2% | ~1.00× |

- Datamart **é restated**, mas estabiliza rápido: em D+2 o CPA está a 2% do final.
- **Direção do viés invertida vs hipótese**: no dado fresco o *spend* atrasa mais que as
  vendas → CPA de ontem parece ~22% **melhor** que o real. Risco = escalar em eficiência
  ilusória, não cortar por pessimismo.
- **Regra**: qualquer janela de decisão usa D-2..D-4. Sem curva de maturação, sem snapshots
  contínuos. Confirmar com mais 1-2 pares de snapshot na semana 1 (bucket D+0-1 tinha n=46).

## H3 — Previsão de demanda

Walk-forward 236 dias (série ago/2025–jul/2026, expanding window):

| Método | MAE |
|---|---|
| **Baseline: índice de ontem** | **0.243** |
| Regressão DOW+MA7+lag1 | 0.289 |
| MA7 | 0.302 |
| Mesmo DOW semana passada | 0.392 |

Nos dias extremos (idx>1.5 ou <0.6, n=96): ontem 0.251 vs regressão 0.391. Demanda é
persistente (ondas de campanha duram dias). **Usar índice de ontem**; transições de
calendário entram como override manual do gestor, não como modelo.

## H4 — Regime LAN (85 LAN ≥15 dias; verdade = pré-pico do MA3 de spend)

Heurísticas de detecção reprovam o critério estrito (melhor: "MA3 subindo", recall 77%,
precisão 56%; ramp mediano = 9 dias, p75 16). Mas o subteste decisivo — **Abordagem C
por fase** — muda o desenho:

| Fase | aumentar | manter | reduzir |
|---|---|---|---|
| Ramp | 1.01 | 1.15 | 1.17 (ordem invertida — C **não** discrimina) |
| Pós-pico | 1.09 | 0.92 | **0.69** (discrimina forte) |

**Refina a conclusão do ANALISE.md §9**: C vale para LAN **pós-pico**, não no ciclo todo.
No ramp nenhum sinal discrimina (consistente com wear-in, ADPULS). Regra operacional:
LAN com MA3 de spend subindo → **sem recomendação** (plano de lançamento manda; nunca
emitir "reduzir" com ROAS_3d>1); MA3 caindo/estável → Abordagem C. Custo dos 23% de ramp
não detectados é limitado (ROAS mediano 1.17 nos dias "reduzir" do ramp).

## H5 — Teto por segmento

Razão de tickets LAN/PPT por trimestre: 1.06 → 2.25 (instável — depende do produto que
está lançando; Q2/2026 teve lançamento de ticket R$502). Segmento fixo não é a unidade:

- **Teto por campanha = margem% × ticket rolling 30d da própria campanha.**
- Margem% (a constante) pende de rodar `mmm_project/scripts/08_ltv` — única pendência de dado.
- Consistência com H1: teto implícito por ticket de LAN (~R$288 no agregado) explica o
  mCAC LAN-up de R$145 ter sido eficiente; PPT-up R$188 raspando o teto R$180.

## Desenho final do recomendador (pós-validações)

```
por campanha, toda manhã (dados D-2..D-4):
  teto_dia = margem% × ticket_30d(campanha) × demand_index(ontem)   [+ override calendário]
  LAN com MA3 spend subindo  → SEM recomendação (nunca "reduzir" se ROAS_3d>1)
  LAN pós-pico               → Abordagem C (ratio 3d vs acumulado)
  PPT                        → mCAC do pooling por segmento×faixa vs teto_dia
  passo máx ±20-25% (fronteira medida no dose-resposta), reavaliar em 48h
  registrar em decision log (recomendação vs ação vs resultado)
```

## Pendências pra implementação

1. Rodar `08_ltv` → margem% por produto (fecha H5)
2. +1-2 pares de snapshot pra confirmar D+0-1 (fecha H2)
3. Walk-forward do recomendador completo (gate da semana 1, critérios já definidos)
4. Shadow mode 2-4 semanas com decision log

## Scripts

| Script | Testa |
|---|---|
| [scripts/cpm_decomposition.py](scripts/cpm_decomposition.py) | Tese LiftLab/CPM (descartada) |
| [scripts/identification_test.py](scripts/identification_test.py) | Identificação das curvas (Dew et al.) |
| [scripts/pooling_placebo_test.py](scripts/pooling_placebo_test.py) | H1 — pooling + placebo |

H2-H5 rodados ad-hoc (código nos blocos desta sessão; H4/H5 usam `camp_daily_full.csv`
= extração fev/2024+ com impressões — recriar via `all_camps.sql` estendida).

---

# Teste out-of-sample em 4 campanhas nomeadas — 24/jul/2026

> **Relatório visual:** [validacao_modelos.html](validacao_modelos.html) — trajetórias das 4 campanhas, comparação de sinais e curva de stop-loss.

Pedido: rodar as modelagens em DOM, ELS, EVG, BMA e ver se funcionam. Agregado por
sigla (a curva de saturação é do lançamento inteiro, não do sub-anúncio). Cada dia D:
sinal com dados até D, comparado com ROAS realizado em D+1..D+3. Script:
`scripts/analise_siglas.py` + `avaliacao.py`. Dados: extração `siglas4.csv`.

As 4 cobrem casos distintos de propósito:
- **DOM** (Domingo Sem Deus): LAN completa e limpa, R$1,16M, ROAS 1.20
- **ELS** (El Salvador): LAN multi-onda relançada 3× (mai→jul), R$4,3M, ROAS 1.29
- **EVG** (Brasil Evangélico): LAN nascida ruim, 9 dias, ROAS 0.45, CPA R$459
- **BMA** (Raio-X Banco Master): LAN→PPT (lançamento virou perpétua)

## Veredito: funcionam parcialmente. Abordagem C sozinha tem 2 pontos cegos.

Comparação sinal C (relativo, CPA_3d/CPA_acum) vs regra absoluta (CPA_3d vs teto + ROAS_3d),
ROAS mediano 3d dos dias marcados "reduzir":

| Sigla | C: reduzir (n/ROAS3d) | Absoluta: reduzir | Leitura |
|---|---|---|---|
| DOM-LAN | 3 / 1.09 | 3 / 1.09 | Empatam; C pouco ativo. Aumentar 1.50-1.58 (escalar foi certo) |
| ELS-LAN | 21 / **1.13** | 12 / **1.02** | C **corta demais** — reduzir com ROAS>1 |
| EVG-LAN | — (só manter 0.62) | 6 / **0.48** | C **cego**; só a absoluta pega a catástrofe |
| BMA-PPT | 8 / 0.95 | 13 / 0.95 | Nenhuma discrimina (ordem não-monotônica) |

### O que funciona
- **DOM (LAN completa saudável)**: C discrimina bem — aumentar 1.50 > manter 1.21 >
  reduzir 1.09, monotônico. Escalada corretamente premiada. É o caso do backtest original.

### Onde quebra (2 pontos cegos de C, ambos resolvidos pela regra absoluta)
1. **Lançamento nascido ruim (EVG) é invisível a C.** C é sinal *relativo* (recente vs
   baseline próprio); uma campanha uniformemente ruim (CPA 400-600 desde o dia 0, ROAS 0.4)
   tem ratio ≈ 1.0 → "manter" pra sempre. EVG queimou ~R$69k em 9 dias e C nunca alertou.
   Só a **regra absoluta (CPA_3d > teto)** pega — e pega limpo (reduzir ROAS 0.48).
2. **Multi-onda (ELS) enviesa C pra cortar.** O CPA_acumulado ancora na 1ª onda barata
   (CPA 59-120 em mai); toda onda de jun/jul (CPA 180-250) parece "cara" → 21 "reduzir",
   dos quais a mediana teve ROAS 1.13 (cortaria dias ainda lucrativos). Baseline deveria
   ser **rolling/por-onda**, não acumulado da vida toda.

### Dois achados adicionais
3. **O overspend canônico do DOM (09/mai, +114% num dia) NÃO foi pego por C** ("manter 1.00"):
   a janela de 3d inclui 2 dias baratos pré-spike e o baseline de 60d dilui. **Quem barra é o
   step-limit ±20-25%** (+114% ≫ limite), não o sinal C. Confirma o step-limit como proteção primária.
4. **Detector de regime por pico global de MA3 é frágil.** No DOM, o spike tardio de 09/mai
   colocou o "pico" no dia 65/71 → quase toda a campanha classificada como ramp. Em ELS
   multi-onda, pico no dia 11 ignora as re-rampas de jun/jul. Precisa de definição de
   regime robusta a ondas (reset por salto sustentado, não máximo global).
5. **PPT de baixo volume (BMA-PPT, 8-30 vendas/dia) é ruído** pra qualquer sinal diário —
   ordem não-monotônica nas duas regras. Confirma o desenho: PPT usa mCAC do **pooling por
   segmento**, não sinal diário por campanha.

## Consequências para o desenho (reforçam, não derrubam, o plano)

- **A regra absoluta (CPA vs teto) deve valer também para LAN**, como piso — não só PPT.
  Era a "rota PPT" do desenho; o teste mostra que é mais robusta que C nos casos difíceis.
  Ordem: `reduzir se (C=reduzir) OU (CPA_3d > teto E ROAS_3d < 1)`.
- **O silêncio no ramp precisa de exceção de catástrofe**: EVG estava em ramp com ROAS 0.4.
  A regra "nunca reduzir se ROAS>1" já permite alertar (ROAS<1), mas o "sem recomendação"
  primário engolia o alerta. Explicitar: ramp com ROAS_3d < ~0.7 e CPA_3d > teto → ALERTA.
- **Baseline de C deve ser rolling (ex. 14-21d ou desde o último salto sustentado)**, não
  acumulado — senão campanhas longas/multi-onda sofrem viés de corte.
- Step-limit e detector de regime robusto a ondas continuam sendo o que segura os eventos
  grandes (DOM overspend). Nenhum sinal diário relativo os pega sozinho.

---

# Stop-loss de campanhas — quão cedo dá pra prever o fracasso (24/jul/2026)

Objetivo reenquadrado pelo André: medir o **potencial** de uma campanha cedo, matar/pivotar
as que não vão ser rentáveis antes de sangrar. Testado em **22 LANs** (sigla-nível,
≥10d, ≥R$50k, fev/2024–jul/2026). Script: `scripts/stoploss_analise.py`.

## O sinal precoce prediz o destino — mas só a partir do dia 5

Spearman(ROAS acumulado até dia K, ROAS final da campanha):

| Janela | Spearman | Leitura |
|---|---|---|
| dia 1-3 | +0.52 | Ruidoso — learning phase, campeões começam com 0 venda (CDL: ROAS3=0, final 3.01) |
| **dia 1-5** | **+0.75** | Forte. Ponto onde o sinal fica confiável |
| — | | ROAS > CPA como métrica: CPA explode com poucas vendas iniciais (Spearman CPA5 só −0.41) |

**ROAS é a métrica certa de stop-loss, não CPA** — normaliza pelo ticket (resolve o
problema H5: ticket varia de R$180 a R$500 entre lançamentos). EVG (que a Abordagem C
não pegou) tinha ROAS 0.36-0.45 desde o dia 1 → pego trivialmente por ROAS, invisível por
ratio relativo.

## Curva de decisão: recall (pega perdedoras) × precisão (não mata vencedoras)

Perdedora = ROAS_final < 1.0 (10 de 22). O threshold **sobe com o tempo** porque a
incerteza cai:

| Dia do corte | Threshold | Recall | Precisão | Vencedoras mortas por engano |
|---|---|---|---|---|
| 3 | 0.7 | 40% | 57% | **CDL (3.01!)**, PAP, HDF — perigoso, mata campeão em learning |
| **5** | **0.7** | 50% | **83%** | só PAP (1.10, marginal) |
| **7** | **0.7** | 50% | **100%** | nenhuma |
| 7 | 0.8 | 60% | 86% | PAP |
| 10 | 0.9 | 90% | 90% | só HDF (1.04, marginal) |
| 10 | 1.0 | 100% | 91% | só HDF |

## Regra de stop-loss recomendada (escalonada)

Não é um corte único — é uma escada, o threshold sobe conforme a confiança:

```
dia 1-3: NÃO matar (learning). Se ROAS_3 < 0.7 → congelar budget (não escalar),
         marcar "em observação". Nunca hard-kill aqui (mataria CDL-like).
dia 5:   ROAS_5 < 0.7 → PIVOTAR (precisão 83%). É o primeiro corte seguro.
dia 7:   ROAS_7 < 0.7 → PIVOTAR (precisão 100% no histórico).
dia 10:  ROAS_10 < 0.9 → PIVOTAR (recall 90%, precisão 90%).
```

Usar ROAS acumulado (não diário), janela de decisão D-2..D-4 (maturação, H2).

## Potencial de economia (regra ROAS_5 < 0.8 → pivotar)

- Gasto pós-dia-5 em perdedoras flagadas: **R$4,5M** (dominado por BNO25, R$4,46M — uma
  única perdedora gigante; sozinha justifica o mecanismo)
- Custo do falso positivo (vencedoras flagadas, PAP+HDF): **R$840k**
- Razão ~5:1 a favor. Mas o custo de matar um campeão é assimétrico — por isso a escada
  começa conservadora (só congela) e só hard-mata quando a precisão históricos ≥ 83%.

## Caveats honestos

1. **N=22** — curva indicativa, não precisa. Recalibrar com mais lançamentos.
2. **"Perdedora = ROAS<1.0" ignora backend/CRM.** BP tem valor de CRM pós-venda; o
   breakeven real pode ser ROAS < ~0.8. Calibrar o threshold com margem/LTV (mesmo
   `08_ltv` pendente do teto). Enquanto isso, ROAS 0.7 é piso conservador.
3. **BNO25 domina a economia** — sem ela a razão cai. O valor vem de pegar poucas
   perdedoras grandes, não muitas pequenas.
4. Isto complementa a Abordagem C, não substitui: C cuida da *degradação ao longo* de uma
   campanha saudável; o stop-loss cuida do *diagnóstico de potencial* nos primeiros dias.

---

# A curva que se move no tempo — teste da formulação retorno = f(investimento) (24/jul/2026)

Ideia do André: `f(investimento) = retorno` é a curva de saturação, mas ela **muda a
cada dia**; usar os dias anteriores para saber onde a curva está hoje. Teste
out-of-sample (prever retorno do dia t com dados até t-1) em 14 LANs ≥20 dias.
Script: `scripts/curva_movel_teste.py`.

Quatro modelos de "onde a curva está":

| Modelo | O que assume | MAPE (todos dias) | MAPE (saltos ↑) | Viés em saltos ↑ |
|---|---|---|---|---|
| persist | retorno = eficiência recente × invest (reta, sem curva) | 39% | 27% | **+16%** |
| curva_own | curva de potência na própria história (fixa) | 38% | 28% | +8% |
| **curva_nivel** | **formato fixo + nível recalibrado p/ dias recentes (a ideia)** | 37% | **23%** | +9% |
| curva_movel | refit do formato nos últimos 10 dias | 37% | 25% | +2% |

## Conclusão: a formulação está certa, com 2 qualificações

1. **Para prever o retorno de amanhã, nenhum modelo passa de ~37% de erro** — a curva
   ganha pouco no dia-a-dia porque na maioria dos dias o investimento quase não muda e o
   ruído de demanda/leilão/maturação domina. Piso irredutível (Lewis & Rao).
2. **Para a DECISÃO de escalar, a curva importa — e é aqui que a ideia se prova.** Nos
   saltos pra cima, a persistência ingênua **superestima o retorno em +16%** (não desconta
   a saturação → mandaria escalar demais). A curva com nível recalibrado corta o erro de
   27%→23% e o viés pela metade. **É exatamente o mecanismo de stop-loss / anti-overspend.**
3. **O formato NÃO precisa de refit diário**: curva_nivel (formato fixo + nível móvel) ≈
   curva_movel (refit). Confirma a decomposição tratável **`retorno_t = β_t · f(investimento)`**:
   formato `f` estável, altura `β_t` que se move e é lida dos dias recentes.

## Modelo recomendado (fecha o desenho)

```
retorno_t = β_t · f(investimento_t)
  f  = FORMATO da curva (concavidade), estável. Estimar do POOLING dos saltos de budget
       entre campanhas (resposta marginal limpa) — NÃO da trajetória de uma campanha só
       (confundida: spend e demanda sobem juntos ao longo do lançamento).
  β_t = ALTURA de hoje ("onde a curva está"), dos dias recentes (EWMA de retorno/f(spend))
        e/ou do índice de demanda exógena (não-Meta).
```

Ou seja: a intuição do André estava certa — **o formato é estável e só a altura se move,
e os dias recentes localizam a altura**. A correção é de *onde* tirar o formato: dos saltos
(pooling), não da série passiva de uma campanha. Curvas servem pra corrigir o viés de
escalar (direção e ordem de grandeza), não pra prever o retorno exato de amanhã.

## Calibração da concavidade — o modelo β_t·invest^b validado (24/jul/2026)

Testei `retorno_t = β_t · investimento_t^b` (β_t = mediana dos últimos 3 dias) variando o
formato b, medindo o viés de previsão out-of-sample ao escalar/cortar. Script:
`scripts/teste_modelo_beta_f.py`.

| b | MAPE todos | viés escalar ↑ | viés cortar ↓ |
|---|---|---|---|
| 1,00 (reta/persist) | 37% | **+16%** | −20% |
| 0,80 | 37% | +2% | −7% |
| **0,75** | 37% | **−2%** | −5% |
| 0,70 | 36% | −6% | +1% |
| 0,55 | 36% | −14% | +13% |

**Convergência de dois métodos independentes em b ≈ 0,75:**
- A concavidade que **zera o viés de decisão** fica em b ≈ 0,72–0,75.
- A **elasticidade bruta dos saltos** de budget deu b = 0,78 (n=424).
- (O "pooling limpo" com controle de demanda deu b=1,20, mas n=19 — amostra pequena
  demais, estimativa não-credível; descartado.)

**Modelo validado:**
```
retorno_t = β_t · investimento_t^0.75
  β_t = mediana(retorno_s / invest_s^0.75) dos últimos 3 dias  ← "onde a curva está hoje"
  b = 0,75  ← concavidade fixa (do viés + corroborada pela elasticidade dos saltos)
```

**Leitura de negócio:** em ROAS, b=0,75 significa que **dobrar o investimento derruba o
ROAS em ~16%** (2^(0,75−1) = 0,84). A persistência ingênua (b=1) assume ROAS constante ao
escalar → superestima o retorno da escalada em +16% e do corte em −20%. Aplicar a
concavidade 0,75 remove quase todo o viés de escalar e metade do de cortar.

**O que isto fecha:** a formulação do André está validada com número. O formato é estável
(b=0,75, não precisa refit), a altura β_t vem dos dias recentes. A curva **não** melhora a
previsão do retorno de amanhã (MAPE ~37% em qualquer b — piso de ruído), mas **corrige o
viés de decisão** — é exatamente o que serve para escalar/cortar/stop-loss sem exagerar.
Ressalva: b=0,75 é média; varia por campanha/segmento e é aproximado (confundimento
residual). Refinar por segmento quando houver volume de saltos.

## Forecast — dá pra projetar cada campanha? (29/jul/2026)

> **Relatório visual:** [forecast_campanhas.html](forecast_campanhas.html) — β_t, persistência, diário vs acumulado.

Testei se `retorno = β_t·invest^0.75` vira modelo de projeção. Como o investimento futuro
é *decisão* (input), o que precisa ser projetado é **β_t** (a altura da curva =
`ROAS·invest^0.25`, a eficiência limpa do dia). Backtest de horizonte em 13 LANs, spend
futuro conhecido. Script: `scripts/forecast_beta.py`.

**β_t tem pouca estrutura projetável:**
- Autocorrelação de log β_t: lag-1 **+0,33**, lag-3 +0,23, lag-7 **+0,09** (some em ~1 semana).
- **Sem ciclo de vida estável**: o pico de β cai em posição mediana 0,76 da campanha, 54%
  picam no último terço — não é o "sobe-e-desce" limpo de Horsky-Simon. Não há formato fixo
  pra ajustar.

**Forecast DIÁRIO do retorno (MAPE mediano por horizonte):**

| horizonte | random walk | EWMA-5d | ciclo de vida |
|---|---|---|---|
| 1 dia | 37% | 41% | 42% |
| 3 dias | 41% | 43% | 51% |
| 7 dias | 46% | 46% | 66% |

→ Nem no dia seguinte fura o piso de ~37%. Extrapolar tendência/ciclo **piora** (66% em 7d)
— sem formato estável, a extrapolação diverge. **Projetar a trajetória diária não é confiável.**

**Forecast ACUMULADO (soma do retorno do período, dado o plano de budget):**

| horizonte | MAPE acum (RW) | MAPE acum (EWMA-5d) |
|---|---|---|
| 3 dias | 35% | **27%** |
| 7 dias | 34% | **24%** |
| 14 dias | 36% | **24%** |

→ Erros diários se cancelam no total: **~24% de erro, e ESTÁVEL no horizonte** (não piora de
3 pra 14 dias). Viés pequeno (−9% em 7d, subestima levemente — corrigível). EWNA bate random
walk (suaviza).

### Veredito: dois produtos, duas respostas

1. **Projetar o dia-a-dia da campanha: NÃO.** O retorno diário é ~40% imprevisível (demanda,
   leilão, maturação) e β_t não tem estrutura além de ~2 dias de persistência. Extrapolar
   ciclo de vida é ativamente pior.
2. **Projetar o TOTAL do período dado um plano de budget: SIM, ~±24%, estável.** É o número
   de planejamento: "mantendo este budget, a campanha traz ~R$X (±24%) nas próximas 2 semanas".

**Produto de forecast recomendado:**
```
retorno_total(próximos H dias | plano de budget) = Σ_d  β̂ · budget_planejado_d^0.75
  β̂ = EWMA de β dos dias recentes (meia-vida ~5d)
  banda de ±24% (não é previsão pontual)
```
É o simulador estendido no tempo: entra um plano de budget (D+1..D+14), sai o retorno total
projetado com banda, e dá pra comparar cenários de budget. Casa com o stop-loss (juntos
respondem "continuo rodando e quanto traz"). Não promete o retorno de um dia específico.
