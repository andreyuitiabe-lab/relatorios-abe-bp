# Bibliografia comentada — saturação, mCAC e decisão diária de budget

**Data:** 2026-07-23
**Origem:** 3 rodadas de pesquisa (curvas/MMM · alocação/bandits · curvas variantes no tempo), consolidadas e ranqueadas pela relevância ao nosso problema — não pela fama do paper.
**Complementa:** seção 2 do [PROPOSTA.md](PROPOSTA.md).

Organização: por tese, não por tema. Cada referência diz o que resolve *aqui*.

---

## Tese 1 — O racional marginal é clássico e está certo; não é o gargalo

| Referência | O que resolve aqui |
|---|---|
| **Dorfman & Steiner (1954)** — [teorema](https://en.wikipedia.org/wiki/Dorfman%E2%80%93Steiner_theorem) | A regra "gastar até mCAC = teto" é o caso discreto do teorema clássico de publicidade ótima. Sanity check importante: o teto (R$180) deve derivar da **margem**, não de convenção do time. |
| **Simon & Arndt (1980), "The Shape of the Advertising Response Function"** (*JAR* 20:11-28; contexto em [Vakratsas et al. 2004](https://dl.acm.org/doi/abs/10.5555/2882794.2882803)) | Meta-análise de ~100 estudos: resposta é **côncava** (retornos decrescentes desde o 1º dólar), não S-shape. Consequência: mCAC monotônico crescente → a regra do teto tem solução única e interior. Encerra o debate de forma funcional — não gastar mais tempo testando formas. |
| **Gufeng Zhou (Robyn) — convergência do marginal ROAS** — [Medium](https://medium.com/@gufengzhou/the-convergence-of-marginal-roas-in-the-budget-allocation-in-robyn-5d407aebf021) | No ótimo, o mROAS equaliza entre campanhas — a mesma lógica do water-filling já implementado em `mmm_project/src/bidding/optimize.py`. Confirma o desenho. |
| **Recast — Average vs marginal ROI** — [getrecast.com](https://getrecast.com/average-vs-marginal-roi-in-mmm-when-to-use-each-and-why-both-matter-for-your-budget/) | O argumento canônico de por que CAC *médio* engana: fica plano enquanto o marginal explode. Bom material pra apresentar ao time de tráfego. |

## Tese 2 — "A curva muda todo dia" se resolve por decomposição, não por modelo dinâmico

| Referência | O que resolve aqui |
|---|---|
| **Ng, Wang, Dai (Uber, AdKDD 2021) — Bayesian Time Varying Coefficient Model** — [arXiv:2106.03322](https://arxiv.org/abs/2106.03322) | Formaliza coeficientes que evoluem suavemente (kernel smoothing, não random walk — que persegue ruído em dado diário). É o paper por trás do Orbit KTR. Referência caso a decomposição simples não baste. |
| **PyMC-Marketing — MMM com TVP** — [notebook](https://www.pymc-marketing.io/en/stable/notebooks/mmm/mmm_tvp_example.html) + [blog PyMC Labs](https://www.pymc-labs.com/blog-posts/modelling-changes-marketing-effectiveness-over-time) | Estruturalmente idêntico ao nosso `demand_t × f(spend_t)`: saturação (Hill) fixa, GP temporal como multiplicador. Tem variante GP global (mercado) + GP por canal — separa "demanda subiu" de "este canal degradou". Caminho de implementação mais direto se formalizarmos a decomposição; já usamos PyMC. |
| **Recast — non-marketing baseline** — [getrecast.com](https://getrecast.com/non-marketing-baseline-mmm-exogenous-factors/) | Posição de praticantes: baseline temporal flexível absorve demanda orgânica em vez de controlar variável a variável. É a versão "engineering" do nosso `demand_index`. |
| **LiftLab — Auction Dynamics vs Consumer Response (two-stage)** — [liftlab.com](https://liftlab.com/blog/auction-dynamics-vs-consumer-response-mmm/) | **Refinamento novo e acionável:** decompõe a curva em spend→impressões (leilão/CPM, volátil diário) e impressões→vendas (consumidor, mais estável). Muito do "a curva mudou" é CPM. Sugere ajustar `f` em spend deflacionado por CPM — melhoria barata na Etapa 3 do bidding pipeline (temos `qt_impressions` no datamart). |
| **Little (1979), "Aggregate Advertising Models: The State of the Art"** (*Oper. Res.* 27:629-667; survey em [Naik](https://prasadnaik.faculty.ucdavis.edu/wp-content/uploads/sites/422/2016/11/tsm2008.pdf)) | Resposta que muda no tempo é fato estilizado desde 1979 (wear-out, cópia, mídia) — não artefato do Meta. Calibra expectativa: nenhum modelo vai "fixar" a curva. |

## Tese 3 — O gargalo é identificação: sem variação exógena, a curva "limpa" não existe

| Referência | O que resolve aqui |
|---|---|
| **Dew, Padilla, Shchetkina (2024) — "Your MMM is Broken: Identification of Nonlinear and Time-varying Effects"** — [arXiv:2408.07678](https://arxiv.org/abs/2408.07678) | **A referência mais importante da bibliografia.** Prova que saturação e efeito time-varying **não são separáveis** só com dado observacional quando o spend é autocorrelacionado — "curva que desloca" e "curva estável mal estimada" são observacionalmente equivalentes. Implicação: os micro-experimentos de budget (Fase 3) não são melhoria opcional, são condição de identificabilidade. |
| **Nuara et al. — Online Joint Bid/Daily Budget Optimization** — [arXiv:2003.01452](https://arxiv.org/pdf/2003.01452) | O único desenho em produção (>1 ano) onde a exploração de budget **é** a fonte de identificação: GP por campanha + knapsack diário + variação deliberada. Formaliza a Fase 3. |
| **Blake, Nosko & Tadelis (2015)** — experimento eBay/search ads | O memento mori: quase todo o "retorno" medido observacionalmente era venda que aconteceria de qualquer forma. Manter em mente a cada R² convincente. |
| **Lewis & Rao (2015), "The Unfavorable Economics of Measuring the Returns to Advertising"** (*QJE*) | Mesmo **experimentos** de ads têm poder estatístico baixo em janelas curtas. Tradução: esperar medir **direção** do mCAC em 3 dias, nunca magnitude precisa. Calibra o que prometer ao time. |
| **Meta — Divergent Delivery** — [arXiv:2508.21251](https://arxiv.org/pdf/2508.21251) | Mudar budget muda a audiência que o Advantage+ entrega — a curva se move quando você mexe nela. Explica mecanicamente a aderência 0.42 das nossas curvas. |
| **Jin et al. (2017) — Bayesian MMM with Carryover and Shape Effects** — [Google Research](https://research.google/pubs/bayesian-methods-for-media-mix-modeling-with-carryover-and-shape-effects/) | Canônico de Hill+adstock conjuntos. Achado aplicável: com pouca amostra o posterior é dominado pelo prior → pooling hierárquico campanha→conta em vez de curva isolada (Fase 2). Ver também o [geo-hierárquico](https://research.google/pubs/geo-level-bayesian-hierarchical-media-mix-modeling/) dos mesmos grupos. |

## Tese 4 — A decisão diária é política de controle, não previsão

| Referência | O que resolve aqui |
|---|---|
| **Little (1970), "Models and Managers: The Concept of a Decision Calculus"** (*Mgmt Sci*) | O critério de sucesso do sistema: simples, robusto, controlável, adaptativo — um modelo que o gestor não entende nem confia não muda decisão. Argumento estrutural a favor da Abordagem C sobre o stack bayesiano como interface. |
| **Gigli & Stella (2024) — MAB for performance marketing** — [Springer](https://link.springer.com/article/10.1007/s41060-023-00493-7) | O "paper Springer 2024" do ANALISE.md, identificado. Bandit paramétrico + bootstrapped TS pra poucas conversões e mercado rápido. Lição aproveitável sem a maquinaria: impor estrutura (curva) compensa escassez de dado. |
| **Discounted Thompson Sampling** — [arXiv:2305.10718](https://arxiv.org/abs/2305.10718) | TS com desconto temporal: half-life ~5-7d é a formalização do instinto "confiar mais no CPA_3d que no acumulado". Evolução opcional (Fase 4), não requisito. |
| **Vernade et al. (2017) — Bandits com delayed conversions** — [arXiv:1706.09186](https://arxiv.org/abs/1706.09186) + modelo de delay de Chapelle | A correção de maturação do CPA_3d: estimar distribuição do delay e inflar conversões recentes. Corrige o viés estrutural da Abordagem C pós-escalada. |
| **Adams & MacKay — BOCPD** (+ aplicação a ads: [arXiv:2509.09758](https://arxiv.org/abs/2509.09758)) | Se formalizarmos a Abordagem C: probabilidade de mudança de regime com controle de falso alarme. Upgrade opcional. |
| **Meta — learning phase / significant edits** — [Help Center](https://www.facebook.com/business/help/112167992830700) + consenso practitioner | ≤20%/dia não reseta learning; >~30% sim; avaliar só com ≥48h. Valida o step-limit e adiciona a regra de lag. |
| **Budget pacing** — [arXiv:2503.06942](https://arxiv.org/abs/2503.06942) | Por que a resposta a budget não é instantânea (throttling/PID intradiário) — fundamenta as 48h. |
| **Mutt Data — Daily Budget Optimization × marginal ROAS** — [blog](https://blog.muttdata.ai/post/2025-07-02-Daily-Optimizations) | O setup mais próximo do nosso: reotimização diária contra curvas marginais, quantificando o ganho vs alocação estática. |

## Tese 5 — Fadiga de criativo é fenômeno próprio, com meia-vida curta

| Referência | O que resolve aqui |
|---|---|
| **Path Signature Framework for Creative Fatigue (2025)** — [arXiv:2509.09758](https://arxiv.org/pdf/2509.09758) | CTR sozinho não distingue fadiga vs leilão vs re-otimização. Detecção formal de wear-out — complementa o filtro da Etapa 1 do bidding pipeline. |
| **Atria — Meta creative fatigue 2026** — [tryatria.com](https://www.tryatria.com/blog/meta-creative-fatigue-diagnose-and-fix-2026) | Practitioner: criativos decaem em ~10 dias hoje (vs ~6 semanas em 2023). Meia-vida de curva por *criativo* é de dias → estimar curva no nível campanha e deixar o multiplicador diário absorver o resto. |

## Tese 6 — Como medir o mCAC nos saltos naturais (rodada 4, 23/jul)

O ferramental metodológico do event-study pooling dos 316 saltos:

| Referência | O que resolve aqui |
|---|---|
| **Hartmann, Nair & Narayanan (2011) — RDD para marketing-mix** — [Stanford GSB](https://www.gsb.stanford.edu/faculty-research/publications/identifying-causal-marketing-mix-effects-using-regression) | O fundamento do desenho: descontinuidades geradas pelas *heurísticas da própria firma* (regras de decisão diária dos gestores) identificam o efeito **marginal local** — exatamente o que os saltos de budget são. |
| **Callaway & Sant'Anna (2021) — DiD com múltiplos períodos** — [arXiv:1803.09015](https://arxiv.org/abs/1803.09015) | O estimador padrão pro pooling: 316 saltos são "adoções escalonadas" (staggered). Usa como controle as campanhas do mesmo dia sem mudança — absorve o choque de demanda comum — e permite matching em tendência pré-salto, atacando a endogeneidade "escalar no calor" que detectamos no teste. |
| **Brodersen et al. (2015) — CausalImpact** — [paper](https://projecteuclid.org/journals/annals-of-applied-statistics/volume-9/issue-1/Inferring-causal-impact-using-Bayesian-structural-time-series-models/10.1214/14-AOAS788.full) / [pacote](https://google.github.io/CausalImpact/CausalImpact.html) | Estimador por-evento antes do pooling: contrafactual sintético de campanhas estáveis do mesmo dia, com incerteza bayesiana. Ferramenta pronta em R/Python. |
| **GeoLift / Augmented Synthetic Control — sensibilidade** — [arXiv:2301.07656](https://arxiv.org/abs/2301.07656) | O núcleo do synthetic control transfere pra nível campanha (donor pool = campanhas sem mudança). Documenta a ameaça principal: campanhas da mesma conta compartilham leilão (spillover). |
| **Hahn & Hyun (1991) — pulsing ótimo** + **Dubé, Hitsch & Manchanda (2005)** — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=478050) | A justificativa teórica de que saltos ≥±25% são informativos: pulsing gera variação de alta frequência que identifica a curvatura local da resposta. |
| **Gordon, Moakler & Zettelmeyer (2023) — "Close Enough?"** — [arXiv:2201.07055](https://arxiv.org/abs/2201.07055) | **O alerta calibrado sobre o teto do método:** 663 experimentos no Facebook; nem DML nem matching com 5.000+ features recuperam o efeito experimental — o delivery algorítmico cria seleção quase indesfazível. Tratar o pooling como **direcional** e validar periodicamente com lift test. |

## Tese 7 — Regime de lançamento (LAN) tem literatura própria

| Referência | O que resolve aqui |
|---|---|
| **Horsky & Simon (1983) — Advertising and the Diffusion of New Products** — [INFORMS](https://pubsonline.informs.org/doi/10.1287/mksc.2.1.1) | Modelo canônico de lançamento: ads informam inovadores, boca-a-boca converte imitadores, e a política ótima de investimento é **decrescente no tempo**. Fundamenta teoricamente por que LAN satura (esgotamento do pool de adotantes) e por que a curva histórica não vale no ramp. |
| **Simon (1982) — ADPULS: wearout e pulsation** (JMR) + [Naik OR 2015 sobre memória em pulsing](https://prasadnaik.faculty.ucdavis.edu/wp-content/uploads/sites/422/2016/11/OR2015.pdf) | Formaliza wear-in (resposta reage a **incrementos** de pressão, não só ao nível) e wear-out. Forma funcional candidata pras 3-6 semanas de LAN: efeito diferencial positivo no ramp, decaimento após o pico. Racionaliza por que a Abordagem C (que olha *mudança* recente) funciona em LAN. |

Sobre learning phase/reset: não há paper acadêmico sólido — a fonte é a própria documentação da Meta. Citar como restrição operacional, não literatura.

## Tese 8 — Priors externos de elasticidade (calibrar expectativa e curvas)

| Referência | O que resolve aqui |
|---|---|
| **Sethuraman, Tellis & Briesch (2011) — meta-análise de 872 elasticidades** — [PDF](https://gwern.net/doc/economics/advertising/2011-sethuraman.pdf) | Elasticidade média de curto prazo **0,12** (longo prazo 0,24; só 53% significativas). Prior externo: dobrar spend ≈ +8-9% vendas na margem — resposta fortemente côncava. Usável como prior do expoente da lei de potência / inclinação da Hill. |
| **Shapiro, Hitsch & Tuchman (2021, Econometrica) — 288 marcas de TV** — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3273476) | Elasticidades medianas ~0,01-0,02 e **ROI marginal negativo pra >80% das marcas** — a maioria sobre-investe. É TV/marca (limite inferior pro nosso direct response), mas o padrão "a maioria está além do ótimo" bate com nossos 122 "reduzir" pós-desconfundimento. |
| **Gordon, Zettelmeyer et al. (2019) — 15 lift studies no Facebook** — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3033144) | Atribuição observacional erra o lift experimental por fatores de **até 3×, pros dois lados**. Benchmark de quanto desconfiar do CAC de atribuição ao calibrar o teto — reforça validar R$180 contra margem, não contra atribuição. |
| Benchmark "quanto o mROAS cai ao dobrar spend em social" | **Não existe público e confiável** — precisa ser derivado das nossas curvas + priors acima (via arcabouço de Jin et al. 2017). Não procurar mais. |

---

## Leitura mínima recomendada (se for ler 4)

1. **Dew et al. 2024** — por que a curva "limpa" exige variação exógena (muda a prioridade das fases)
2. **LiftLab two-stage** — refinamento CPM barato e imediato
3. **Little 1970** — o critério pra qualquer coisa que o gestor vá usar
4. **Lewis & Rao 2015** — calibra o que é possível prometer

## Implicações não incorporadas ainda ao PROPOSTA.md

1. ~~**Ajuste por CPM (LiftLab)**~~ — **testado e descartado (23/jul/2026)**. Nos nossos dados
   (204 dias, 258 campanhas VENDA): só **5%** da var(log CAC) vem do CPM (95% é resposta do
   consumidor); elasticidade CPM×spend within-campanha ≈ 0 (Advantage+ absorve escala sem
   encarecer o leilão); e o power fit sobre spend vence o fit sobre impressões em **14 de 16**
   campanhas (R² 0,674 vs 0,550). Shares negativos nas PPT grandes indicam que CPM caro
   correlaciona com conversão melhor — ajustar por CPM removeria sinal. A tese two-stage vale
   pra leilões voláteis (search/B2B competitivo), não pro nosso caso. Reforça que a fonte da
   "curva que muda" é demanda/conversão → `demand_index` é o ajuste certo.
2. **Dew et al. / inversão Fase 2 ↔ Fase 3 — testado e confirmado, com diagnóstico corrigido (23/jul/2026).**
   Teste em 43 campanhas ≥20 dias (`scripts/identification_test.py`):
   - Autocorrelação lag-1 do spend within-campanha é **baixa** (mediana 0,36; só 9% >0,8) — a
     condição de pior caso de Dew não vale forte aqui; **variação existe** (12,7% dos
     campanha-dias são saltos ≥±25% sobre base estável = 316 quasi-experimentos naturais).
   - Mas a curva **falha evento a evento**: concordância de direção vs teto = 58% contra 60%
     do chute majoritário; Spearman 0,14. Só o *nível agregado* é calibrado (mediana R$202
     curva vs R$206 medido).
   - Diagnóstico: o gargalo não é falta de variação, é variação **suja** (endogeneidade
     "escalar no calor" — ratio salto/curva p25=0,61) + ruído (Lewis & Rao). Conclusão dupla:
     (a) não polir curvas com camada bayesiana; (b) **pooling dos 316 saltos naturais**
     (event-study por segmento PPT/LAN × faixa de gasto) antes de experimentos deliberados.
3. **Teto derivado de margem (Dorfman-Steiner):** validar se R$180 veio de margem/LTV ou de convenção — conecta com `scripts/08_ltv` do mmm_project, já apontado lá como pendência.
