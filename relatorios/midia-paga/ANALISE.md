# Curva de Resposta ao Investimento — Meta Ads

**Status:** em andamento (não concluído nessa sessão)
**Início:** maio/2026
**Última atualização:** jun/2026

## Pergunta original

Encontrar o ponto ótimo de investimento em Meta Ads: onde a próxima venda incremental
começa a não valer a pena. Meta operacional: apoiar decisão dos gestores de tráfego
sobre **quanto gastar por dia**, **quando escalar** e **quando cortar**, antes de ter
resultado ruim ou deixar dinheiro na mesa.

## Evolução da abordagem

A investigação passou por várias reformulações. Documentar aqui evita repetir caminhos
que não funcionaram.

### 1. Curva de resposta agregada do portfólio
Primeiro modelo: `vendas = f(spend)` no portfólio total. Testado com:
- Lei de potência (`sales = a·spend^b`)
- Logística (`V·(1−e^(−k·spend))`)
- Polinomial grau 2 e 3

**Vencedora inicial:** polinomial grau 3 (R² 0.81 no histórico completo,
identifica joelho da curva em ~R$173k/dia).

**Adstock:** aplicado antes do ajuste, α=0.50, l_max=14d (alinhado com
`mmm_project/src/modeling/transforms.py`).

**Relatórios:** [relatorio_curva_polinomial.html](relatorio_curva_polinomial.html),
[faixa_orcamento.html](faixa_orcamento.html), [rolling_efficiency.html](rolling_efficiency.html).

### 2. Detector de tendência (semáforo 🟢🟡🔴)
Baseado em projeção de ROAS + nível + slope. Captura 97% dos dias ruins (ROAS<1)
como 🟡+🔴, com só 4% falso positivo em 🟢.

**Relatório:** [detector_tendencia.html](detector_tendencia.html).

### 3. Budget Advisor
Combinou curva polinomial (faixa piso-teto) com detector de tendência (posicionamento
na faixa). Adiciona cap de extrapolação de 1.2× o gasto máximo observado.

**Relatório:** [budget_advisor.html](budget_advisor.html).

### 4. Análise por campanha individual
Percebido que o portfólio agregado mistura curvas heterogêneas. Ajuste individual
por campanha (lei de potência / logística / polinomial conforme nº de pontos).

**Relatórios:** [analise_campanhas.html](analise_campanhas.html),
[curva_acumulada_campanhas.html](curva_acumulada_campanhas.html).

### 5. Reformulação: rastrear G* no tempo
Definido G* = gasto onde CPA marginal = R$180 (CPA-alvo fixo). A série temporal de
G* mostra evolução da eficiência marginal.

**Aderência CPA pred × real (rolling 60d, CPA target R$200):** 0.42.
**Cobertura dias ruins:** 64%.

### 6. Testes com sinais antecedentes do funil
**Hipótese:** hook rate e CTR predizem CPA futuro (1-14 dias).
**Resultado:** correlações fracas ou invertidas.
- Hook rate lag 7d: +0.28 (invertido: hook alto → CPA alto depois, provável escalada)
- CTR lag 0-1: −0.30 (contemporâneo, não preditivo)
- ΔCTR contemporâneo: −0.45 (forte mas não preditivo)
- CVR: nenhum sinal antecipa (correlações <0.15)

**Conclusão:** essas métricas servem para **diagnóstico em tempo real**, não para
antecipar CPA futuro. Descartada como preditor.

### 7. Análise de dia da semana
Testado se DOW prediz eficiência. Padrão emerge quando cruzado com nível de gasto:
- Domingo em gasto médio (R$30-117k): índice de eficiência 79-88 (bom)
- Sábado em gasto baixo: índice 129 (ruim)
- Segunda em gasto alto: índice 86 (surpreendentemente bom)
- Meio de semana (Qua/Qui) em gasto alto: caro

**Sinal detectado:** ΔCTR cai −5.6% em 78% dos sábados (sazonalidade real).

### 8. Segmentação por tipo (LAN vs PPT) e objetivo (VENDA vs LEAD)
**Achado principal:** LAN e PPT são estatisticamente diferentes.
- **PPT** (perpétuas): R$6.5M gastos, ROAS 1.33, CPA R$165. Ticket implícito ~R$219.
- **LAN** (lançamentos): R$7.8M gastos, ROAS 1.68, CPA R$187. Ticket implícito ~R$308.
LAN vende produtos mais caros. Mesma curva não serve pra ambos.

**LEAD**: ROAS 0.36 (nunca vai ser bom no direto — leads convertem depois via
comercial/WhatsApp). KPI certo é CPL, não ROAS direto. Análise separada.

**Por produto** (siglas de posição 2 no nome): 18 lançamentos com ≥30 pontos permitem
curva polinomial confiável. Concentram 98% do gasto de VENDA.

### 9. Backtest de 3 abordagens para LAN
Simulado em 17 LAN completas do histórico. Cada dia D, sinal com dados ATÉ D-1,
comparado com ROAS real dos próximos 3 dias.

| Abordagem | "aumentar" ROAS | "manter" ROAS | "reduzir" ROAS | Veredito |
|---|---|---|---|---|
| **A** (polinomial G*) | 1.31 | 0.97 | 1.23 | ❌ ordem confusa |
| **B** (slope CPA marg 5d) | 1.13 | 1.28 | 1.16 | ❌ ordem trocada |
| **C** (CPA 3d vs baseline) | **1.45** | 1.15 | **0.75** | ✅ discrimina bem |

**Conclusão validada:** para LAN, usar **Abordagem C** (CPA recente vs acumulado da
própria campanha). Não requer ajuste de curva — evita confundir trajetória temporal
com resposta a gasto.

**Fórmula:**
```
ratio = CPA_últimos_3d / CPA_acumulado_da_campanha
ratio > 1.30 → reduzir
ratio < 0.85 → aumentar
caso contrário → manter
```

## Achados principais

### Sinal robusto por tipo de campanha

**PPT (perpétuas):** curva polinomial com adstock funciona. G* estável ao longo do
tempo. Campanhas com claro espaço para escalar (jun/2026):
- `[PPT] [FNC] [VENDA] [ADVANTAGE] Brasil` — gasto R$13k/dia, G* R$33k, R²=0.85
- `[PPT] [10R] [VENDA] [ADVANTAGE] Novos ads março` — R$6k/dia, G* R$28k
- `[PPT] [EXM] [VENDA] [ADVANTAGE] Recuperação` — R$2k/dia, G* R$10k, ROAS 1.62

**LAN (lançamentos):** curva ingênua falha (aprende trajetória, não saturação).
Abordagem C (ratio CPA recente/baseline) discrimina bem. Aplicar apenas para
campanhas com ≥5 dias de histórico.

### Dinâmica do fim de semana ruim (9-10/mai)
- CTR caiu de 2.5% (sex) para 2.0% (sáb-dom) — audiência atingida piorou
- Ticket médio caiu de R$250 para ~R$190 (produto mais barato vendendo)
- ROAS foi 0.92 (prejuízo direto). Perda: R$29k.

**Nenhum sinal antecedente** dos modelos testados capturou isso. Escalada +90% de
gasto entre 8 e 9/mai, com CTR já em queda. O sistema atual só detectaria depois.

### Escalada bem-sucedida (21-27/mai)
- ROAS inicial em 3.48 (21/mai, R$63k/dia)
- Gasto escalou até R$254k/dia em 27/mai, ROAS 2.22
- Sistema classificaria como "acima do limite" durante a escalada, mas ROAS aguentou
- Confirma: LAN em ramp-up é regime distinto — curva histórica não vale como referência

### Sazonalidade DOW × nível de gasto
Existe padrão robusto (índice de eficiência controlado por gasto):
- Domingo em spend médio+ é o mais eficiente (índice 79-88)
- Sábado em spend baixo é o pior (índice 129)
- Quarta/quinta em spend alto são caros

### Distribuição do mix
% LAN no mix semanal variou de 1% (19/jan) a 93% (25/mai). Comparar CPA agregado
entre semanas com mix diferente **compara coisas diferentes**. Sempre controlar por
mix.

## Pendências / próximos passos

### Prioritário

1. **Consolidar em uma única ferramenta operacional** (dashboard unificado)
   - Split por PPT (polinomial + G*) e LAN (ratio C)
   - Filtro só campanhas ativas (últimos 7 dias)
   - Recomendação diária: aumentar/manter/reduzir por campanha + total

2. **Ad Set granularidade** — não implementado ainda. Query pronta em
   `queries/adset_daily.sql`. Falta rodar análise: quantos pontos por ad set?
   Vale ajustar curva ou usar só como referência?

3. **Análise LEAD separada** — KPI é CPL, não ROAS. Modelo completamente diferente.

### Médio prazo

4. **Modelo bayesiano por campanha** (inspirado em Springer 2024)
   - Prior de V, k vindo do MMM da casa (`mmm_project`)
   - Posterior por campanha com intervalos de credibilidade
   - Ancora campanhas com poucos pontos com prior informativo
   - Prompt de novo chat preparado (ver seção "Continuação" abaixo)

5. **Thompson sampling para alocação entre campanhas**
   - Multi-armed bandit adaptado do paper
   - Alocação sob incerteza sem depender de preditor forte

### Longo prazo

6. **Migração para Meridian** (em andamento no projeto MMM)
   - Estrutura mais completa que suporta o problema
   - Aguarda produção

## Queries e scripts

### Queries SQL (em [`queries/`](queries/))
- `daily_spend_venda.sql` — portfólio diário VENDA
- `scatter_campaign_daily.sql` — campanha × dia
- `daily_funnel_metrics.sql` — funil (impressões, cliques, views) diário
- `all_camps.sql` — todas as campanhas (VENDA + LEAD + etc.)
- `adset_daily.sql` — ad set × dia (não usado ainda)

### Scripts Python (em [`scripts/`](scripts/))
- `curve_fits.py` — biblioteca de ajuste (power, logistic, polinomial, adstock)
- `analyze_active_campaigns.py` — status atual das campanhas ativas
- `lan_backtest.py` — validação das 3 abordagens para LAN
- `funnel_correlation.py` — correlações hook/CTR/CVR × CPA
- `refresh_data.sh` — atualiza todos os CSVs de `/dados/midia_paga/`

### Como reproduzir
```bash
# Atualizar dados do BigQuery
bash scripts/refresh_data.sh

# Rodar análises
python scripts/analyze_active_campaigns.py
python scripts/lan_backtest.py
python scripts/funnel_correlation.py
```

## Relatórios HTML

| Arquivo | O que mostra |
|---|---|
| [relatorio_ponto_otimo_investimento.html](relatorio_ponto_otimo_investimento.html) | Primeira análise — ponto ótimo, curva agregada |
| [scatter_response_curve.html](scatter_response_curve.html) | 4 níveis + lei de potência, slider CPA-alvo |
| [relatorio_curva_polinomial.html](relatorio_curva_polinomial.html) | Comparação polinomial 1/2/3 vs logística |
| [faixa_orcamento.html](faixa_orcamento.html) | Teto adaptativo (ticket médio 7d) |
| [rolling_efficiency.html](rolling_efficiency.html) | ROAS marginal rolling 14d/28d |
| [detector_tendencia.html](detector_tendencia.html) | Semáforo 🟢🟡🔴 (baseado em ROAS projetado) |
| [budget_advisor.html](budget_advisor.html) | Recomendação diária (portfólio) |
| [analise_campanhas.html](analise_campanhas.html) | Curva por campanha individual |
| [curva_acumulada_campanhas.html](curva_acumulada_campanhas.html) | Curva acumulada + CPA marginal por período |

Portal: https://andreyuitiabe-lab.github.io/relatorios-abe-bp/relatorios/midia-paga/

## Limitações honestas

Documento as ressalvas que apareceram consistentemente:

1. **Curvas são descritivas, não causais.** Gasto foi escolhido baseado em expectativa
   (endogeneidade). Não temos experimentos randomizados. Recomendações são referência,
   não regra automática.

2. **Aderência preditiva é moderada.** Correlação CPA modelo × real ~0.42 em janelas
   rolantes. Erro relativo médio 25%. Boa pra sinalizar regime, ruim pra prever amanhã.

3. **Sinais antecedentes do funil são fracos.** Hook rate e CTR não preveem CPA
   futuro (correlações <0.30, e algumas invertidas). Servem só para diagnóstico
   contemporâneo.

4. **Falta calendário de eventos.** Lançamentos, mudanças de criativo, mudanças de
   oferta são exógenos e não estão no modelo. Isso limita previsão.

5. **Extrapolação além do observado é insegura.** G* que caem fora de 1.2× do gasto
   máximo já testado são marcados como extrapolação.

## Continuação em nova sessão

Um prompt pronto para próxima conversa está preparado. Contém:
- Persona (analista sênior, engenheiro de dados antes de modelador)
- Contexto completo do problema
- Decisões já tomadas (não revisitar)
- O que não funcionou (não repetir)
- Objetivo específico (modelo bayesiano com prior do MMM)
- Caminhos dos arquivos

Ver seção "Prompt de continuação" no final da conversa origem, ou colar novo prompt
com contexto atualizado incluindo:
- Backtest LAN validou Abordagem C
- Sinais funil descartados (correlação fraca)
- Segmentação LAN vs PPT vs LEAD é o eixo certo
- Aguarda decisão sobre camada bayesiana + Thompson sampling
