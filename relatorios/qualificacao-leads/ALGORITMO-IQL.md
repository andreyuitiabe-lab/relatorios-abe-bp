# IQL — Índice de Qualidade de Lead (proposta de algoritmo)

**Data:** jul/2026
**Status:** proposta — aguardando validação com time de mídia
**Objetivo:** dar ao marketing uma métrica de direção além do CPL durante a fase de captação, alinhada a expandir a base **e** mirar retorno financeiro de longo prazo.

---

## 1. O problema que o algoritmo resolve

- CPL não prediz qualidade: DOM teve CPL 2,6× maior que VDS, mas CAC 6,4× maior. Otimizar CPL leva a desperdício.
- A janela de conversão de Não Membros é ~421 dias — CAC/receita chegam tarde demais para decidir criativo durante o aquecimento.
- Precisamos de um sinal **disponível no dia do cadastro** que preveja valor futuro.

## 2. Arquitetura em duas camadas

### Camada 1 — Score por lead (probabilidade calibrada de conversão)

Modelo: **Regressão Logística calibrada, sem class_weight** (decisão da revisão adversarial jul/2026 — mesmo AUC que boosting, score interpretável como probabilidade real; `balanced` infla o score 30×).

Features no momento do cadastro, em 3 blocos:

| Bloco | Features | Lift validado |
|---|---|---|
| **Status** | Membro Ativo / Vitalício / Ex-Membro / Não Membro | 5–11× Membro vs NM |
| **Região via DDD** (candidato v0.2) | grupo de UF extraído do telefone | Validado jul/2026: cobertura 86% dos NM, IV 0,032–0,043 (fraco). MT/PR/SC/ES 1,2–1,34× vs Nordeste/AM 0,71–0,95×; "sem DDD válido" 0,78×. Substituto parcial do proxy de renda. Ressalvas: portabilidade, confundimento com targeting regional. Query: `iql_v0/sql/04_exploracao_ddd.sql` |
| **Histórico de cadastro** | nº do cadastro (1º vs recorrente), **recência do cadastro anterior** | Validado jul/2026 (cohort 2025, NM): recadastro ≤30d converte 4,75% vs 3,93% do 1º cadastro (lift 1,21×, z≈7,7); recadastro 181–365d cai para 3,26% (0,83×); 5+ cadastros 3,31% (0,84×). Sinal modesto mas 100% de cobertura (não depende de pesquisa). ⚠️ Conflita com achado EVG de reativação >1 ano (+50%) — definições diferentes; peso final sai da recalibração WOE, não de ajuste manual. ⚠️ Conversão por cadastro dilui mecanicamente para multi-cadastrantes (compra atribuída a 1 dos N cadastros) — estimar pesos só dentro de NM. Query: `queries/07_recencia_frequencia_cadastro.sql` |
| **Pesquisa** (NM principalmente) | ~~renda~~ (pergunta removida jul/2026), relação com BP, tempo que conhece BP, fonte de confiança, streaming, respondeu (sim/não) | responder +50%; "nunca ouvi falar" 0,24% vs 1%; streaming como proxy parcial de poder de compra |

⚠️ **Remoção da pergunta de renda (jul/2026)** — ablação no dataset EVG/BP10 (`modelo_evg_bp10/ablacao_renda.py`): para NM (survey-only), AUC cai 0,685→0,665 e o top decil passa a capturar **20,9% das vendas (lift 2,09×) vs 25,5% (2,55×) com renda**. No modelo completo (status+survey) a perda é menor: AUC 0,745→0,734, top decil 35,1%→33,9%. O score continua útil; renda respondida era 38,6% dos NM (34,6% "prefiro não informar") e a faixa R$10k+ era ~4,7% dos respondentes. Substitutos parciais: streaming/qtd_streaming (poder de compra), proxy geo de renda via CEP/IBGE (se CEP for capturado no cadastro). No desenho parametrizável, o atributo `renda_declarada` fica dormente (nível "sem resposta" = 0 pts) — nada quebra; se a pergunta voltar (ou virar faixa menos invasiva), reativa-se o atributo na recalibração.

Benchmark atual (modelo EVG/BP10): AUC 0,746 (status+survey), top decil = 35% das vendas / lift 3,5× (geral); para mídia usar o headline **NM-only: top decil = 26% das vendas / lift 2,6×**.

Output: `p_conv` ∈ [0,1] por lead + classificação em faixas:

| Faixa | Definição | Interpretação |
|---|---|---|
| **A — Qualificado** | Membro/Ex OU NM com `p_conv` ≥ cutoff decil 8 do treino | Vale pagar CPL premium |
| **B — Potencial** | NM decil 5–7 | Neutro — nutrir |
| **C — Frio** | NM decil 1–4 ou "nunca ouvi falar" sem outro sinal positivo | Não pagar por mais desses |

### Camada 2 — Agregação por anúncio/adset (a métrica do dia a dia)

Para o time de mídia, duas métricas derivadas:

1. **IQL** (0–100) = % de leads faixa A no anúncio/adset. Comparável **apenas dentro da mesma campanha**.
2. **CPLq — Custo por Lead Qualificado** = spend ÷ leads faixa A. É "o CPL que importa": mesma mecânica do CPL, mas o denominador só conta quem tem chance real de comprar. (Métrica padrão de mercado: CPQL — cost per qualified lead. Caso WhatConverts: duas campanhas com CPL idêntico de $65 tinham CPQL de $650 vs $118 — 5× de diferença invisível ao CPL.)

Salvaguardas estatísticas (obrigatórias):
- Mínimo **50 leads por criativo** antes de exibir IQL (abaixo disso, variância domina).
- **Shrinkage** (empirical Bayes) do IQL do anúncio em direção à média da campanha, proporcional ao n — evita que anúncio com 60 leads e sorte pareça campeão.
- Decisão pós-campanha por adset: **conversão observada com shrinkage**, não eRPL (refutado — circularidade de ticket).
- Nunca comparar IQL/CPLq entre campanhas diferentes (funil e produto dominam).

## 3. Regras de decisão para o marketing (matriz CPL × IQL)

Dentro da mesma campanha, por anúncio/adset com n ≥ 50:

| | IQL alto | IQL baixo |
|---|---|---|
| **CPL baixo** | 🚀 **Escalar** — melhor custo-benefício (ex: AD35 EVG: 30% qualificados a CPL R$1,47) | ✂️ **Cortar/limitar** — volume barato que não compra (ex: Pack 2 EVG: CPL R$1,84 mas 11% qualificados) |
| **CPL alto** | 🔧 **Otimizar criativo/lance** — audiência certa, entrega cara | ❌ **Matar** |

Meta de expansão de base: acompanhar em paralelo o **volume absoluto de NM faixa A** (não só o %). Uma campanha pode ter IQL alto só recapturando membros — isso não expande a base. O norte é: **maximizar NM-A por real gasto**, mantendo CPLq total sob controle.

## 4. Loop de validação e calibração

1. **Durante a campanha:** IQL/CPLq diários por anúncio → realocação de budget.
2. **Pós-campanha (na mesma idade de cohort):** comparar ranking IQL vs conversão real por adset via análise de decis/gains — o lift deve ser monotônico (decil 1 concentra múltiplos da taxa base). ⚠️ Nunca comparar campanhas em idades diferentes — usar cohort/KM (censura subestima receita em ≥31%).
3. **Backtest out-of-time:** congelar o modelo numa data, escorar leads posteriores e comparar com conversões observadas — não só validação cruzada dentro do mesmo período.
4. **Recalibração:** re-treinar/recalibrar (isotonic/Platt) a cada campanha encerrada ou trimestralmente, e imediatamente após mudança estrutural (nova pesquisa, novo funil, novo produto); monitorar taxa de resposta da pesquisa (se cair ou variar entre campanhas, o eixo declarado deixa de ser comparável) e drift da distribuição de score.
5. **Registrar em `metricas-referencia.md`** o hit-rate do IQL (ranking previsto vs realizado) por campanha.

Benchmark de mercado para produção: AUC ≥ 0,80 (estamos em 0,746 status+survey / 0,756 com tudo — bom para ranking, com espaço para features comportamentais); requisito mínimo para modelo preditivo: ~1.000 leads e ~100 conversões (EVG teve 34k/390 — folga).

### 4b. Aprendizado contínuo — ciclo de vida das perguntas

As perguntas da pesquisa mudam; o algoritmo aprende com elas via um **banco de perguntas** com métrica de qualidade padronizada: **IV (Information Value)**, que pondera exatamente população em cada resposta × separação de conversão. Régua: <0,02 inútil · 0,02–0,1 fraca · 0,1–0,3 média · 0,3–0,5 forte · >0,5 suspeita de vazamento.

Duas leituras complementares por pergunta:
- **IV total** (inclui "sem resposta" como nível) — valor efetivo da pergunta como está exposta hoje;
- **IV entre respondentes** — potencial puro de separação. Cobertura baixa + IV_resp alto = pergunta boa subexposta (aumentar exposição); cobertura alta + IV_resp baixo = aposentar.

**Leaderboard EVG/BP10, NM, jul/2026** (`modelo_evg_bp10/iv_perguntas.py`):

| Pergunta | Cobertura | IV total | IV respondentes | Ação |
|---|---|---|---|---|
| renda (removida) | 38,6% | 0,262 | 0,185 | — |
| relacao_bp | 43,7% | 0,182 | 0,178 | novo carro-chefe |
| streaming | 37,8% | 0,163 | 0,039 | manter, codificar binário: "assina algo pago" 1,52% conv vs "Nenhum" 1,08% (1,4× entre respondentes) — não usar níveis por plataforma (células pequenas) |
| tempo_conhece_bp | 24,1% | 0,075 | **0,266** | **subexposta — aumentar exposição** |
| midia_tradicional | 18,3% | 0,042 | 0,155 | subexposta — observar |
| religiao | 25,4% | 0,040 | 0,015 | fraca |
| qtd_streaming | 24,7% | 0,013 | 0,051 | aposentar (libera slot) |
| fonte_confianca | 24,9% | 0,010 | 0,038 | aposentar (libera slot) |

**Decomposição da renda** (responde à objeção "população de alta renda é pequena"): as faixas R$10k+ (1,8% dos NM) contribuíam só ~20% do IV da pergunta (0,051 de 0,262). O grosso vinha de **R$5–10k** (4,7% pop, lift 2,7×, IV 0,083) + contraste respondeu/não + "Até R$5.000" (lift 1,5). Se a pergunta voltar: **3 faixas bastam** (Até R$5k / R$5k+ / prefiro não informar) — mantém a maior parte do sinal com menos atrito.

**Ciclo de vida** (o mecanismo de aprendizado):
1. **Entrada — modo coleta:** pergunta nova entra no de-para mapeada a um atributo canônico, peso 0. Coleta sem afetar o score.
2. **Avaliação:** quando a cohort matura (≥100 conversões no segmento NM; agrupar níveis com <30 conversões), rodar o relatório IV/WOE.
3. **Decisão:** IV total ≥0,1 → promover (WOE suavizado vira pontos no seed); 0,02–0,1 → observar ou reformular; <0,02 por 2 campanhas → aposentar, liberando slot do formulário para testar pergunta nova.
4. **Recalibração:** WOE→pontos recalculado a cada campanha madura, com pooling entre campanhas (empirical Bayes) para estabilidade; scorecard versionado (git dos seeds).
5. **Monitoramento:** PSI (population stability index) da distribuição de respostas entre campanhas — detecta quando a mesma pergunta muda de comportamento (audiência ou posição no formulário diferente).

Humano só decide promoções/aposentadorias; os pesos em si saem dos dados — é isso que faz o sistema aprender sem retrabalho a cada mudança de pesquisa.

### 4b-2. Auditoria de literatura — cortes de faixa e valoração (jul/2026)

Pesquisa sobre métodos de cutoff (credit scoring, teoria da decisão, value-based bidding) auditou nosso método. Veredito:

**Confirmado como best practice:** ponderar faixas por RPL observado (= value-based bidding do Google/Meta: valor do estágio = taxa de fechamento × ticket); "receita esperada por R$" > CPQL como métrica de steering; higiene de masterscale (monotonia, recalibração por versão, ICs separáveis).

**A corrigir (escopo v0.3):**
1. **Corte por múltiplo da base (2×/1,3×) é arbitrário e usa a estatística errada.** O certo: (a) limiar vem da economia — break-even de Elkan: tratar lead enquanto `custo ≤ p(conv) × margem` (`p* = C_fp/(C_fp+B_tp)`); (b) aplicado à conversão **marginal no corte**, não acumulada (hoje a borda da faixa A tem lift < 2× — o topo subsidia a borda). Redefinir faixas por **EV em R$** (ex.: A: EV ≥ R$4 · B: R$2–4 · C: R$0,80–2 · D: EV < custo variável de tratamento) — significado econômico direto e estável entre versões.
2. **Métrica de mídia deve usar o EV contínuo que o PDO já dá de graça:** `Odds(s) = Odds₀·2^((s−s₀)/PDO)` → `EV(s) = p(s)×ticket maturado` → `ROAS_esperado(anúncio) = Σ EV(s_i)/custo`. Sem cliff effect, invariante a redefinição de faixa. Faixas continuam para comunicação/roteamento (padrão bancário de dupla via: contínuo para economia, grades para governança).
3. **Censura:** pesos/EV medidos em cohort madura + fator de maturação (curvas de coortes antigas — análise jul/2026: D+30 antecipa ~52% do D+240); congelar por versão do scorecard.
4. **Sem devolver valor à plataforma (CAPI/OCI), o leilão continua caçando lead barato** — reforça a v2.

Fontes-chave: Thomas/Edelman/Crook *Credit Scoring and Its Applications* (strategy curve, cutoff por odds de break-even); Elkan *Cost-Sensitive Learning* IJCAI 2001; Verbraken/Baesens EMP (EJOR 2014, pacote R `EMP`); Google [Value-based Bidding Best Practices](https://support.google.com/google-ads/answer/14792795); BIS bcbs66 / Tasche (masterscale). Relatório completo na pesquisa de 08/jul (transcript da sessão).

### 4c. Desenho de perguntas — regras da literatura (pesquisa jul/2026)

Três tradições convergem; a mais aplicável é a de **application scorecards de crédito** (problema isomorfo: formulário → WOE/IV → binário).

**Desenho da pergunta e das opções:**
- 4–6 opções de resposta, rótulos verbais completos, exclusivas e exaustivas; uma ideia por pergunta, ≤15 palavras (anti-satisficing — cadastro é ambiente de motivação baixíssima).
- Desenhar faixas para a NOSSA população de leads: nenhuma opção com <5–10% dos leads (bin inutilizável) nem >~50% (não discrimina). Desenhar já pensando nos bins finais do scorecard.
- Ordinal (renda, familiaridade): ordem natural fixa, nunca inverter direção entre versões. Nominal (ocupação, streamings): **randomizar ordem das opções** — viés de primazia contamina o WOE da primeira opção.
- Preferir factual/verificável a hipotético ("quais streamings assina" > "quanto pagaria") — mais estável e menos manipulável.
- Sensível (renda): faixas fechadas + "prefiro não informar" explícito; esperar 15–35% de não-resposta (literatura; batemos 34,6%); "não respondeu" é bin próprio com WOE próprio. Técnica de recuperação: fallback binário "acima/abaixo de R$X?" após recusa (unfolding brackets recupera 50–67% dos missings — Juster & Smith 1997).
- Posição: sensíveis/demográficas no final; **mudar a posição de uma pergunta = criar pergunta nova** (versionar).

**Teste e julgamento:**
- Slot experimental: N−1 perguntas core fixas + 1 candidata servida a fração do tráfego, posição fixa.
- Medir custo (Δ completude do formulário no A/B) × valor (IV com cohort madura). 3–5 perguntas é zona defensável (HubSpot 40k LPs: pico de conversão ~3 campos; mas evidência de marketing é observacional — testar no nosso funil).
- Amostra mínima para julgar: ≥30–50 conversões no menor bin; ordem de 1.500–2.000 casos por classe para scorecard robusto (Lewis/Siddiqi).
- Aprovar: IV ≥ ~0,1 com tendência de WOE coerente com o negócio (quebrar monotonia para ganhar IV = ruído — caso qtd_streaming). **IV > 0,5 = investigar leakage**, não comemorar. IV é univariado — exigir ganho incremental (ΔAUC) se correlacionada com pergunta existente.
- Aposentar: IV < ~0,05 por 2–3 campanhas; não-resposta > ~40%; CSI/PSI > 0,25; ou candidata do slot dominar.

**Fontes:** Siddiqi *Credit Risk Scorecards* (IV thresholds, coarse classing); Anderson *The Credit Scoring Toolkit* (seleção de características, palatability); Tourangeau & Yan 2007 *Psych. Bulletin* (perguntas sensíveis); Krosnick & Presser *Question and Questionnaire Design* (satisficing, nº de categorias, primazia); Dillman *Tailored Design Method* (ordem/posição); HubSpot 40k landing pages + CXL (campos × conversão, contrapontos); progressive profiling (HubSpot/Marketo). URLs no histórico da pesquisa jul/2026.

## 5. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| Goodhart: mídia otimiza para "quem responde pesquisa bem" | Score depende de status+histórico além da pesquisa; auditar mix de resposta por adset; **não divulgar os pesos exatos** para quem opera as campanhas; parear IQL com volume e conversão real downstream |
| Viés de resposta da pesquisa (quem responde já é mais quente) | "Respondeu" é feature explícita; lift de renda é medido *dentro* dos respondentes |
| Amostra pequena por criativo | n mínimo 50 + shrinkage |
| Score vira previsão absoluta de receita | Proibido — só ranking relativo intra-campanha; validação pós-campanha usa conversão observada |
| Cobertura: 87% dos NM sem dim_user | Pesquisa é a única fonte de sinal para NM — manter pesquisa no fluxo de cadastro é pré-requisito do sistema |

## 6. Implementação (fases)

1. **v0 (imediato, sem ML):** IQL rule-based com pontos derivados dos lifts validados — status, reincidência, renda, relação BP, respondeu. Transparente para o marketing entender.
2. **v1:** LogReg calibrada (modelo EVG/BP10 existente) rodando diariamente sobre `dtm_analytics_lead_conversion` → `bp-staging.dbt_abe.tb_lead_quality_scores`; dashboard por campanha/adset/anúncio com CPL, IQL, CPLq e volume NM-A.
3. **v2 — feedback ao Meta via CAPI:** ⚠️ correção (jul/2026): o objetivo "Conversion Leads" da Meta é para leads de **Instant Forms**; nossos leads entram em landing pages próprias. O caminho correto para leads de site: evento server-side **"LeadQualificado"** via CAPI quando o lead escora faixa A (mesmo dia — todas as features existem no cadastro), conversão personalizada no Events Manager, e otimização da campanha apontada para esse evento em vez de "Lead". Requisitos: ✅ verificado jul/2026 — `id_fbclid` já é capturado em `bp-lake.marketing.lead_registration` com **81,9% de cobertura** nos cadastros 2026 (o `fbc` deriva do fbclid; e-mail hash já temos) — a dependência de engenharia está essencialmente resolvida; fase de aprendizado do leilão precisa de ~50 eventos/adset/semana — com faixa A a 10–20% dos leads fecha no nível de campanha, pode apertar em adset pequeno (fallback: otimizar A+B). Validação honesta: A/B de campanhas otimizando "Lead" vs "LeadQualificado", comparando CPLq — o ~19% de melhora reportado pela Meta é número promocional, não nosso. Caminho intermediário sem CAPI: custom audience/lookalike semeado só com leads faixa A (mecânica que o time já usa, muda só a lista de entrada).
   - **Não enviar valor previsto (eRPL/EVpL) como `value` nesta fase** — a revisão adversarial já refutou eRPL por adset (circularidade); enviar estágio real de funil é mais robusto contra Goodhart no leilão. Value-based optimization fica para uma v3, apenas com valor calibrado em R$ e re-auditado contra receita real.
   - Filtro grosso imediato sem modelo: **Meta Value Rules** permite ajustar valor por segmento (idade, região, device) de −90% a +1.000% — pode codificar já o que sabemos (ex: penalizar segmentos com histórico de faixa C).

## 7. Referências externas

- **CPQL como métrica de steering:** WhatConverts — [How to calculate CPQL](https://www.whatconverts.com/blog/how-to-calculate-cost-per-qualified-lead-why-cpl-isnt-enough/) (caso $650 vs $118 com CPL igual); AxZ Lead — [CPL vs CPQL 2025](https://axzlead.com/blog/cpl-vs-cpql-2025-guide)
- **Fit × engajamento (explícito + implícito):** framework SiriusDecisions/Marketo — [Matrix scoring](https://nation.marketo.com/t5/champion-program-blogs/how-to-create-a-matrix-scoring-model-in-marketo-engage/ba-p/331263). Nossas 3 camadas mapeiam: pesquisa = eixo explícito (fit); status + histórico de cadastro = eixo implícito.
- **Validação de score preditivo:** Reform — [Predictive scoring validation](https://www.reform.app/blog/predictive-scoring-validation-best-practices) (splits temporais, AUC ≥0,80, retraining trimestral, mínimos de 1.000 leads/100 conversões)
- **Shrinkage para amostras pequenas:** MetricGate — [Empirical Bayes shrinkage](https://metricgate.com/docs/empirical-bayes-shrinkage/)
- **Meta Conversion Leads / CAPI:** [Meta for Developers](https://developers.facebook.com/documentation/ads-commerce/conversions-api/conversion-leads-integration); LeadsBridge — [requisitos operacionais](https://leadsbridge.com/blog/conversion-leads-optimization-facebook/); Birch — [Value Rules](https://bir.ch/blog/meta-value-rules)
- **pLTV bidding (assinatura):** AdZeta — [pLTV no Meta 2026](https://www.adzeta.io/blog/pltv-bidding-meta-ads-what-actually-works-2026); Admiral Media — [Predictive LTV bidding](https://admiral.media/predictive-ltv-bidding/) (lifts de ROAS 20–40% reportados; referência para a v3)
- **Google Ads (se voltar a ser canal):** [Enhanced conversions for leads](https://support.google.com/google-ads/answer/15713840) — ⚠️ a partir de jun/2026 uploads offline migram para a Data Manager API
- **Goodhart:** KPI Tree — [Goodhart's Law em métricas de marketing](https://kpitree.co/guides/frameworks/goodharts-law)

---

## Queries / artefatos relacionados

- Modelo e benchmarks: `modelo_evg_bp10/` (benchmark.csv, lift_table.csv, tarefa_c.py)
- Base de scoring: `bp-staging.dbt_abe.tb_leads_qualification_base` / `_enriched`
- Pesquisa normalizada: extração in-funnel em `evg-bp10-pesquisa/refresh.py`
