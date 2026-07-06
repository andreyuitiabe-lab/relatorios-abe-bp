# Proposta — Curva de saturação e budget diário por campanha

**Data:** 2026-07-06
**Status:** proposta para aprovação (sessão sem execução)
**Insumos:** `ANALISE.md` (9 iterações), scripts em `scripts/`, pipeline de bidding em `mmm_project/src/bidding/` (Etapas 1–4b), pesquisa externa (referências na seção 2)

---

## 0. O achado que muda o enquadramento

Antes da crítica técnica, um fato organizacional: **existem dois esforços paralelos atacando o mesmo problema**, e o `ANALISE.md` desta pasta não referencia o outro.

| | `midia-paga/` (esta pasta) | `mmm_project/src/bidding/` (Etapas 1–4b) |
|---|---|---|
| Curvas | logística/potência/poly3, escolha por nº de pontos | Hill + exponencial, escolha por R², mCAC analítico |
| Adstock | α=0.50, l_max=**14d** | α=0.50, l_max=**8d** |
| Confundimento de demanda | **não tratado** | tratado (`06_demand_index.py`, vendas deflacionadas por demanda não-Meta) |
| Fadiga de criativo | não tratada | downweighting logístico por anúncio |
| Otimizador | G* por campanha, sem restrição de passo | ceiling-optimal + water-filling + step-limit ±20%/dia |
| Validação | backtest 17 LAN (Abordagens A/B/C) | evento 09–10/mai (corte recomendado R$33k vs R$31–73k medido independentemente) |
| Regime LAN | **tratado** (Abordagem C validada) | não tratado (Hill sobre a vida inteira da campanha) |

O pipeline de bidding já resolve o que as iterações 1–5 desta pasta tentaram — com desconfundimento e validação por evento que esta pasta não tem. E esta pasta tem a única coisa que falta lá: o tratamento de regime para LAN (Abordagem C). **A proposta é unificar, não criar uma terceira via.**

---

## 1. Análise crítica do que fizemos

### Onde acertamos

1. **Segmentação LAN / PPT / LEAD como eixo primário.** Estatisticamente diferentes (ROAS 1.68 vs 1.33, tickets R$308 vs R$219), e LEAD com KPI errado se medido em ROAS direto. Nenhuma referência externa contradiz isso; a literatura de bandits não-estacionários confirma que lançamento de 3–6 semanas é um regime que exige tratamento próprio.

2. **Backtest honesto com dados até D-1 e descarte do que não funcionou.** Testar sinais antecedentes de funil e descartá-los (correlações <0.30, algumas invertidas) foi o procedimento correto. O mesmo vale pro detector de tendência: mantido só como diagnóstico.

3. **Abordagem C venceu por ser a única que não confunde trajetória com resposta.** A regra `CPA_3d / CPA_acumulado` é, sem saber, um proto-CUSUM (detector sequencial de mudança) — exatamente a classe de método que a literatura recomenda quando não há preditor forte. A ordem do backtest (aumentar 1.45 > manter 1.15 > reduzir 0.75) é discriminação real.

4. **Seção "Limitações honestas" no ANALISE.md.** Endogeneidade, aderência 0.42, extrapolação — tudo declarado. Raro e valioso.

### Onde erramos / premissas que não se sustentam

**a) A premissa central não se sustenta: não existe uma curva estável `vendas = f(spend)` recuperável da série temporal passiva de uma campanha.** Dois mecanismos, ambos agora documentados:

- **Confundimento de demanda** (provado no `mmm_project`): dias de alto gasto são dias de alta demanda. A curva observacional *desloca para cima* em vez de a campanha *andar ao longo* dela. Quando as vendas foram deflacionadas pelo índice de demanda não-Meta, a curva do portfólio **dobrou** (CAC por faixa: de plano ~190 para 63→180; mCAC no topo foi a R$735) e as campanhas "reduzir" saltaram de 67 para 122. **Todo G* calculado nesta pasta está sobre curvas confundidas e superestima o espaço para escalar.** As campanhas listadas como "com espaço" (FNC G* R$33k, 10R G* R$28k, EXM G* R$10k) precisam ser re-verificadas sob desconfundimento antes de qualquer recomendação.
- **Divergent delivery** (Meta, arXiv 2508.21251): mudar budget muda a composição da audiência que o Advantage+ entrega. A "curva" da campanha se move quando você mexe no budget. Isso explica *mecanicamente* a aderência 0.42 — não era questão de achar uma forma funcional melhor. As 5 formas × 5 janelas testadas eram variações sobre uma premissa quebrada.

**b) Polinomial grau 3 como modelo de decisão foi um erro já demonstrado.** O `mmm_project` avaliou e rejeitou a poly3: R² in-sample maior (premia flexibilidade), mas **43% das campanhas têm derivada não-monotônica** — o mCAC vira negativo/inválido — e sem assíntota a extrapolação é insegura. A Abordagem A do nosso próprio backtest (poly + G*) falhou exatamente assim ("ordem confusa"). R² não é critério para modelo de *decisão*; monotonicidade da derivada e comportamento em extrapolação são.

**c) O CPA recente não é corrigido por maturação de conversões.** Conversões chegam com atraso (o adstock l_max=8–14d que nós mesmos usamos implica isso). O `CPA_3d` é viesado **para cima** nos dias mais recentes — pior justo após uma escalada, quando as conversões do gasto novo ainda não maturaram. A Abordagem C pode disparar "reduzir" falso nesse cenário. A literatura de delayed feedback (Chapelle; Vernade 2017) dá a correção padrão: inflar conversões recentes pelo fator de maturação estimado.

**d) Inconsistência de parâmetros entre projetos.** Adstock l_max=14d aqui vs 8d no bidding pipeline, ambos ditos "alinhados com o MMM da casa". Um dos dois está errado, ou o alinhamento é nominal.

**e) O fracasso em prever 09–10/mai não era falta de sinal — era falta do controle certo.** "Nenhum sinal antecedente capturou" o fim de semana ruim. Mas o `demand_index` do dia foi 0,72: a demanda não-Meta estava fraca *enquanto o gasto escalava +90%*. Com o teto modulado por demanda (0,72×180 = R$129), o recomendador do bidding pipeline, em backtest as-of 08/mai, apontou REDUZIR nas mesmas campanhas que causaram o overspend. O sinal existia — em outra variável.

**Veredito: não descartar tudo.** Descartar as curvas descritivas desta pasta como motor de decisão (iterações 1–5). Manter: segmentação, Abordagem C, achados de DOW × gasto, e o backtest harness. Adotar o bidding pipeline como backbone.

---

## 2. Referências externas

Filtradas para o que resolve algo específico do nosso problema. Duas pesquisas independentes (curvas/MMM e alocação/bandits); links verificados.

### Sobre a curva e sua identificação

| Referência | O que resolve aqui |
|---|---|
| **Jin et al. 2017 — Bayesian Methods for MMM with Carryover and Shape Effects** (Google Research) | O paper canônico de Hill+adstock estimados juntos. Achado diretamente aplicável: com pouca amostra, o posterior é dominado pelo prior → usar priors informativos de modelos relacionados. Justifica ancorar campanhas novas com prior da conta/MMM em vez de ajustar cada curva isolada. |
| **Sun, Wang, Jin et al. — Geo-level Bayesian Hierarchical MMM** (Google) | Hierarquia estreita intervalos de credibilidade. Análogo direto: hierarquia campanha→conta resolve nossa cobertura de 31% (campanhas com poucos pontos herdam forma da conta). |
| **Nuara et al. — Online Joint Bid/Daily Budget Optimization** ([arXiv:2003.01452](https://arxiv.org/pdf/2003.01452)) | **A referência mais próxima do nosso problema exato.** Curva spend→conversões por campanha via Gaussian Process, decisão diária como semi-bandit combinatório, e — crucial — a *exploração deliberada de budget é a fonte de identificação*: o sistema varia budget de propósito pra aprender a curva. Rodou em produção >1 ano. Resolve a endogeneidade que nenhuma forma funcional resolve. |
| **Characterizing and Minimizing Divergent Delivery in Meta Advertising** ([arXiv:2508.21251](https://arxiv.org/pdf/2508.21251)) | Explica mecanicamente por que a curva de uma campanha Advantage+ não é estável: mudar budget muda a audiência entregue. Fundamenta o abandono da premissa de curva fixa por campanha. |
| **PyMC-Marketing — BudgetOptimizer** ([docs](https://www.pymc-marketing.io/en/latest/notebooks/mmm/mmm_budget_allocation_example.html)) | Ferramenta prática: saturações intercambiáveis, otimizador com restrições de desigualdade (dá pra codificar "mCAC ≤ 180" como restrição), incerteza posterior propagada até a alocação. Base natural da camada bayesiana, e já usamos PyMC na casa. |
| **Gufeng Zhou (autor do Robyn) — convergência do marginal ROAS** ([Medium](https://medium.com/@gufengzhou/the-convergence-of-marginal-roas-in-the-budget-allocation-in-robyn-5d407aebf021)) | Formaliza o critério que já usamos por instinto: no ótimo, o mROAS equaliza entre campanhas; o teto R$180 é a condição de parada. É a mesma lógica do water-filling já implementado no `optimize.py`. Confirma o desenho, não o muda. |
| **Cost caps no Meta** (prática de mercado, ex.: [Triple Whale](https://www.triplewhale.com/blog/cost-caps-facebook)) | Alternativa operacional: informar o teto ao leilão via cost cap em vez de só cortar budget — a Meta deixa de gastar quando não consegue entregar abaixo do alvo. Limite: mira CPA *médio*, não marginal, e restringe entrega. Vale teste controlado, não substitui o sistema. |

### Sobre a decisão diária sob incerteza

| Referência | O que resolve aqui |
|---|---|
| **Gigli & Stella 2024 — Multi-armed bandits for performance marketing** (Springer — provavelmente "o paper Springer 2024" do ANALISE.md; [link](https://link.springer.com/article/10.1007/s41060-023-00493-7)) | Bandit paramétrico (impõe curva de saturação como estrutura) + bootstrapped Thompson sampling, desenhado pra poucas conversões diárias e mercado que muda rápido — o regime LAN. Mostra que estrutura paramétrica compensa escassez de dado. |
| **Discounted Thompson Sampling** ([arXiv:2305.10718](https://arxiv.org/abs/2305.10718)) | TS com fator de desconto pra ambientes não-estacionários. Half-life de ~5–7 dias é a formalização exata do instinto da Abordagem C ("confiar mais no CPA_3d que no acumulado"), mas com incerteza quantificada. Candidato pra Etapa 5 do bidding pipeline ("update Bayesiano/bandit online", já pendente lá). |
| **Vernade et al. 2017 — Bandits com delayed conversions** ([arXiv:1706.09186](https://arxiv.org/abs/1706.09186)) + modelo de delay de Chapelle | A correção de maturação do CPA_3d: estimar a distribuição do delay de conversão e inflar conversões recentes antes de alimentar a regra. Corrige o viés estrutural da Abordagem C (item 1c). |
| **Adams & MacKay — Bayesian Online Changepoint Detection** (+ aplicação a fadiga de ads, [arXiv:2509.09758](https://arxiv.org/abs/2509.09758)) | Se quisermos formalizar a Abordagem C: BOCPD dá probabilidade de "a curva mudou" com poucos pontos e controle explícito de falso alarme. Upgrade opcional, não necessário na v1. |
| **Meta — learning phase / significant edits** ([Help Center](https://www.facebook.com/business/help/112167992830700)) + consenso practitioner | Mudanças de budget ≤20%/dia não resetam o learning; acima de ~30% sim; avaliar efeito só com ≥48h (pacing interno da plataforma leva 1–2 dias pra convergir). Valida o step-limit ±20% já implementado e adiciona a regra de lag de avaliação que **não** temos. |
| **Budget pacing** ([arXiv:2503.06942](https://arxiv.org/abs/2503.06942)) | Por que a resposta a budget não é instantânea: a plataforma redistribui gasto intradiário via throttling/PID. Consequência prática: nunca julgar uma mudança de budget com <48h de dado. |

**Síntese das duas pesquisas:** a literatura converge para o desenho que já emergiu por tentativa e erro — (a) Hill hierárquico com priors + desconfundimento, não curva livre por campanha; (b) regra simples de razão recente/baseline como detector de regime; (c) passos limitados a ±20%/dia com avaliação em ≥48h; (d) **variação deliberada de budget como fonte de identificação** — a peça que nenhum dos dois projetos tem; (e) geo-lift ocasional pra calibrar nível (já existe no projeto).

---

## 3. Proposta de modelagem

### Arquitetura em três camadas

**Camada 1 — Estado: onde cada campanha está na curva (motor: bidding pipeline, melhorado).**

Adotar o backbone existente: Hill por campanha sobre vendas desconfundidas (`eff_sales_adj`), mCAC analítico, teto R$180 modulado pelo `demand_index` do dia. Duas melhorias:

1. **Hierarquia bayesiana campanha→conta** (PyMC-Marketing, priors de forma vindos do MMM da casa e do pool de campanhas do mesmo tipo/produto). Campanha com 8 pontos herda a forma da conta e só desloca escala; campanha com 60 pontos deixa o dado falar. Resolve a cobertura de 31% — o gargalo declarado da validação do evento — e dá intervalo de credibilidade no G\* em vez de ponto.
2. **Split de regime**: PPT e LAN madura (>~10 dias pós-pico de ramp) usam a curva. **LAN em ramp-up não usa curva nenhuma** — usa a Abordagem C, importada desta pasta, com correção de maturação de conversões. É a lição conjunta dos dois backtests: a curva falha em LAN (Abordagem A), a razão funciona (C); e a escalada 21–27/mai mostrou que cortar LAN em ramp por "estar acima da curva histórica" custa caro.

**Camada 2 — Decisão: o que fazer amanhã.**

Regra determinística por campanha, na ordem:

```
1. mCAC_real(gasto_atual) > teto·demand_index  →  REDUZIR (nunca aumentar; já implementado)
2. LAN em ramp-up                              →  Abordagem C (ratio com conversões maturadas)
3. Caso contrário                              →  mover em direção ao G* com passo máx ±20%/dia
4. Toda mudança: reavaliar só com ≥48h de dado (pacing)
```

Sem ML na decisão — a decisão é uma política, o modelo só estima o estado. Discounted Thompson sampling fica como evolução opcional (Fase 3), não requisito.

**Camada 3 — Identificação: de onde vem a variação que ensina a curva.**

Este é o único componente genuinamente novo, e ataca a causa raiz da aderência 0.42. Três fontes, em ordem de custo:

1. **Micro-experimentos de budget programados** (Nuara): nas campanhas PPT estáveis, variações deliberadas de ±15–20% por 3–4 dias, agendadas em rodízio. Gera variação de spend *exógena à demanda* — a única forma de estimar a inclinação local da curva sem confundimento, dentro do limite que não reseta o learning. Custo: pequena perda de eficiência nas campanhas em teste, limitada pelo próprio step-limit.
2. **Eventos naturais de budget** como quasi-experimentos (harness do `05_overspend_event.py`, já validado): manter como validação contínua.
3. **GeoLift** (já existe no projeto): calibração de nível 1–2×/ano, não instrumento diário.

### Dados adicionais necessários

- **Delay de conversão**: verificar se o `dtm_analytics_facebook_ads_funnel` restated (vendas atribuídas ao dia do clique mudam retroativamente?) permite estimar a curva de maturação comparando snapshots D+1 vs D+7. Se a tabela é restated, basta guardar snapshots diários por ~3 semanas. Sem isso, a correção de maturação usa aproximação pelo adstock.
- **Calendário de eventos**: `tb_campaign_period` já existe; integrar como flag no fit (dia de abertura de carrinho ≠ dia normal).
- **Nenhum dado novo de plataforma** é necessário pra v1. `frequency/reach` continuam ausentes — limitação conhecida, contornada pela proxy de retenção de vídeo já implementada na Etapa 1.

### Como valida

1. **Teste de aceitação existente**: evento 09–10/mai — recomendação deve cortar na ordem de R$31–73k, apontando as campanhas certas. Já passa com cobertura 31%; a meta é passar com cobertura ≥70%.
2. **Backtest walk-forward** no formato da Abordagem C: pra cada dia D e campanha, sinal com dados até D-1 vs ROAS realizado em D+1..D+3 (respeitando as 48h). Critério: ordem monotônica ROAS(aumentar) > ROAS(manter) > ROAS(reduzir), separação ≥ a do backtest C atual (1.45/1.15/0.75).
3. **Métrica de negócio contínua**: saving simulado por mês (gasto em dias/campanhas com mCAC>teto que o sistema teria cortado), medido pelo harness de eventos.

### Horizonte de previsão realista

Sendo honesto com o que os dados suportam:

- **Direção (aumentar/manter/reduzir) por campanha: 1–3 dias.** É o que os backtests validam.
- **Magnitude: confiável só do lado REDUZIR.** O lado AUMENTAR extrapola a zona eficiente — por isso o passo gradual (limite já reconhecido no `08_recomendar_orcamento.py`).
- **Prever o CPA de amanhã com precisão: não.** Ninguém prevê — a resposta certa é decisão robusta sob incerteza, não previsão pontual. A aderência 0.42 não vai virar 0.9 com modelo melhor; o divergent delivery e a demanda garantem isso.

---

## 4. Plano de implementação em fases

### Fase 0 — Unificação e re-verificação (1–2 dias)

- **Entregável:** um documento canônico único (provavelmente promover `mmm_project/wiki/pages/model-decisions.md`), reconciliação do adstock (14d vs 8d — decidir e alinhar), e **re-verificação das campanhas "com espaço pra escalar" desta pasta sob desconfundimento** (rodar Etapa 3 sobre elas e comparar G*).
- **Critério de sucesso:** lista revisada de campanhas escaláveis; nenhum G* desta pasta citado sem passar pelo desconfundimento; ANALISE.md atualizado apontando pro backbone unificado.
- **Uso pelo gestor:** ainda nenhum — é higiene. Mas evita que ele receba duas recomendações contraditórias dos dois sistemas.

### Fase 1 — Recomendador diário unificado v1 (3–5 dias)

- **Entregável:** `08_recomendar_orcamento.py` estendido com: (i) rota LAN-em-ramp → Abordagem C; (ii) correção de maturação simples nas conversões recentes; (iii) regra das 48h; (iv) saída em dashboard único (padrão `index.html` + `data.json` + `refresh.py` desta pasta) — uma linha por campanha ativa: gasto atual → recomendado → ação → confiança.
- **Critério de sucesso:** (a) reproduz o corte do evento 09–10/mai; (b) no walk-forward, ordem ROAS por bucket monotônica com separação ≥ backtest C; (c) na escalada 21–27/mai, **não** recomenda cortar antes de 27/mai.
- **Uso pelo gestor:** abre o dashboard de manhã, vê 1 linha por campanha com ação e passo em R$. Aplica passos de ±20%, ignora campanhas marcadas "sem recomendação" (wear-in / fora do range).

### Fase 2 — Camada bayesiana hierárquica (5–8 dias)

- **Entregável:** fit hierárquico campanha→conta em PyMC-Marketing, priors do MMM v31, posterior de G* com intervalo de credibilidade por campanha; substitui o fit isolado da Etapa 3.
- **Critério de sucesso:** cobertura de gasto [VENDA] com recomendação válida ≥70% (hoje 31%); evento 09–10/mai continua passando; intervalo de credibilidade do G* calibrado (cobertura empírica ~80% em walk-forward).
- **Uso pelo gestor:** recomendações passam a existir também pra campanhas novas/pequenas, com selo de incerteza ("G* R$28k ± R$9k") — ele sabe quando a recomendação é firme e quando é palpite ancorado.

### Fase 3 — Identificação ativa (contínua; setup 2–3 dias)

- **Entregável:** rodízio de micro-experimentos de budget (±15–20%, 3–4 dias, 2–3 campanhas PPT por vez), registrado numa tabela de eventos; análise automática da inclinação local após cada ciclo. Opcional: piloto de cost cap em 1 campanha PPT pra comparar contra o controle por budget.
- **Critério de sucesso:** após 6–8 semanas, inclinação local medida experimentalmente em ≥5 campanhas PPT; desvio médio entre inclinação experimental e a da curva desconfundida <30% (se maior, as curvas ainda enganam e o peso da decisão migra pros experimentos).
- **Uso pelo gestor:** ele mesmo executa as variações (são passos de ±20% que já faz), só que agendadas; em troca, as recomendações das campanhas testadas ganham selo "calibrado experimentalmente".

*(Discounted Thompson sampling entra como Fase 4 opcional, só se a política determinística da Fase 1 mostrar limitação concreta no walk-forward.)*

---

## 5. Aplicações práticas

Números lidos dos arquivos do projeto (os G* desta pasta ainda são pré-desconfundimento — marcados ⚠️).

**1. Rotina da manhã — PPT com espaço.**
`[PPT][FNC][VENDA] Brasil`: gasto R$13k/dia, G* ⚠️R$33k (R²=0.85). Se o G* desconfundido confirmar ≥R$20k: recomendação AUMENTAR, passo +20% → R$15,6k. Reavaliar sexta (48h). O gestor não pula pra R$33k — 2,5× de uma vez resetaria o learning e a curva não é confiável tão longe do observado.

**2. O fim de semana que motivou tudo — 09–10/mai.**
Demanda não-Meta a 0,72 → teto efetivo 0,72×180 = **R$129**. Backtest as-of 08/mai: REDUZIR 25 campanhas somando R$54,9k/dia, lideradas por BNO25/DOM a mCAC R$212–332. Perda real medida: mCAC incremental R$266–362, saving potencial R$31–73k. O sistema teria avisado na quinta à noite — a decisão do gestor seria não escalar +90% no sábado.

**3. LAN em ramp-up — não matar a escalada boa (21–27/mai).**
ROAS 3.48 no dia 21 (R$63k) escalando até R$254k no dia 27 (ROAS 2.22). A curva histórica diria "muito acima do G*, reduzir" desde o dia 22. A rota LAN da Fase 1 aplica a Abordagem C: ratio CPA_3d/acumulado ficou <1.0 durante toda a escalada → AUMENTAR/MANTER. Diferença de receita de seguir a regra errada: centenas de milhares de reais na semana.

**4. LAN saturando — quando cortar.**
Pelo backtest C: quando o ratio cruza 1.30, o ROAS mediano dos 3 dias seguintes é **0.75** (prejuízo direto). Ação: REDUZIR −20%/dia até o ratio voltar <1.15. Com a correção de maturação da Fase 1, o falso-positivo pós-escalada (conversões ainda não maturadas inflando o CPA_3d) deixa de disparar corte indevido.

**5. Dia de demanda fraca — teto dinâmico.**
Sábado com `demand_index` 0,85 e sem lançamento ativo: teto efetivo 0,85×180 = R$153. Campanhas operando a mCAC R$160–175 — aceitáveis num dia normal — aparecem como REDUZIR. Conecta com o achado DOW desta pasta (sábado em gasto baixo é o pior slot, índice 129): o índice de demanda captura a mesma coisa, mas por mecanismo, não por tabela de dia da semana.

---

## Decisões finais

**Implementar primeiro:** Fase 0 + Fase 1 juntas (a Fase 0 é pré-requisito curto da 1).

**Estimativa:** 4–7 dias úteis para as duas.

**O que preciso de você antes de começar:**

1. **Decisão de unificação** — o código canônico vive no `mmm_project/src/bidding/` (minha recomendação: já tem validação, testes de aceitação e desconfundimento) e a pasta `midia-paga/` vira o front (dashboard + ANALISE)? Ou prefere migrar tudo pra cá?
2. **Teto modulado por demanda** — o time aceita que o teto de R$180 vire dinâmico (`180 × demand_index`)? No evento de maio isso significa teto R$129. É mudança de regra de negócio, não técnica.
3. **Micro-experimentos de budget (Fase 3)** — os gestores toparam variar ±15–20% de propósito em campanhas PPT estáveis, em rodízio? Sem isso a identificação continua observacional e as curvas continuam com a ressalva de sempre.
4. **Snapshot pra delay de conversão** — o `dtm_analytics_facebook_ads_funnel` é restated (vendas do dia D mudam retroativamente)? Se sim, autorizar snapshots diários por ~3 semanas pra estimar a curva de maturação. Se não souber, eu verifico na Fase 0.
5. **Adstock** — l_max 8d (bidding) vs 14d (esta pasta): há razão de negócio pra 14, ou alinho tudo em 8?
