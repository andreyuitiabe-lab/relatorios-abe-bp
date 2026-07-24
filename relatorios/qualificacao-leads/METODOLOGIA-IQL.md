# Metodologia IQL — Índice de Qualidade de Lead

**Data:** jul/2026 · **Status:** proposta para apresentação
**Complementa:** [ALGORITMO-IQL.md](ALGORITMO-IQL.md) (evidências, ablações, ciclo de vida das perguntas, referências)

Este documento é o desenho formal da metodologia — feito para ser apresentado, defender credibilidade e manter-se com baixo custo quando perguntas e campanhas mudarem.

---

## 1. A tese em um parágrafo

CPL mede o custo de captar um lead, não a chance de ele virar receita — e os dois anticorrelacionam (DOM: CPL 2,6× maior que VDS, CAC 6,4× maior). Como a conversão de Não Membro demora ~421 dias, precisamos de um sinal **no dia do cadastro**. O IQL é esse sinal: um scorecard — a mesma metodologia que bancos usam há 50 anos para aprovar crédito no ato da proposta — que converte o que sabemos do lead no momento zero (status, histórico de cadastro, pesquisa) em probabilidade de conversão. Para o time de mídia, ele vira duas métricas na rotina existente: **IQL** (% de leads qualificados por anúncio) e **CPLq** (custo por lead qualificado — o CPL que importa).

**Por que scorecard e não uma caixa-preta de ML:** empatou com boosting nos nossos dados (AUC 0,746 vs 0,766, diferença sem valor prático), é explicável ao negócio ponto a ponto, e — decisivo para manutenção — os pesos vivem em tabelas de configuração versionadas, não em código ou modelo serializado. Quando uma pergunta muda, muda-se uma linha de configuração.

## 2. Arquitetura: 5 passos

```
pergunta crua ──(1) de-para──▶ atributo canônico ──(2) binning──▶ nível
                                                                    │
lead ◀──(4) faixa A/B/C ◀── score = Σ pontos ◀──(3) pontos por nível (WOE)
  │
  └──(5) agregação por anúncio: IQL (% faixa A) e CPLq (spend ÷ faixa A)
```

### Passo 1 — Normalização (o que torna o sistema parametrizável)

O score **nunca** referencia uma pergunta diretamente. Perguntas cruas são mapeadas para **atributos canônicos** — dimensões estáveis do lead — via tabela de-para:

| Atributo canônico | O que mede | Pergunta atual que o alimenta | Se a pergunta mudar |
|---|---|---|---|
| `status_cadastro` | relação contratual com BP | (não é pergunta — vem de `dim_subscriptions`) | nunca muda |
| `historico_cadastro` | reincidência e recência de cadastro | (não é pergunta — vem do histórico de leads) | nunca muda |
| `afinidade_bp` | proximidade declarada com a marca | relacao_bp + tempo_conhece_bp | nova pergunta → novas linhas no de-para |
| `paga_conteudo` | disposição a pagar por conteúdo | streaming (binário: paga algo / nenhum) | idem |
| `renda_declarada` | poder de compra declarado | *(dormente — pergunta removida jul/2026)* | reativa se a pergunta voltar |
| `respondeu_pesquisa` | intencionalidade | derivado (respondeu ≥1 pergunta) | automático |

A pesquisa muda de campanha para campanha; os atributos não. Uma pergunta nova entra no de-para em **modo coleta** (peso 0) e só ganha pontos quando prova IV — o ciclo de vida completo está na [seção 4b do ALGORITMO-IQL.md](ALGORITMO-IQL.md).

### Passo 2 — Binning (coarse classing)

Respostas cruas → níveis do atributo, seguindo as regras da literatura (Siddiqi):
- 4–6 níveis por atributo; nenhum nível com <5% da população nem >~50%;
- **"sem resposta" é sempre um nível próprio** (é informativo: não-respondente converte 0,70× a base);
- a tendência de WOE entre níveis deve fazer sentido de negócio — quebrar monotonia para ganhar IV é ruído (foi o critério que aposentou `qtd_streaming`).

### Passo 3 — Pontuação (WOE → pontos)

Para cada nível: `WOE = ln(P(nível|converteu) / P(nível|não converteu))`, com suavização para células pequenas e **pooling entre campanhas** (empirical Bayes) para estabilidade. Os pontos escalam o WOE pelo método padrão PDO de scorecards, com uma regressão logística sobre os atributos WOE-codificados resolvendo a correlação entre atributos (ex.: não responder 3 perguntas não penaliza 3×).

**Ninguém escolhe peso na mão.** Os pontos são gerados por script a partir dos dados e exportados para a tabela de configuração. Recalibrar = rodar o script na cohort madura nova. Ordem de grandeza dos sinais já validados (escala 20·ln(lift)):

| Sinal | Lift medido | Pontos (ordem de grandeza) |
|---|---|---|
| Membro Ativo (vs NM) | 4,9× (EVG) | ~+32 |
| Ex-Membro | 3,8× | ~+27 |
| NM · "assino/já assinei" na relação com BP | 2,0–2,2× | ~+15 |
| NM · paga algum streaming | 1,7× | ~+11 |
| NM · respondeu a pesquisa | 1,5× | ~+8 |
| NM · recadastro ≤30 dias | 1,2× | ~+4 |
| NM · recadastro frio (>180d) ou 5+ cadastros | 0,83× | ~−4 |
| NM · "nunca ouvi falar" | 0,23× | ~−28 |

*(valores finais saem do ajuste na semana 2 do plano — esta tabela é a ordem de grandeza para apresentação)*

### Passo 4 — Faixas

| Faixa | Definição | Leitura de negócio |
|---|---|---|
| **A — Qualificado** | pontos ≥ cutoff (calibrado para p(conv) ≥ ~2× a base NM) | vale pagar CPL premium |
| **B — Potencial** | intermediário | nutrir |
| **C — Frio** | pontos baixos | não pagar por mais desses |

O cutoff é **fixo em pontos durante a campanha** (definido na calibração) — não é percentil intra-campanha, senão o IQL% seria 20% por construção e não diferenciaria anúncios.

> **Evolução planejada (v0.3, pós-auditoria de literatura jul/2026):** cortes deixarão de ser múltiplos da taxa base e passarão a ser definidos por **valor esperado em R$** com estatística marginal (A: EV ≥ R$X; piso = break-even de Elkan: EV ≥ custo de tratamento), e a métrica de mídia ganhará o **ROAS esperado contínuo** (EV(s) via fórmula PDO × ticket maturado) ao lado do CPLq. Ver ALGORITMO-IQL.md §4b-2.

### Passo 5 — Agregação para mídia

- **IQL** = % de leads faixa A do anúncio/adset — só comparável **dentro da mesma campanha**;
- **CPLq** = spend ÷ leads faixa A;
- **NM-A/R$** = Não Membros faixa A por real gasto — o guardrail da meta de expandir a base (evita "melhorar o IQL" recapturando membros).

Regras de leitura obrigatórias: n ≥ 50 leads por criativo; shrinkage do IQL em direção à média da campanha proporcional ao n; decisão pós-campanha por conversão observada (nunca eRPL — refutado por circularidade).

## 3. Validação (o que dá credibilidade na apresentação)

1. **Backtest out-of-time** no EVG/BP10: o scorecard é ajustado numa janela e avaliado na seguinte. Critério: lift monotônico por decil e top-decil NM capturando ≥2× a base (benchmark atual do modelo: 2,1× sem renda, 2,6× com).
2. **Calibração:** faixa A deve converter na taxa prevista (±30%) na cohort madura.
3. **Teste retrospectivo da decisão:** aplicar a matriz CPL×IQL nos anúncios do EVG e mostrar que ela teria realocado budget do Pack 2 (CPL R$1,84, 11% qualificados) para o AD35 (CPL R$1,47, 30% qualificados) — decisão que o CPL sozinho não tomaria.
4. **Hit-rate contínuo:** a cada campanha encerrada, correlação de ranking (Spearman) entre CPLq da fase de captação e CAC real por adset — registrada em `metricas-referencia.md`. É o número que responde "o IQL funcionou?" campanha após campanha.

## 4. Manutenibilidade: 3 tabelas de configuração + 2 scripts

Tudo que muda com o tempo vive em **seeds versionados no git** (repo dbt):

| Artefato | Conteúdo | Quem mexe | Quando |
|---|---|---|---|
| `seed_iql_de_para.csv` | pergunta crua × resposta → atributo × nível | analytics | nova pergunta/campanha (antes do go-live) |
| `seed_iql_pontos.csv` | atributo × nível → pontos + `versao` | **gerado por script** | recalibração (pós-campanha) |
| `seed_iql_cutoffs.csv` | faixas A/B/C + parâmetros (n mínimo, shrinkage) | analytics | raramente |
| `iql_recalibra.py` | cohort madura → WOE/PDO → exporta seed_iql_pontos | roda pós-campanha | |
| `iv_perguntas.py` | leaderboard IV/CSI por pergunta (já existe) | roda pós-campanha | |

Regras de governança:
- **Marketing não vê os pesos exatos** (anti-Goodhart) — vê IQL, CPLq e a matriz de decisão.
- Scorecard versionado: toda pontuação de lead grava `cd_scorecard_version`; backtest sempre usa a versão vigente na época.
- Pergunta com opções alteradas ou posição mudada no formulário = pergunta **nova** no de-para (a antiga arquiva).
- Checklist de lançamento de campanha: pesquisa no fluxo + perguntas mapeadas no de-para + `fbp`/`fbc` capturados no cadastro (habilita a v2 CAPI).

## 5. Pipeline técnico

```
dtm_analytics_lead_conversion (diário)
  └─ int_iql_survey_normalizada   (aplica seed_iql_de_para)
      └─ fct_lead_iql             (pontos + faixa por lead; cd_scorecard_version)
          └─ mart_iql_midia       (anúncio × adset × dia: leads, IQL, CPLq, NM-A; join spend Meta)
              └─ relatório HTML no portal (padrão template: refresh.py + data.json)
```

Modelos dbt em `dbt_abe` (staging) na fase piloto; promoção a prod após a campanha piloto validar.

**Promoção ao dbt (quando a validação passar)** — mapeamento do protótipo v0 (`~/meu_projeto/BigQuery/iql_v0/`) para o repo:

| Hoje (protótipo) | No dbt |
|---|---|
| `seeds/*.csv` (de-para, pontos, cutoffs) | `seeds/` nativos do dbt (versionados no git do repo — privado, ok para pesos) |
| `sql/01_tb_lead_iql.sql` | `int_lead_iql_niveis` + `fct_lead_iql` — ⚠️ ler das **fontes** (`lead_registration`, `dim_subscriptions`), não do `dtm`, se o `dtm` for consumir o score (evita ciclo no DAG) |
| `sql/03_tb_iql_iv_perguntas.sql` | `mart_iql_iv_perguntas` + `mart_iql_woe_respostas` (schedule diário/semanal do próprio dbt Cloud/cron) |
| `vw_lead_conversion_iql` | coluna no `dtm` via join com `fct_lead_iql`, ou mantém como view |
| scheduled queries (agendar.sh) | substituídas pelo job dbt — descartar |

Requisitos da promoção: testes dbt (unicidade email×tag, faixas ∈ {A,B,C}, versão preenchida), SQLFluff, e gate de validação = critérios de sucesso do piloto (§6). Contrato: `cd_scorecard_version` gravada em toda linha continua obrigatória.

## 6. Plano de implementação

| Fase | Entregável | Esforço | Dependência |
|---|---|---|---|
| **1. Config e score** (semana 1) | ✅ **feito (jul/2026)** — 3 seeds + `tb_lead_iql` v0.1 escorando jan/2025+ (validado: faixa A 1,9× base) + `tb_iql_iv_perguntas` com auto-descoberta de perguntas | 2–3 dias | — |
| **2. Calibração v0.2** (semana 2) | ✅ **feito (jul/2026)** — `iql_recalibra.py` (WOE + regressão + PDO), atributos novos (`regiao_ddd`, `status_pessoa` via identity graph, `tempo_conhece`). **Backtest out-of-campaign (treino EVG → teste BP10): AUC NM 0,618 → 0,750; top decil 20,4% → 32,4% das vendas (lift 3,24×); sem relacao_bp perde quase nada (31,0%)** — valida a mudança do formulário. Ressalva: tempo_conhece tem IV suspeito no BP10; número pode estar otimista | 3–4 dias | fase 1 ✅ |
| **3. Dashboard** (semana 3) | ✅ **feito (jul/2026)** — relatório `qualificacao-leads/iql/` (template padrão): backtest, faixas × conversão real, monotonia, **CPL × IQL × CPLq por anúncio** (89 anúncios EVG/BP10), leaderboard IV com recomendações automáticas. Publicação no portal pendente de commit | 2 dias | fase 2 ✅ |
| **4. Piloto** (campanha seguinte) | rotina com time de mídia: leitura diária, matriz de decisão, realocações registradas | acompanhamento | fase 3 + pesquisa no fluxo |
| **5. Fechamento do piloto** | recalibração v2 do scorecard, hit-rate Spearman CPLq×CAC, leaderboard IV, go/no-go CAPI | 2 dias | cohort madura |
| **6. CAPI** (v2) | evento server-side "LeadQualificado" → Meta; otimização da campanha aponta para ele (leads são de site, não Instant Forms — ver correção no ALGORITMO-IQL.md §6) | a estimar c/ eng. | ✅ praticamente resolvida: `id_fbclid` já capturado (81,9% dos cadastros 2026) |

**Critérios de sucesso do piloto** (meta verificável antes de começar):
1. Backtest: lift monotônico por decil, top decil NM ≥2× a base;
2. Operação: time de mídia toma ≥1 decisão de realocação usando a matriz CPL×IQL e a registra;
3. Resultado: Spearman(CPLq, CAC real) por adset > Spearman(CPL, CAC real) — o IQL precisa prever o CAC melhor que o CPL, senão não paga a complexidade.

## 7. Registro de decisões (auditoria)

Toda decisão relevante do IQL fica registrada aqui com racional e evidência. **Processo de mudança:** proposta referencia o ID da decisão + evidência comparável (backtest nas mesmas cohorts congeladas) → se aprovada, gera nova versão do scorecard (`cd_scorecard_version`) e nova linha aqui. Nada muda silenciosamente.

### Modelo

| ID | Data | Decisão | Racional / evidência | Status |
|---|---|---|---|---|
| D1 | jul/26 | Scorecard WOE/PDO, não boosting/caixa-preta | Empate prático em AUC (0,746 vs 0,766, `benchmark.csv`); explicável ponto a ponto; pesos em config versionada | vigente |
| D2 | jul/26 | Score referencia **atributos canônicos**, nunca perguntas (de-para parametrizado) | Perguntas mudam por campanha; atributo é estável. Pergunta nova = modo coleta (peso 0) | vigente |
| D3 | jul/26 | LogReg **sem** class_weight, calibrada | Revisão adversarial jul/26: mesmo AUC, Brier 15× melhor; balanced infla score 30× | vigente |
| D4 | jul/26 | Pesos gerados por script a partir dos dados; nunca ajuste manual; congelados durante campanha | Comparabilidade intra-campanha + auditabilidade (`cd_scorecard_version` em toda linha) | vigente |
| D5 | jul/26 | Fonte = `dtm_analytics_lead_conversion` direto | `tb_leads_qualification_base` é snapshot estático de mai/26 (perdia EVG/BP10) | vigente |
| D6 | 09/jul | Campanha sem pesquisa → `pesquisa_indisponivel` (0 pts), não "não respondeu" (−17) | Não ser perguntado ≠ recusar. Validação: faixa A em campanhas pré-pesquisa (membros ocultos) converte 6,23% vs 1,88% da B, out-of-sample maduro | vigente |
| D7 | jul/26 | Cortes A/B/C por múltiplo da base (A: conv acumulada ≥2×; B ≥1,3×) | Partida pragmática; **reconhecido como provisório** — auditoria de literatura (08/jul, ALGORITMO §4b-2): corte deve ser econômico (EV em R$) e marginal | vigente até v0.3 |
| D8 | jul/26 | Recalibração em lote por campanha madura; **nunca** online nem no meio da campanha | Conversores precoces enviesariam o score contra o comprador lento (NM ~14 meses) | vigente |
| D9 | 08/jul | v0.3 (pós-piloto): cortes por EV em R$ com estatística marginal + ROAS esperado contínuo (PDO) + fator de maturação nos pesos | Auditoria de literatura (Thomas, Elkan, Baesens/EMP, VBB Google) — ALGORITMO §4b-2 | planejado |
| D10 | jul/26 | Pooling multi-campanha na recalibração (peso maior às recentes) | Uma campanha só = pesos reféns de idiossincrasia (ex: IV da tempo_conhece 0,93 no BP10 vs 0,08 no EVG) | planejado (v0.3) |

### Perguntas da pesquisa

| ID | Data | Decisão | Racional / evidência | Status |
|---|---|---|---|---|
| D11 | jul/26 | Ciclo de vida por IV (régua 0,02/0,1/0,5; coleta → promover/observar/aposentar; promoção é humana) | §4b do ALGORITMO; leaderboard automático `tb_iql_iv_perguntas` com auto-descoberta | vigente |
| D12 | jul/26 | Renda removida do formulário (decisão do negócio) | Ablação: top decil NM 25,5%→20,9%. Se voltar: 3 faixas bastam (R$10k+ era só ~20% do IV) | vigente |
| D13 | 09/jul | relacao_bp sai; tempo_conhece e streaming ficam; formulário = 2 core + 2 slots experimentais | Ablação: −2,3pp top decil; identity graph repõe o sinal de identidade (membro oculto 2,9×); níveis do meio instáveis entre campanhas | vigente |
| D14 | jul/26 | qtd_streaming e fonte_confianca aposentadas | IV <0,02; qtd_streaming quebra monotonia (2 serviços < 0 serviços = ruído) | vigente |

### Métricas e leitura

| ID | Data | Decisão | Racional / evidência | Status |
|---|---|---|---|---|
| D15 | jul/26 | Métricas de mídia: IQL + CPLq; guardrail NM-A/R$ | CPQL é padrão de mercado; NM-A evita "melhorar IQL" recapturando membros | vigente |
| D16 | jul/26 | Comparação só intra-campanha; n≥50/criativo; shrinkage; decisão pós-campanha por conversão observada (nunca eRPL) | Regras validadas (regras-negocio.md + revisão adversarial) | vigente |
| D17 | 09/jul | Quadrante com fronteira **iso-CPLq** (mediana = descritiva) + linha de **CPLq alvo** (normativa, default versionado por campanha, ajuste local via navegador) | Reta pela origem IQL=100·CPL/CPLq precifica o trade-off; quadrantes tratam custo e qualidade como vetos independentes | vigente (dashboard v3) |
| D18 | 10/jul | Significância traduzida em semáforo ● sólido / ◐ sinal / ○ insuficiente (Wilson IC95 + eventos mínimos; conv <5 vendas não exibe %) | Diretoria/mídia não lê p-valor; a pergunta real é "quão a risca levar" | vigente (dashboard v3) |
| D19 | 09/jul | Conversão precoce como indicador antecedente de safra: D+60 prevê ranking final (ρ 0,76); comparar campanhas só na mesma fase estrutural (calendário de oferta) | Medido em 10 campanhas 2025 maduras; encurta a validação do piloto de 14 meses para ~2 | vigente |
| D26 | 10/jul | **CPL máximo por segmento** = RPL observado × fator de maturação ÷ meta de retorno (default 1,5× sobre receita bruta, configurável). Veredito escalar/segurar/parar quando CPL corrente cruza os tetos | Fator de maturação = mediana histórica (D+30→D+240: 1,90; p25–p75 1,66–2,36). Break-even bruto não desconta margem/incrementalidade — a meta é a folga. Implementa o break-even de Elkan em nível de segmento antes da v0.3 | vigente (dashboard) |
| D27 | 14/jul | **Backtest em cohorts maduras** (RIO/MST/TPV 2025, 460k leads, >1 ano de receita, pesquisas antigas mapeadas via de-para): o score transporta mas atenuado — AUC NM 0,55–0,57, top decil 1,4–1,8×, faixa A 2,4× conv e **RPL R$24 vs R$6 da C**. Atenuação é genuína (sensibilidade de mapeamento piora o AUC): metade dos atributos sem dados nas pesquisas antigas + drift de pesos 2026→2025. Interpretação: desempenho pleno (BP10: 32%/3,2×) requer o conjunto completo de atributos das campanhas novas | registrado |
| D41 | 24/jul | **Status direto do dtm + membro_oculto descontinuado + parametrização (pós-2ª review)**. (1) `nm_status_level` passa a vir do `st_member_status_at_registration` do `dtm_analytics_lead_conversion` (bate 1:1 com a derivação anterior: NM 2,43M, ativo 195k, ex 151k, vitalício 19k) — remove os joins com `dim_subscriptions`/`dim_user`/`dim_person_identity` e **conserta a limitação da D40** (a coluna do dtm é as-of-cadastro, sem o viés retroativo do `dt_expires_in`). (2) **Membro oculto descontinuado** (revoga a D37): era o único consumidor do identity graph e do scan caro; medição mostrou que dropar **não contamina** o NM (conversão 3,807%→3,807%), custo = subvalorizar 55k leads/1,9% que convertem 8% (2,2× o NM). Escolha de manutenção mínima — o subsistema inteiro sai. (3) **Review 2 (skill /review, 8 finders) aplicada**: gate `delta_safra` com `LEFT JOIN` + teto auto-escalado para nível novo (antes o INNER JOIN deixava nível novo passar sem limite); gate `universal_so_prior` ignora atributo em quarentena (β=0); `seed_iql_cutoffs` ganha `not_null`+`accepted_values`; **precedência multi-select** via `nr_precedence` no de-para (D40 resolvida: streaming Netflix+BP → `paga_algum`, não mais o alfabético `bp_informal`); **mapa de atributos centralizado no macro `iql_attributes()`** (fonte única: WOE vivo, 10 joins do fct e teste de reconciliação são gerados dele — atributo novo = 1 edição); **constantes de tuning viram `vars` `DBT_IQL_*`** (PDO, 240d, 100 conv, era 2026, cobertura 5%/razão 2,0, bootstrap 30, gate 5/10 pts). Refutados na review (sem ação): regex de DDD (backtracking resolve o DDD 55), cbo sem dedup (dtm tem grão único). Validado: 21/21 testes, faixas estáveis (v1-d3245efb) | vigente |
| D40 | 23/jul | **Revisão sênior do MR !2426 aplicada** — 2 críticos corrigidos: (1) o gate de sanidade dos pesos movido para **dentro do INSERT** do `fct_iql_pesos` (antes o teste rodava depois da materialização: a versão ruim já estava persistida no append-only e o pipeline entrava em deadlock sem runbook; agora candidata reprovada = zero linhas gravadas = a vigente permanece, rollback implícito — o teste virou monitor `warn` de "candidata bloqueada"); (2) `NOT IN` → `NOT EXISTS` no filtro incremental (um `cd_versao` NULL travaria todas as versões futuras silenciosamente) + `not_null` no yml. Médios aplicados: testes generic no `fct_iql_pesos` (not_null + unicidade atributo×nível×versão), `full_refresh=false` nos 2 modelos de trilha de auditoria, guard de rerun no mesmo dia no histórico (grão diário), teste de reconciliação níveis×pesos (nível sem peso = falha explícita, não 0 silencioso), e **padrões de nome do repo adotados** antes de existir consumidor do cbo: **todas as colunas dos 11 modelos IQL passaram para inglês** (mecânica do scorecard + termos de domínio — `nm_attribute`/`nm_level`/`nm_iql_band`/`nm_question`/`nm_answer`/`vl_total_weight`/`tx_rule`/`qt_iql_points`/`cd_scorecard_version`/`nr_registration`/`qt_sales`, e o padrão `nm_<atributo>_level` para os níveis), **os VALORES ficam em português** (`membro_ativo`, `sem_resposta` etc. — o de-para, os `accepted_values` e esta metodologia os referenciam), e todos os modelos terminam em `SELECT * FROM final`. **Limitações registradas (sem mudança de código)**: (a) status-no-cadastro usa a janela corrente da assinatura — cadastro feito durante lapso de pagamento que depois renovou (mesma assinatura) vira `membro_ativo` retroativo; população pequena, direção conservadora, autocorrige no rebuild diário; mesmo caráter as-of-hoje no grafo do membro_oculto; (b) precedência de respostas multi-select no de-para resolvida por `MIN()` (ordem alfabética acidental) — follow-up: coluna de precedência no seed quando houver caso real | vigente |
| D39 | 22/jul | **Pesos vivos** — WOE recalculado pelo próprio pipeline dbt a partir das campanhas maduras; a manutenção humana reduz-se ao de-para (objetivo: menor rotina possível). Componentes: (1) **trava de maturidade p99 ≤ hoje−240d + ≥100 conv NM** — p99 ignora stragglers (a regra por MAX segurava RIO/ODD/MST fora do treino por 13 meses e descartava 78% das conversões maduras; hoje: 13 tags no treino, âncoras incluídas); 240d cobre o membro que compra no evento seguinte; (2) atributos de pesquisa treinam só em tag in-funnel **2026+** com **exposição uniforme das perguntas (razão de cobertura ≤2,0** — BP10 6,5 barrado, EVG 1,9 passa, ELB26 1,0 é o padrão; threshold provisório, reavaliar no 1º refit) e pergunta exibida na tag (≥5%); (3) **prior de bootstrap** = pesos v0.3 como 30 pseudo-eventos/nível — domina enquanto não há safra madura no regime e desaparece conforme dados acumulam (campanhas antigas vivem aqui: validaram o modelo e dão o ponto de partida); (4) **β congelados**, revalidados por evento (mudança de formulário, 1ª safra in-funnel madura), não por rotina; (5) **congelamento por evento de safra**: `fct_iql_pesos` append-only versionado, versão = hash do conjunto de treino (`v1-…`, auditável) — pesos imutáveis entre eventos, D4 preservada, histórico completo como trilha; (6) **cortes rederivados por evento de safra** com histerese ±2 pts (percentis operacionais 1,5/15/50/85% dos NM in-funnel — a troca de escala v0.3→v1 quebrou os cortes estáticos na primeira validação e provou a regra); (7) **bateria de testes bloqueantes** no lugar de revisão humana (âncoras de sinal do status, treino vazio, universal só-prior, delta >5 pts/nível entre versões, anti-colapso do sem_resposta, unicidade) — falhou, pipeline bloqueia e a versão anterior segue vigente. **Evidência adversarial**: revisão independente (Model QA, 22/jul, duas rodadas com verificação empírica no BQ) — aprovado com condições, todas implementadas. Achados incorporados: **leakage confirmado e corrigido** (`cd_contact_phone` é preenchido na compra — conv 17–25% quando presente vs 0,05%; atributo passa a usar só o telefone do cadastro) e **regiao_ddd em quarentena (β=0)**: o sinal inverte entre eras mesmo com o campo limpo (2025: sem_ddd converte ~2× mais; 2026: ~4× menos) — viola a premissa do pooling. Agenda do 1º refit (EVG matura ~mar/2027; ELB26 ~abr/2027): reavaliar DDD (consistência em ≥3 tags), threshold de uniformidade, teste WOE de pesquisa NM-only vs geral | vigente |
| D38 | 21/jul | **Config em SQL, não CSV**: os 4 seeds viraram modelos dbt (`SELECT FROM UNNEST([STRUCT...])`) — os fluxos de CI/defer do repo (`dbt run`) não contemplam seeds (primeiro uso no repo). Mesmos nomes, refs intocados; config-como-dado preservado (valores gerados pela calibração, diff revisável — D4 vale igual); recarga diária garantida independente de `build` vs `run`. **Pipeline do MR !2426 verde em todos os 6 jobs** (lint, compile, dry-run, integrity, docs com 102 colunas documentadas, unit tests) — pronto para merge/go-live | vigente |
| D37 | 21/jul | **Membro oculto é membro**: reclassificado de nível de atributo separado para **nível do status** (`membro_oculto`) — sai das métricas de expansão de base (NM-*), onde inflava o guardrail, e entra no lado membro para tratamento/personas/clusters. Pontos dobrados de forma neutra (+3 líquido — nenhum score mudou); peso próprio preserva a calibração (converte 8% na base geral — entre NM 3,7% e ex 14,6% — não os 27% do membro declarado; parte da conversão dele realiza no e-mail principal da pessoa, invisível no grão e-mail). Base atual: 55k membros ocultos (1,9% da base) | vigente |
| D36 | 21/jul | **ELB26 (campanha nova) mapeada e pontuando** — formulário real do time: tempo_conhece (de-para existente, já pontuava) · **assina_streaming binária** (→ paga_conteudo — a codificação recomendada virou pergunta) · **renda de volta em 5 faixas** (quase a reformulação proposta na D12) · midia_tradicional em coleta (IV decide). **Renda REATIVADA** com calibração conjunta em receita madura: 15k+ +22 / 10–15k +17 / 5–10k +9 / até-5k −4 / não-informa −4 (univariado seria até +36 — crédito dividido com ocupação/região; β renda 0,62 = sinal próprio forte confirmado). Idade/ocupação seguem dormentes (fora do formulário). Verificação ELB26: 11k leads com renda escorada, gradiente de score coerente (sem_resposta −18 → 15k+ +31). ELB26 é a candidata a piloto — congelar v0.3 ao formalizar. **Obs. metodológica (21/jul)**: os IVs do BP10 estão contaminados por exposição desigual das perguntas (cobertura 8–68%, formulário mudou de fase durante a campanha; responder tarde correlaciona com a janela de compra) — tempo_conhece IV 1,21 é o sintoma extremo; as ex-aposentadas aparecendo fortes lá NÃO revertem decisões tomadas no EVG (exposição uniforme). Regra derivada: **IV só é comparável entre perguntas com exposição uniforme** — o bloco único da ELB26 (cobertura idêntica 51,2% nas 4) é o desenho correto e vira requisito de formulário | vigente |
| D35 | 20/jul | **v0.3 montada e no MR !2426** (assume antes do piloto; congela ao entrar nele). Pesos: pooling por regime (pesquisa in-funnel EVG/BP10; universais nas 5 tags) — LOO out-of-campaign: ≥ v0.2 em 3/4 confrontos justos (RIO AUC 0,545→0,627), empate no regime novo (BP10 36,0% vs 35,9% top decil). Idade/ocupação calibradas **em conjunto** (crédito dividido: 60+ vale +5 vs +14 univariado; aposentado +8; estudante −12) — dormentes até o de-para do formulário novo. **5 faixas por tamanho operacional com EV maduro de referência** (A+ 2% NM/R$20,74 → Comercial · A 18%/R$11,25 → métrica de mídia · B/R$9,53 · C/R$4,80 · D 10%/R$2,47) = os 5 valores distintos do CAPI; ressalva: A/B separam pouco no regime antigo (pesquisa limitada), esperado abrir no in-funnel. Mapeamento de pesquisa genérico no dbt (pergunta nova = linhas de seed). **Challenger RF institucionalizado: perdeu por 0,117 de AUC out-of-campaign — D1 mantida com a evidência mais forte até aqui.** Pendências da v0.3: dashboard migrar para fct_lead_iql/5 faixas; de-para de idade/ocupação quando o formulário fechar; modelo IV no dbt | vigente |
| D34 | 20/jul | **M_fase rebaixada a refinamento opcional** (não entra como padrão da v0.3): não toca o score — afeta só a precisão do forecast (±25%→±12%), e custa manutenção de calendário validado + % pré-venda por campanha + exceções (venda direta) + fragilidade em campanha ao vivo (abertura às vezes só conhecida retroativamente). Forecast padrão segue no relógio do cadastro como faixa; M_fase plugável por campanha quando a data de abertura for sólida. Aprofundamento (clusters × fase × calendário de eventos) adiado para pós-piloto. O diagnóstico dos 3 relógios (D33) permanece como conhecimento validado | vigente |
| D33 | 17/jul | **M(t) por fase estrutural validada** (9 campanhas maduras, abertura de venda do calendário + TPV derivada dos dados): erro do retro-forecast em abertura+30d cai de **±25% para ±12% mediano** (7 de 9 dentro de ±14%). Dois parâmetros: % pré-venda (4–28% — venda direta da LP durante aquecimento) + curva pós-abertura. Outliers explicáveis: TLR (28% pré-venda — produto vendido direto na LP) e TPV (abertura derivada, campanha pequena) — campanhas de venda direta usam curva própria. **Evidência direta do relógio (RIO, 20/jul)**: cortando por semana de cadastro, todos os grupos compram na mesma quinzena de calendário da venda (17–34% do total, estável) independente da antecedência do cadastro; só a compra direta na LP segue o relógio do cadastro (27%→0% conforme o cadastro se aproxima da abertura); a cauda (~60%) segue o calendário de eventos da casa — três relógios, e o da oferta domina a janela da campanha. **Piso da faixa D** parametrizado: custo de régua por lead = n_wpp×0,4528 + n_email×0,0008 + n_sms×0,0552. **Régua REAL medida (EVG, 2 meses, fct_leads_events, 20/jul)**: 1,3 WhatsApp médio (mediana 0 — concentrado num subconjunto) + 28,9 e-mails → **custo médio real R$0,61/lead, sendo 96% WhatsApp**. Regra derivada: o piso D governa o *WhatsApp* (suprimir wpp quando EV < ~R$0,60); e-mail é ~grátis (R$0,02/lead) e pode continuar para quase todos. Cenários hipotéticos anteriores (R$0,92/1,95/3,89) substituídos pela medição. Query: `iql_v0/fase_curva.csv` + medição no transcript 20/jul | vigente |
| D32 | 17/jul | **Insumos de negócio para a v0.3 entregues**: (1) custos unitários de tratamento — WhatsApp R$0,4528 · e-mail R$0,0008 · SMS R$0,0552 por disparo (piso da faixa D = break-even de Elkan parametrizado pela régua de contatos); (2) **meta de retorno oficial: 1,5×** sobre receita bruta ("por enquanto" — revisável); (3) janelas de venda das campanhas históricas via `campanhas-calendario.md` (fonte do M(t) por fase estrutural). Autoriza onda 1 + M(t) por fase da onda 2 | vigente |
| D31 | 17/jul | **Forecast por composição de clusters**: receita projetada da campanha = Σ leads do cluster × valor maduro do cluster × M_cluster(t). 6 clusters com parâmetros medidos (RIO/MST/TPV maduras): Vitalício R$515,71/lead (ticket R$2.816) · Membro R$129,62 · Ex R$44,64 · NM-A R$24,28 · NM-B R$7,83 · NM-C R$6,20. Curvas de maturação distintas: NM/Ex rápidas (43–48% das conversões até D+30), Membro/Vitalício lentas (13–17% — realizam no evento seguinte). NM ancora no nível da campanha (múltiplos relativos); status com valor absoluto de referência (faixa entre tags como incerteza) | vigente (dashboard em construção) |
| D30 | 16/jul | **Escopo consolidado da v0.3** (gatilho: fim do piloto; treina em cohorts maduras 2025 + EVG/BP10 ajustadas por maturação): núcleo D9/D10 (cortes por EV marginal em R$, EV contínuo via PDO, pooling multi-campanha, valores congelados+maturação) + renda reativada (3 faixas e/ou CEP→IBGE; escada madura 6×) + idade/ocupação com pesos de receita realizada + M(t) por fase estrutural (maior fonte de erro do forecast) + **M(t) por status** (medido 17/jul em cohorts maduras: NM realiza 47,6% das conversões até D+30, membro ativo só 12,8% — membro compra no evento seguinte, não no flight; curva única distorce campanhas com mix de recaptura diferente) + score em ≥5 níveis (requisito do value optimization Meta; conecta D25) + identity graph por telefone + check de calibração por decil (pré-requisito do EV) + PSI automático e taxa de resposta por adset + rebinning do histórico de cadastro. Fora: engajamento pós-cadastro (v0.4) e troca de motor (D1 mantida) | planejado |
| D29 | 16/jul | **Modelo preditivo de receita por lead** em 3 equações: (1) receita_final da campanha = observada(t) ÷ M(t), curva de maturação **única** (compartilhada entre faixas — medido: A/B/C atingem 44–49% em D+30); (2) distribuição pelo score: conv_banda = base × lift_banda; (3) valor = conv × **ticket por banda** (A R$319 / B R$233 / C R$221, maduro). Validação retro-forecast leave-one-out: erro ~±25% a partir de D+30 (RIO −1%, TPV −26%, MST +26–33% — matura mais rápido que as pares). D+14 é território de prior (±21–56%). Refinamento previsto: alinhar M(t) por **fase estrutural** (calendário de oferta), que explica o desvio do MST. Forecast reportado sempre como faixa, nunca ponto | vigente |
| D28 | 14/jul | **Valores relativos de lead para RPL esperado e forecast** (receita madura, pooled RIO/MST/TPV): não-NM ≈ **11×** o NM médio (8,7–13,7× entre tags); NM-A **3,3×** · NM-B 1,05× · NM-C 0,83×. Fórmula: `RPL_esperado(anúncio) = base_NM_campanha × Σ share_grupo × múltiplo`; `CPL_alvo = RPL_esperado ÷ meta`. Ressalva: múltiplo do A encolhe quando a faixa A é larga (seleção) — múltiplos pooled vêm de campanhas com A estreito; v0.3 substitui por EV contínuo. Renda madura confirma escada 0,54×→3,20× de RPL — reforça reativação renda/CEP na v0.3 | vigente (dashboard) |

### Governança e publicação

| ID | Data | Decisão | Racional / evidência | Status |
|---|---|---|---|---|
| D20 | jul/26 | Pesos do scorecard **não circulam** para quem opera campanhas; repo público só recebe agregados; assert programático no `data.json` (sem WOE/pontos) | Anti-Goodhart; decomposição do score publicada só como shares relativos + fatos de mix | vigente |
| D21 | jul/26 | ICPs por cascata mutuamente exclusiva (Reencontrado → Simpatizante → Pagante → Frio → neutro) + anti-persona + avisos de viés de seleção | Somas fecham 100%; personas com números auditáveis (`icps` no data.json) | vigente |
| D22 | jul/26 | Gate do piloto: Spearman(CPLq, CAC) > Spearman(CPL, CAC) por adset; sem passar, IQL não promove | O IQL precisa provar que dirige melhor que o CPL, senão não paga a complexidade | vigente |
| D23 | jul/26 | Promoção ao dbt só pós-gate; agendamento via processo dbt (sem scheduled queries paralelas) | §5 (mapeamento protótipo→dbt); repo dbt privado pode versionar seeds/pesos | vigente |
| D24 | jul/26 | v2 CAPI: enviar **estágio** "LeadQualificado" (não valor previsto) para leads de site; value-based fica para v3 com valor calibrado em R$ | eRPL por adset refutado (circularidade); estágio real é robusto contra Goodhart no leilão. `id_fbclid` já capturado (81,9% dos cadastros 2026) | planejado |
| D25 | jul/26 | Faixas extras A+ (abordagem ativa) e D (supressão CRM) só quando os tratamentos existirem | Faixa sem ação é decoração; dados suportam até 5 bandas separáveis (ICs sem sobreposição) | condicionado |

Detalhes de implementação do dashboard (iterações, decisões de visualização): `ANALISE.md` da pasta. Evidências e ablações: `ALGORITMO-IQL.md`. Pesos e calibração: `~/meu_projeto/BigQuery/iql_v0/` (privado).

## 8. Riscos e respostas prontas (para a apresentação)

| Pergunta que vão fazer | Resposta |
|---|---|
| "Por que não usar só o CPL?" | DOM×VDS: CPL 2,6× maior, CAC 6,4× maior. CPL não prediz qualidade — está em `regras-negocio.md` com números. |
| "Por que confiar num score se a conversão demora 14 meses?" | Backtest: nos dados de 2025–26, o top decil do score capturou 26% das vendas de NM (2,6× a base). O score é validado contra conversão real, cohort a cohort. |
| "E se a pesquisa mudar?" | O score referencia atributos, não perguntas. Pergunta nova entra em modo coleta e só ganha peso quando prova IV. Nada quebra. |
| "E quem não responde a pesquisa?" | Status + histórico de cadastro cobrem 100% dos leads; "não respondeu" é sinal por si (0,70×). |
| "O marketing não vai 'hackear' o score?" | Pesos não são divulgados; o hit-rate contra CAC real é auditado toda campanha; sinal majoritário (status, histórico) não é manipulável. |
| "Como funciona numa campanha nova?" | Pontua desde o dia 1 com o scorecard vigente (atributos são da pessoa, não da campanha; status+histórico cobrem 100% dos leads). Pesos ficam congelados durante a campanha (comparabilidade entre anúncios + auditoria via `cd_scorecard_version`) e o sistema reaprende entre campanhas: recalibração com pooling quando a cohort matura, pergunta nova entra em modo coleta e é promovida se provar IV. Aprendizado em lote versionado, não online — recalibrar no meio com as primeiras conversões enviesaria o score para o comprador rápido (NM típico demora ~14 meses). |
