# Metodologia IQL — Índice de Qualidade de Lead

**Data:** jul/2026 · **Status:** implementado (MR !2426, aguardando merge) — atualizado 31/jul/2026
**Complementa:** [ALGORITMO-IQL.md](ALGORITMO-IQL.md) (evidências, ablações, ciclo de vida das perguntas, referências)

Este documento é o desenho formal da metodologia — feito para ser apresentado, defender credibilidade e manter-se com baixo custo quando perguntas e campanhas mudarem.

---

## 1. A tese em um parágrafo

CPL mede o custo de captar um lead, não a chance de ele virar receita — e os dois anticorrelacionam (DOM: CPL 2,6× maior que VDS, CAC 6,4× maior). Como a conversão de Não Membro demora ~421 dias, precisamos de um sinal **no dia do cadastro**. O IQL é esse sinal: um scorecard — a mesma metodologia que bancos usam há 50 anos para aprovar crédito no ato da proposta — que converte o que sabemos do lead no momento zero (status, histórico de cadastro, pesquisa) em probabilidade de conversão. Para o time de mídia, ele vira duas métricas na rotina existente: **IQL** (% de leads qualificados por anúncio) e **CPLq** (custo por lead qualificado — o CPL que importa).

**Por que scorecard e não uma caixa-preta de ML:** empatou com boosting nos nossos dados (AUC 0,746 vs 0,766, diferença sem valor prático), é explicável ao negócio ponto a ponto, e — decisivo para manutenção — o peso de cada resposta é recalculado pelo próprio pipeline a partir das campanhas maduras e versionado por safra, não fica preso em código nem em modelo serializado. Quando uma pergunta muda, muda-se uma linha de configuração.

## 2. Arquitetura: 5 passos

```
pergunta crua ──(1) de-para──▶ atributo canônico ──(2) binning──▶ nível
                                                                    │
lead ◀──(4) faixa A+/A/B/C/D ◀── score = Σ pontos ◀──(3) pontos por nível (WOE × β × PDO)
  │
  └──(5) agregação por anúncio: IQL (% faixa A+∪A) e CPLq (spend ÷ faixa A+∪A)
```

### Passo 1 — Normalização (o que torna o sistema parametrizável)

O score **nunca** referencia uma pergunta diretamente. Perguntas cruas são mapeadas para **atributos canônicos** — dimensões estáveis do lead — via `dim_iql_mapping`. São 11 atributos, dos quais 8 ativos e 3 em quarentena:

| Atributo canônico | O que mede | Fonte | Estado |
|---|---|---|---|
| `status_cadastro` | relação contratual com a BP no dia do cadastro | `st_member_status_at_registration` do dtm (D41) | ativo — o mais forte |
| `historico_cadastro` | reincidência e recência de cadastro | histórico de leads do próprio e-mail | ativo |
| `respondeu_pesquisa` | intencionalidade | derivado (respondeu ≥1 pergunta) | ativo |
| `afinidade_bp` | proximidade declarada com a marca | `relacao_bp` | ativo |
| `tempo_conhece` | há quanto tempo conhece a BP | `tempo_conhece_bp` | ativo |
| `paga_conteudo` | disposição a pagar por conteúdo | `streaming` / `assina_streaming` | ativo — 3 níveis (D47) |
| `renda_declarada` | poder de compra declarado | `renda` | ativo |
| `confianca_midia` | ruptura com a imprensa tradicional | `midia_tradicional` | ativo desde a D48 |
| `regiao_ddd` | proxy geográfico de poder de compra | DDD do telefone do cadastro | **quarentena** — sinal inverte entre eras (D39) |
| `idade` | faixa etária | *(o formulário não coleta)* | **quarentena** (D49) |
| `ocupacao` | ocupação declarada | *(o formulário não coleta)* | **quarentena** (D49) |

Quarentena = β 0, contribui zero pontos. Não é remoção: o atributo segue mapeado e volta trocando uma linha de configuração quando o sinal se provar.

A pesquisa muda de campanha para campanha; os atributos não. Uma pergunta nova entra no de-para em **modo coleta** (`nm_status = 'coleta'`, zero ponto) e só é promovida quando o IV comprova — ciclo de vida completo em [PERGUNTAS-FORMULARIO.md](PERGUNTAS-FORMULARIO.md).

### Passo 2 — Binning (coarse classing)

Respostas cruas → níveis do atributo, seguindo Siddiqi:
- a tendência de WOE entre níveis deve fazer sentido de negócio — quebrar monotonia para ganhar IV é ruído;
- **"sem resposta" é sempre um nível próprio** (é informativo: não-respondente converte abaixo da base);
- só se juntam bins de **risco similar**. Foi por isso que a D47 revogou a D46 e devolveu o `bp_informal` a nível próprio: colapsá-lo em `paga_algum` juntava bins que convertem 5,11% e 2,66% (1,9× de diferença) e derrubava o IV do atributo de 0,125 para 0,068.

**O critério operativo de tamanho de bin é número de conversões, não percentual da população.** A régua dos 5% da literatura não protege contra o caso real: um nível com 8% da base e 19 conversões dá WOE instável. Foi esse critério que colapsou os dois níveis superiores de `confianca_midia` (D48) e os níveis de topo de `renda_declarada`.

### Passo 3 — Pontuação (WOE → pontos), com **pesos vivos**

Para cada nível: `WOE = ln(P(nível|converteu) / P(nível|não converteu))`, com suavização para células pequenas e **pooling entre campanhas** para estabilidade. Os pontos escalam o WOE pelo método PDO padrão:

```
pontos = ROUND(fator_PDO × β × WOE)      fator_PDO = 20 / ln(2) = 28,8539
```

O β vem de uma regressão logística sobre os atributos WOE-codificados e resolve a correlação entre eles (não responder 3 perguntas não penaliza 3×).

**Ninguém escolhe peso na mão — e desde a D39 ninguém roda script para recalibrar.** O WOE é recalculado **pelo próprio pipeline dbt** a cada execução, a partir das campanhas maduras, e congelado por **evento de safra** (`cd_version` = hash do conjunto de tags de treino). O β fica congelado, revalidado por evento (mudança de formulário, primeira safra madura no regime), não por rotina.

**A única manutenção humana que sobrou é o de-para.**

Trava de maturidade: uma tag entra no treino quando o **p99** dos seus cadastros é ≤ hoje−240 dias **e** ela tem ≥100 conversões de Não Membro — hoje 14 tags. O p99 (em vez do máximo) evita que um cadastro retardatário segure a campanha inteira fora do treino; os 240 dias cobrem o membro que compra no evento seguinte.

Enquanto não há campanha madura com pesquisa in-funnel, os atributos de pesquisa rodam sobre um **prior de bootstrap** (a calibração v0.3 entra como pseudo-observações de peso fixo). Ele domina agora e desaparece sozinho conforme dado maduro acumula — o EVG matura por volta de mar/2027.

Ordem de grandeza dos sinais já validados (escala 20·ln(lift)) — os valores exatos vivem no repo dbt, não aqui (governança D20):

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

### Passo 4 — Faixas

Cinco faixas, com **valor esperado em R$** por lead (a evolução v0.3 planejada em jul/2026 já está implementada):

| Faixa | Leitura de negócio |
|---|---|
| **A+** | topo (~1,5% dos NM in-funnel) — vale abordagem ativa |
| **A** | qualificado — é o que entra no IQL e no CPLq |
| **B** | potencial — nutrir |
| **C** | frio — não pagar por mais desses |
| **D** | fundo — suprimir WhatsApp quando o EV cai abaixo da régua de custo (D33) |

Os cortes são **fixos em pontos durante a campanha** — não percentil intra-campanha, senão o IQL% seria constante por construção e não diferenciaria anúncios. São rederivados **por evento de safra**, com histerese de ±2 pontos para não oscilar por ruído, mirando os percentis operacionais 1,5 / 15 / 50 / 85% dos NM in-funnel.

Para métricas que foram medidas em 3 faixas (múltiplos de valor D28, forecast D31), a correspondência é A+∪A → A, B → B, C∪D → C, até serem re-medidas em 5 faixas no 1º refit.

### Passo 5 — Agregação para mídia

- **IQL** = % de leads faixa A+∪A do anúncio/adset — só comparável **dentro da mesma campanha**;
- **CPLq** = spend ÷ leads faixa A+∪A;
- **NM-A/R$** = Não Membros faixa A por real gasto — o guardrail da meta de expandir a base (evita "melhorar o IQL" recapturando membros).

Regras de leitura obrigatórias: n ≥ 50 leads por criativo; shrinkage do IQL em direção à média da campanha proporcional ao n; decisão pós-campanha por conversão observada (nunca eRPL — refutado por circularidade).

## 3. Validação (o que dá credibilidade na apresentação)

1. **Ordenamento monotônico dentro de campanha** — o critério válido (D16: o agregado entre campanhas **não** é comparável, porque a mistura de faixas difere por campanha). EVG: A+ 3,78% → D 0,30%. BP10: A+ converte 21× o D.
2. **Distribuição bate o alvo de percentis** nos NM in-funnel: A+ 1,5% (alvo 1,5%), acumulado A 16,4% (alvo 15%), acumulado C 85% (alvo 85%).
3. **Backtest out-of-time** (treino EVG → teste BP10): AUC NM 0,618 → 0,750; top decil 20,4% → 32,4% das vendas (lift 3,24×).
4. **Teste retrospectivo da decisão:** aplicando a matriz CPL×IQL nos anúncios do EVG, ela teria realocado budget do Pack 2 (CPL R$1,84, 11% qualificados) para o AD35 (CPL R$1,47, 30% qualificados) — decisão que o CPL sozinho não tomaria.
5. **Hit-rate contínuo:** a cada campanha encerrada, correlação de ranking (Spearman) entre CPLq da captação e CAC real por adset — registrada em `metricas-referencia.md`. É o número que responde "o IQL funcionou?" campanha após campanha.

⚠️ **O EV de referência não transfere entre campanhas.** O RPL real varia muito (BIT R$79 → RIO R$10, 8×) enquanto o EV de referência é achatado e ancorado numa campanha só. Ele serve para **ordenar** faixas, não para prever receita absoluta de uma campanha nova.

## 4. Manutenibilidade: 1 tabela editada à mão

Toda a configuração vive em **modelos SQL versionados no git** (repo dbt) — não em seeds CSV: o CI roda `dbt run --defer`, que não executa `dbt seed`, então os cinco são `SELECT ... FROM UNNEST([STRUCT(...)])` com a tag do job diário (D38). Continuam sendo config-como-dado, com diff revisável em MR.

| Modelo de config | Conteúdo | Quem mexe | Quando |
|---|---|---|---|
| `dim_iql_mapping` | pergunta crua × resposta → atributo × nível (+ precedência para multi-resposta) | **analytics (manual)** | **nova pergunta de formulário — a única rotina** |
| `dim_iql_betas` | β congelado por atributo; β 0 = quarentena | analytics | por evento (atributo novo, revalidação) |
| `dim_iql_cutoffs` | cortes das 5 faixas + EV em R$ + n mínimo | analytics | evento de safra (histerese ±2 pts) |
| `dim_iql_woe_bootstrap` | prior de WOE (calibração v0.3) | ~nunca | desaparece sozinho conforme dado maduro acumula |
| `dim_iql_ddd_region` | DDD → UF → grupo de região | ~nunca | — |

O que **saiu** da manutenção humana com a D39: a tabela de pontos. Não existe mais `seed_iql_pontos.csv` nem script de recalibração no fluxo — o `fct_iql_weights` é gerado pelo pipeline e versionado por safra.

Regras de governança:
- **Marketing não vê os pesos exatos** (anti-Goodhart) — vê IQL, CPLq, faixa e a matriz de decisão. Os β e os pontos vivem no repo dbt (privado); este documento fica na ordem de grandeza.
- Scorecard versionado: toda pontuação grava `cd_scorecard_version`; backtest sempre usa a versão vigente na época.
- Pergunta com opções alteradas ou posição mudada no formulário = pergunta **nova** no de-para (a antiga arquiva).
- Checklist de lançamento de campanha: pesquisa no fluxo + perguntas mapeadas no de-para + `fbp`/`fbc` capturados no cadastro (habilita a v2 CAPI).

## 5. Pipeline técnico

11 modelos + 1 macro + 2 testes, no repo `bp-dbt-dw` (MR !2426), todos na tag `11h00_utc` do job diário:

```
CONFIG (dim_iql_*)                          FONTE
  mapping · ddd_region · betas                dtm_analytics_lead_conversion
  woe_bootstrap · cutoffs                            │
        │                                            ▼
        ├───────────────────────▶ ① int_iql_lead_levels     (níveis canônicos por lead × tag)
        │                                            ▼
        ├───────────────────────▶ ② int_iql_woe_live        (WOE das tags maduras + prior; define a versão)
        │                                            ▼
        ├───────────────────────▶ ③ fct_iql_weights         (WOE × β × PDO → pontos) [incremental, append-only]
        │                                            ▼
        └───────────────────────▶ ④ fct_lead_iql            (score + faixa + EV por lead)
                                                     ├──▶ ⑤ cbo_lead_conversion_iql  (dtm + score — consumo)
                                                     └──▶ ⑥ fct_lead_iql_history     (auditoria) [incremental]

TESTES: iql_weights_sanity (warn) · iql_missing_weight_levels (error)
MACRO:  iql_attributes() — fonte única do mapa atributo → coluna → regime
```

**O gate no lugar da revisão humana.** Como ninguém revisa os pesos a cada safra, o `fct_iql_weights` só grava uma versão nova se ela passar por um gate de sanidade **embutido no INSERT**: âncoras de sinal do status, treino não-vazio, atributo universal com dado real além do prior, delta ≤5 pts por nível entre versões, anti-colapso do `sem_resposta`, unicidade. Candidata reprovada = zero linhas gravadas = **a versão vigente permanece** (rollback implícito). O teste `iql_weights_sanity` é o monitor que avisa quando isso acontece.

`full_refresh=false` nos dois modelos incrementais protege a trilha de auditoria — rollback exige DDL manual, com runbook no README do diretório.

Nomenclatura: modelos, colunas, CTEs e documentação em **inglês** (RDA-0005); **valores de dado em português** (`membro_ativo`, `sem_resposta`…), porque o de-para casa com o texto literal das respostas do formulário (D49/D50).

## 6. Estado e próximos passos

| Fase | Estado |
|---|---|
| **1. Config e score** | ✅ jul/2026 |
| **2. Calibração** | ✅ jul/2026 — v0.3, backtest out-of-campaign validado |
| **3. Dashboard** | ✅ jul/2026 — `qualificacao-leads/iql/` no portal |
| **4. Modelo no dbt** | ✅ jul/2026 — MR !2426, pesos vivos (D39), 4 revisões independentes aplicadas, 25/25 testes |
| **5. Piloto ELB26** | 🔲 em curso — leitura D+60 (~set/2026), gate = Spearman(CPLq, CAC) > Spearman(CPL, CAC) |
| **6. Fechamento do piloto** | 🔲 hit-rate Spearman, leaderboard IV, go/no-go CAPI |
| **7. CAPI v2** | 🔲 evento server-side com valor por faixa (EV já disponível em `vl_reference_ev`); `id_fbclid` capturado em 81,9% dos cadastros 2026 |
| **8. 1º refit** | 🔲 ~mar/2027, quando o EVG maturar |

**Critérios de sucesso do piloto** (meta verificável):
1. Ordenamento monotônico por faixa dentro da campanha;
2. Time de mídia toma ≥1 decisão de realocação usando a matriz CPL×IQL e a registra;
3. Spearman(CPLq, CAC real) por adset > Spearman(CPL, CAC real) — o IQL precisa prever o CAC melhor que o CPL, senão não paga a complexidade.

**Agenda do 1º refit:** revalidar os β; reavaliar a quarentena de `regiao_ddd`, `idade` e `ocupacao`; threshold de uniformidade de exposição (2,0); simplificações de binning já medidas (`renda_declarada` 5→3 níveis, `status_cadastro` 4→3, `tempo_conhece` 4→3); decidir sobre `religiao` (IV 0,015) e revisitar a D14; re-medir os múltiplos D28/D31 nas 5 faixas; avaliar **trava de maturidade por regime** (D50 — a janela curta preserva o ordenamento dentro do NM, mas inverte no `status_cadastro`).

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
| D50 | 31/jul | **Nomenclatura e documentação 100% em inglês (2ª rodada do review do Victor).** Ele apontou que a padronização RDA-0005 ficou pela metade: os *nomes de modelo* seguiam em português. Renomeados 6 modelos + 2 testes + 1 campo: `int_iql_lead_niveis`→`int_iql_lead_levels`, `int_iql_woe_vivo`→`int_iql_woe_live`, `fct_iql_pesos`→`fct_iql_weights`, `fct_lead_iql_historico`→`fct_lead_iql_history`, `dim_iql_de_para`→`dim_iql_mapping`, `dim_iql_ddd_regiao`→`dim_iql_ddd_region`, `iql_niveis_sem_peso`→`iql_missing_weight_levels`, `iql_pesos_sanidade`→`iql_weights_sanity`, `cd_versao_bloqueada`→`cd_blocked_version`. Decisão do André estendeu o escopo para **toda nomenclatura e documentação por padrão**: também foram traduzidos os nomes de CTE e variáveis jinja, todos os comentários de SQL, os headers de modelo, as descrições do `_iql_models.yml`, a docstring do macro e o README do diretório. **Os VALORES de dado permanecem em português** (`membro_ativo`, `sem_resposta`, `status_cadastro`…) — são conteúdo, não identificador, e o de-para, os `accepted_values` e esta metodologia os referenciam literalmente; traduzi-los exigiria migrar dado, não só código. Rename feito com `git mv` + substituição restrita ao escopo IQL (o `sed` amplo em `models/` foi o que causou o incidente do TSE na D49). Consumidor externo atualizado: `iql/refresh.py` aponta para `fct_iql_weights`. Tabelas antigas dropadas do `bp-staging.dbt_abe`. Validado: 25/25 testes, lint 3.4.0 limpo, distribuição idêntica à pré-rename (A+ 1,5% / acumulado A 16,4%) e ordenamento monotônico 3,63%→0,32%. ⚠️ **Defeito pré-existente registrado, não corrigido**: as seções 4 e 5 deste documento ainda descrevem a arquitetura anterior à D38/D39 (seeds CSV, `int_iql_survey_normalizada`, `mart_iql_midia`, `iql_recalibra.py` gerando pontos) — idem `iql/metodologia.html`. Precisa de reescrita à parte | vigente |
| D49 | 31/jul | **Review do Victor aplicado + alinhamento ao RDA-0005.** (1) **`idade` e `ocupacao` em quarentena (β 0)** — ponto substantivo do review: estavam ativos com β 0,34/0,37 mas **sem nenhuma linha no de-para** (o formulário não coleta), então todo lead caía em `sem_resposta` e eles só injetavam offset constante, sem poder discriminativo. Mesma lógica que já quarentenava o `regiao_ddd` — eu deveria ter pego sozinho. (2) **Os 5 modelos de config `seed_*` viraram `dim_*`**: `seed` não é categoria sancionada do repo (`stg_/base_/int_/fct_/dim_/dtm_/cbo_/obt_`) e é *resource type* reservado do dbt (CSV via `dbt seed`), então o prefixo sugeria algo que o modelo não é. (3) **Colunas alinhadas ao RDA-0005** (tabela oficial de 15 prefixos, agora espelhada em `wiki-bp/pages/nomenclatura-campos.md`): `sg_uf`→`cd_uf` (`sg_` não existe na tabela), `nr_registration`→`qt_registration` e `nr_precedence`→`qt_precedence` (`nr_` não existe; `qt_` é o único slot para inteiro), `qt_days_since_previous_registration`→`qt_days_last_registration` (35→25 chars, respeitando o limite de 30 e removendo a preposição). **`tx_rule` foi mantido** — o review supôs que devia virar `nm_`, mas `tx_` É oficial ("Texto. Ex: tx_description"). (4) **Padrão de CTE**: `ref()` puro no CTE-topo e filtro no CTE seguinte, em `fct_lead_iql`, nos 2 testes e também no `fct_lead_iql_historico` (mesmo caso, não citado no review). (5) **Headers enxutos**: Business Goal de 1 linha + ponteiro para esta metodologia nos 11 modelos; IDs de decisão saíram também das descrições do yml. (6) **Cortes v3** — a quarentena removeu o offset constante de idade/ocupacao e deslocou a escala (A+ saltou de 1,6% para 3,0%); rederivados por evento de safra com histerese ±2: **A+ 9→12** (Δ3) e **B −24→−21** (Δ3) atualizados, **A −4** (Δ2) e **C −28** (Δ1) mantidos. Distribuição volta ao alvo: A+ 1,5% (alvo 1,5%), acumulado A 16,5% (alvo 15%). Nota de contexto: o limite de 30 chars já é violado em produção por outro time (`obt_kafka__view_sessions.qt_days_since_previous_view_session`, 35) — corrigimos o nosso mesmo assim | vigente |
| D48 | 29/jul | **`confianca_midia` promovido a atributo ativo + cortes v2 + `motivacao` em coleta.** (1) A `midia_tradicional` estava em **coleta valendo zero** com **IV 0,328 em não-membro — a segunda mais forte do formulário** (gradiente 1,5% / 0,9% / 0,2% / 0,1%, 15× do topo ao fundo). Vira atributo `confianca_midia` com **3 níveis**: `busca_alternativas` / `desconfia` / `nao_incomodado` — "Não penso muito nisso" e "Acho que está tudo certo" colapsam porque o segundo tinha **19 conversões** (mesmo critério que colapsou a renda 15k+; e o oposto do `bp_informal`, que tem 366 e foi mantido — o critério é **contagem de conversões**, não share de população). Pontos: **+5 / −4 / −17**. (2) **β = 0,42**, e aqui há uma ressalva de método: a regressão conjunta em BQML (108k respondentes) deu **0,4547**, e o número adotado é um ponto escolhido dentro do intervalo medido 0,40–0,46 — tecnicamente contra a D4 ("ninguém escolhe peso na mão"), aceito porque **medimos que a escolha nessa faixa é imaterial**: conversão por faixa idêntica na terceira decimal entre β 0,40 e 0,45, só 2,11% dos leads trocam de faixa (e entre faixas vizinhas). Lição generalizável: **o WOE carrega a forma, o β só escala** — erro de ±15% no β não muda ordenação; o que mata um atributo é sinal invertido (caso `regiao_ddd`), não imprecisão de magnitude. (3) **Confundimento de campanha detectado e corrigido no meio do caminho**: o primeiro ajuste deu β 0,395, mas o nível `sem_resposta` era **marcador de campanha** (66% da EVG, 0% da ELB26 — e a EVG converte mais), então o WOE dele media "ser da EVG". Refazendo só com quem respondeu: β 0,4547 e o conjunto todo se moveu 15–20%. Por isso o `sem_resposta` entra **neutro (WOE 0,0)** em vez do valor medido. Corolário: a "validação" de que renda (0,6196) e afinidade (0,3705) reproduziam o seed era **coincidência do ajuste contaminado** — no limpo dão 0,511 e 0,442. (4) **Estabilidade verificada**: a ordenação dos 3 níveis se mantém em BP10, ELB26 e EVG; magnitudes variam 2–3× (o pooling absorve), **sem inversão de sinal**. (5) **Cortes rederivados (v2)** por evento de safra, com histerese ±2pts: **A+ 6→9** (Δ3) · **A −7→−4** (Δ3) · **C −32→−28** (Δ4) · **B mantido em −24** (Δ1, dentro da banda). Distribuição resultante nos NM in-funnel bate o alvo (A+ 1,6% vs 1,5%; acumulado A 15,3% vs 15%; C 85,3% vs 85%) e o ordenamento intra-campanha melhorou (BP10 A+ vs D = **21×**; EVG 7,9×). (6) **`motivacao` entra em coleta** (10 linhas no de-para, textos por campanha → níveis canônicos compartilhados; vale 0 ponto até o IV comprovar). (7) Os outros 6 β **não** foram atualizados: movem-se 15–20% entre especificações e a população do ajuste é estreita (só respondentes, safras 2026 imaturas). Isso aceita **dupla contagem parcial** com `tempo_conhece` (correlação 0,41 com o atributo novo) — limitação registrada, não acidente. Fila do 1º refit: revalidar todos os β juntos, com safra madura e exposição uniforme | vigente |
| D46 | 28/jul | **`paga_conteudo` vira binário — nível `bp_informal` colapsado em `paga_algum`**. A pergunta antiga `streaming` (multi-select) passa a mapear como a `assina_streaming` (ELB26+): qualquer plataforma marcada (incl. "Brasil Paralelo") → `paga_algum` (prec 3), "Nenhum" → `nao_paga` (prec 1). Motivação: IV da ELB26 validou a variante binária (0,11 entre respondentes, vs 0,03/0,23 da multi) e o atributo agora poola WOE entre campanhas antigas e novas com os mesmos níveis. Efeito: leads antigos com resposta "Brasil Paralelo" perdem a diferença de prior (0,912→0,5472 de WOE) — deltas registrados no `fct_lead_iql_historico`. Mudanças: `seed_iql_de_para` (dbt + csv do protótipo), prior `bp_informal` removido do `seed_iql_woe_bootstrap`, descrições no yml. Sem refit de β (mesmo atributo). Versões antigas do `fct_iql_pesos` mantêm a linha `bp_informal` como trilha de auditoria | vigente |
| D45 | 27/jul | **ELB26 no dashboard + visão por campanha Meta + métrica "página de obrigado"**. (1) ELB26 nas tags do dashboard; para isso o protótipo foi atualizado uma última vez (fonte de `tb_iql_woe_respostas`/`tb_iql_iv_perguntas`): de-para ganhou `assina_streaming` (Sim→paga_algum/Não→nao_paga, espelho do seed dbt) e o `01_tb_lead_iql.sql` ganhou o join da variante binária. (2) **Resultado por campanha Meta**: agregado por `nm_campaign_name` (cada campanha = otimização/estratégia em teste) — piso de 50 leads no agregado, não por anúncio; expôs [QUENTE] Lista Toda Base (IQL 42,8%, CPLq 4,91) vs [ADVANTAGE] Brasil Exclusão Insider (IQL 7,2%, CPLq 26,71). (3) Tabelas de anúncio ganharam sublinha campanha·ad set (mesmo criativo muda de resultado por público — caso AD32) e colunas CPL e RPL projetado. (4) **Compra na página de obrigado = transação ≤30min do cadastro** — corte medido na distribuição cadastro→compra (bimodal: cluster imediato ≤30min, vale 30min–2h; BP10: 388 vs 43 vendas). Referências: ELB26 62,6% das vendas atuais / EVG 46,7% / BP10 32,9%; por lead: 0,87% EVG vs 0,43% BP10 (diferença de oferta/página) | vigente |
| D44 | 27/jul | **Cutover antecipado do dashboard para o modelo v1 (pré-merge)**: o `refresh.py` deixou de ler o protótipo `tb_lead_iql` (v0.2, 3 faixas) e passou a ler `fct_lead_iql`/`fct_iql_pesos` em `bp-staging.dbt_abe` — constante `DATASET` única; no cutover pós-merge troca-se 1 linha para `bp-datawarehouse.datamart`. UI passou a exibir as **5 faixas (A+/A/B/C/D)**; "qualificado" (IQL, CPLq) = A+∪A (preserva a semântica v0.2: A ≈ ≥2× conversão base); para múltiplos D28 e forecast D31 (medidos em 3 faixas): A+∪A→nm_a, B→nm_b, C∪D→nm_c (re-medir por 5 faixas no 1º refit). Impacto ganhou os 10 atributos do macro (`renda_declarada`, `idade`, `ocupacao` incluídos); `status_pessoa` saiu (D41). ⚠️ Pré-merge o fct não atualiza sozinho: rodar `dbt run --select models/marts/marketing/iql --target local --defer --state manifest --favor-state` antes do refresh (aviso no header do refresh.py). Motivação: pergunta do André ("por que A/B/C se o modelo tem A+…D?") + piloto ELB26 rodando no modelo que vai a prod. O protótipo segue existindo só como fonte de `tb_iql_woe_respostas`/`tb_iql_iv_perguntas` (agregados de pesquisa) até o mart_iql_iv | vigente |
| D43 | 27/jul | **Persona "Fantasma" (2ª anti-persona) na aba Personas**: `nivel_respondeu='nao' AND historico != recadastro_quente` — não respondeu nada e sem histórico, entra na cascata depois do Curioso Frio (que, por definição, **respondeu** — declarou primeiro_contato/nunca_ouviu). Medição EVG+BP10: Fantasma é ~30% da base NM nas duas campanhas, conv 0,45%/0,08% (≈1,5× abaixo do Curioso Frio); no BP10 concentra o tráfego pmax (14,5k leads, conv 0,007%). Ação de mídia distinta: Curioso Frio = gancho genérico demais (mensagem); Fantasma = canal/segmentação ruim (compra). Neutro residual cai para 11–33% e passa a converter acima da média da base. Cor violeta `#9085e9` (validada 6-checks no surface). Reincidentes silenciosos (recadastro_quente sem resposta) permanecem no Neutro — promover a persona própria é candidato futuro | vigente |
| D42 | 27/jul | **Persona "Reencontrado" removida da aba Personas** (decisão do André): membro oculto tem/teve assinatura sob outro e-mail — reconexão, não aquisição — logo não pertence à base de "Não Membros" que a aba descreve para o time de marketing. O corte é no **denominador**: `refresh.py` exclui `nivel_status_pessoa='membro_oculto'` da base de personas (queries `icps` e `perfil_anuncios`) e o JS recomputa fatias/lift das contagens cruas. Restam 4 perfis (Simpatizante Maduro, Pagante de Conteúdo, Curioso Frio, Neutros) + nota explicativa na aba. Coerente com a D41 (membro_oculto descontinuado no modelo dbt); o protótipo `tb_lead_iql` ainda expõe a coluna, usada aqui só para exclusão. No cutover pós-merge, revisar as queries do refresh.py que dependem dela | vigente |
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
| "Como funciona numa campanha nova?" | Pontua desde o dia 1 com o scorecard vigente (atributos são da pessoa, não da campanha; status+histórico cobrem 100% dos leads). Pesos ficam congelados durante a campanha (comparabilidade entre anúncios + auditoria via `cd_scorecard_version`) e o sistema reaprende **sozinho** entre campanhas: quando uma cohort matura, ela entra no treino, o pipeline recalcula o WOE e grava uma versão nova — sem script e sem MR (D39). Pergunta nova entra em modo coleta e é promovida se provar IV. Aprendizado em lote versionado, não online — recalibrar no meio com as primeiras conversões enviesaria o score para o comprador rápido (NM típico demora ~14 meses). |
