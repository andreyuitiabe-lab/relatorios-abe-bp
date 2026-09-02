# Bibliografia comentada — associar relevância de marca a vendas

Referências que sustentam (ou limitam) o que fizemos em `ANALISE.md`. Formato do repo: cada
entrada diz **o que resolve aqui**, não o que o paper diz em geral. Compilado em 25/08/2026.

---

## Tese 1 — A pergunta de fundo: marca move vendas, e por dois caminhos

| Referência | O que resolve aqui |
|---|---|
| **Binet & Field (2013), _The Long and the Short of It_** — [IPA](https://ipa.co.uk/knowledge/publications-reports/the-long-and-the-short-of-it) | A base da hipótese que o time levantou: brand building eleva a **eficiência da ativação**, não só o volume. É exatamente o mecanismo que testamos como "resistência menor" (conversão por sessão, CAC a spend constante). Fundamenta *por que* olhar eficiência e não só volume. |
| **Sharp, _How Brands Grow_** — mental availability | Dá o vocabulário para o resultado invertido da rodada 1: relevância aumenta a chance de a marca ser lembrada *por quem já a conhece*. Coerente com o efeito existir em membro morno e ser nulo em freemium. |
| **Cain / Marketscience — brand equity em MMM** — [artigo](https://market.science/measuring-brand-equity-and-long-term-marketing-effects/) · [PDF](https://www.market.science/wp-content/uploads/Marketing-Mix-Modelling-and-Return-on-Investment.pdf) | **A referência mais próxima do que queremos fazer.** Marca entra no MMM por dois componentes: eleva o *baseline* (longo prazo) e melhora a *eficiência da ativação* (curto prazo). Recomenda **não** jogar métrica de marca direto na equação de vendas — usa Unobserved Components para separar o componente estrutural lento do ruído de curto prazo. É o caminho de evolução natural da nossa análise diária. |
| **Artefact — brand e efeito de longo prazo em MMM** — [blog](https://www.artefact.com/blog/demystifying-brand-and-long-term-effect-measurement-in-marketing-mix-modelling-2/) | Versão praticante do acima; útil para explicar ao time por que otimizar por ROAS de curto prazo subestima marca. |

## Tese 2 — Medir atenção com rastro digital (nowcasting)

| Referência | O que resolve aqui |
|---|---|
| **Choi & Varian (2012), _Predicting the Present with Google Trends_** (*Economic Record*) — [PDF](https://people.ischool.berkeley.edu/~hal/Papers/2011/ptp.pdf) · [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1659302) | O paper fundador do uso de busca como indicador **coincidente** (nowcasting), não preditivo. É a justificativa metodológica para tratar nosso índice como termômetro do dia — e o alerta de que "prever o presente" é um resultado mais modesto do que "prever o futuro". Varian revisitou em [_Nowcasting with Google Trends_ (2023)](https://onlinelibrary.wiley.com/doi/10.1111/1475-4932.12783). |
| **Moat, Curme, Preis et al. (2013), _Quantifying Wikipedia Usage Patterns Before Stock Market Moves_** (*Scientific Reports*) — [Nature](https://www.nature.com/articles/srep01801) · [PDF](https://wrap.warwick.ac.uk/id/eprint/54525/1/WRAP_Moat_srep01801.pdf) | **A referência que legitima a Wikipedia como fonte** (rodada 4). Estabelece pageviews de Wikipedia como traço mensurável da *fase de coleta de informação* antes da decisão. É precisamente o que queremos capturar: alguém que ouviu falar da BP e foi checar o que é. |
| **Wikipedia pageviews como indicador de atenção — Nasdaq** — [Wiley/ISAF](https://onlinelibrary.wiley.com/doi/full/10.1002/isaf.1508) | Replicação posterior; confirma que o sinal é de **atenção**, com poder modesto e ruidoso — bate com nosso volume baixo (mediana 96 views/dia) e a recomendação de ler em média móvel. |
| **Nowcasting de turismo com atenção da Wikipedia (2026)** — [MDPI](https://www.mdpi.com/2673-5768/7/4/113) | Uso recente fora de finanças: pageviews como proxy aberto e interpretável de demanda por informação. O paralelo mais próximo de aplicação comercial que encontrei. |
| **See-To & Ngai (2018), nowcasting de vendas com dados online** (*Annals of OR*) — [Springer](https://link.springer.com/article/10.1007/s10479-016-2296-z) | Nowcasting de **vendas** (não de bolsa) a partir de rastro digital. Útil como precedente de método, ainda que a fonte seja reviews. |

⚠️ **Lacuna real:** não existe referência publicada de "Wikipedia pageviews → vendas de assinatura".
O uso consolidado é finanças e turismo. Nossa aplicação é uma extensão razoável, mas **inédita
o suficiente para ser tratada como exploratória** — o que reforça validar contra o Trends, como
já fizemos (pico de 04/06/2026 coincidente nas duas fontes).

## Tese 3 — Share of search: a métrica de mercado mais próxima do que buscamos

| Referência | O que resolve aqui |
|---|---|
| **Binet, IPA EffWorks Global 2020** — [IPA](https://ipa.co.uk/effworks/effworksglobal-2020/share-of-search-as-a-predictive-measure) · [WARC](https://www.warc.com/en/article/les-binet-outlines-why-%22share-of-search%22-is-a-powerful%2C-predictive-marketing-metric-07db5c40f18642ca9d93d1e84a42d668) | A origem do conceito: share de busca por marca prediz market share com 6–12 meses de antecedência. É o padrão de mercado que nosso "índice de relevância" tentava replicar — e que **descartamos como métrica primária** por confundimento com spend. |
| **Hankins / Vizer para o think tank da IPA — 30 casos, 12 categorias, 7 países** — [Marketing Week](https://www.marketingweek.com/share-of-search-market-share/) | A validação mais ampla: share of search explica ~83% do market share. Também o alerta de escala — funciona em **categoria com concorrentes**, o que é o nosso problema (ver abaixo). |
| **Share of Search Council** — [site](https://www.myshareofsearch.com/) | Comunidade que mantém método e ferramentas; ponto de partida se formos construir a versão de categoria. |
| **Share of search na era da IA** — [Search Engine Land](https://searchengineland.com/why-share-of-search-matters-more-than-traffic-in-the-ai-era-466241) | Argumento atual de por que share of search ganha importância enquanto o clique orgânico cai (respostas geradas por IA) — relevante para nós, que medimos parte da atenção via tráfego. |

⚠️ **Por que não aplicamos direto:** share of search exige um **denominador de categoria** (buscas
da BP ÷ buscas de todos os concorrentes). Nós medimos só o numerador. Sem o denominador, o
indicador se move com o tamanho do mercado e com nosso próprio spend — que foi exatamente o
problema medido (Trends não sobreviveu à quantificação por quartis). **Construir o denominador
com uma lista de concorrentes é o próximo passo óbvio** e barato via Google Trends comparativo.

## Tese 4 — O confundidor que quase derrubou tudo: mídia gera "relevância"

| Referência | O que resolve aqui |
|---|---|
| **Blake, Nosko & Tadelis (2015), _Consumer Heterogeneity and Paid Search Effectiveness_** (*Econometrica*) — experimento eBay | **A referência central do nosso principal achado negativo.** Quem busca a marca em boa parte já viria de qualquer jeito. Explica por que busca de marca sobe com spend e por que não se pode ler tráfego de marca como incremental. Sustenta o descarte do social orgânico (ρ com spend 0,861). |
| **Gordon, Zettelmeyer et al. (2019), 15 lift studies no Facebook** — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3033144) | Atribuição observacional erra o lift experimental em até 3×, para os dois lados. Calibra quanto desconfiar de qualquer correlação nossa. |
| **Gordon, Moakler & Zettelmeyer (2023), _Close Enough?_** — [arXiv](https://arxiv.org/abs/2201.07055) | 663 experimentos: nem DML nem matching com 5.000+ features recuperam o efeito experimental, por causa do delivery algorítmico. **É o teto do nosso método** — o pareamento por spend é direcional, não causal. |
| **Lewis & Rao (2015), _The Unfavorable Economics of Measuring the Returns to Advertising_** (*QJE*) | Por que n=2 sabatinas nunca ia detectar nada, e por que reportamos intervalo em vez de ponto. A justificativa formal do teste placebo. |

## Tese 5 — Desenho de identificação (o que usamos e o que faltou)

| Referência | O que resolve aqui |
|---|---|
| **Brodersen et al. (2015), _CausalImpact_** — [paper](https://arxiv.org/abs/1506.00356) · [pacote](https://google.github.io/CausalImpact/) | Contrafactual bayesiano com covariáveis de controle. Implementamos a versão OLS + placebo porque a série (spend só desde ago/2025) não sustenta prior de sazonalidade anual — mas é o alvo se a série crescer. |
| **MacKinlay (1997), _Event Studies in Economics and Finance_** | Janela de evento vs janela de estimação, retorno anormal, p bicaudal. Estrutura da rodada 1. |
| **Bernal, Cummins & Gasparrini (2017), _Interrupted time series regression_** (*IJE*) — [paper](https://academic.oup.com/ije/article/46/1/348/2622842) | Tutorial de regressão segmentada; a alternativa frequentista simples ao CausalImpact para intervenções datadas. |
| **Hartmann, Nair & Narayanan (2011), RDD para marketing-mix** — [Stanford GSB](https://www.gsb.stanford.edu/faculty-research/publications/identifying-causal-marketing-mix-effects-using-regression) | Descontinuidades geradas pelas heurísticas da própria firma identificam efeito **marginal local** — o fundamento do estudo de mCAC por saltos de budget (rodada 3). |
| **Callaway & Sant'Anna (2021), DiD com múltiplos períodos** — [arXiv](https://arxiv.org/abs/1803.09015) | O estimador correto para os saltos escalonados; nossa mediana-de-ratio é uma aproximação mais simples. Caminho de refino do mCAC. |

## Tese 6 — Prática de mercado (o que o mercado realmente faz)

| Referência | O que resolve aqui |
|---|---|
| **eMarketer — FAQ de incrementalidade 2026** — [link](https://www.emarketer.com/content/faq-on-incrementality-how-prove-your-ads-actually-work-2026) | Estado da prática: MMM para visão cross-canal, atribuição para otimização diária, incrementalidade para validar. Nossa análise é do 1º tipo; o teste de lift é o que falta. |
| **Vervaunt — incrementalidade de brand awareness sobre mídia paga** — [link](https://vervaunt.com/how-to-measure-the-incrementality-of-brand-awareness-on-paid-media-activity) | Praticante, endereça exatamente nossa pergunta (marca eleva a eficiência do paid?) e descreve os testes geo/holdout que seriam o padrão-ouro aqui. |
| **Agility PR — atribuição de earned media** — [link](https://www.agilitypr.com/pr-news/uncategorized/measuring-pr-roi-advanced-attribution-models-for-earned-media-and-brand-visibility/) | Quando earned media e conversão sobem juntos, só o MMM separa PR do resto — o caso das sabatinas. |

---

## O que a bibliografia diz que deveríamos fazer a seguir

1. **Construir o denominador de categoria** para o share of search (Trends comparativo com
   concorrentes). Transforma um numerador confundido na métrica validada da IPA. Barato.
2. **Geo holdout ou lift test** — é o padrão-ouro que Gordon et al. mostram ser insubstituível.
   Nenhum método observacional nosso resolve o delivery algorítmico.
3. **Migrar para UCM/MMM com componente de marca** (Cain) quando houver ~2 anos de série: separa
   baseline estrutural de ruído e mede os dois caminhos (baseline + eficiência da ativação) que
   Binet & Field descrevem — em vez de correlação diária.
