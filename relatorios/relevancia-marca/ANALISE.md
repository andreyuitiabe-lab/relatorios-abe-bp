# Relevância pública → vendas: as sabatinas presidenciais geram lift?

**Data:** 21/08/2026 · **Pedido por:** André (a partir de discussão interna)
**Relatório publicado (02/09/2026):** https://andreyuitiabe-lab.github.io/relatorios-abe-bp/relatorios/relevancia-marca/ — snapshot das 6 rodadas, dados em `data.json` (gerado a partir dos resultados dos scripts; `refresh.py` só valida — recalcular exige rodar `scripts/*.py`). Versão interativa original: artifact `8db66008`.

## Pergunta original

A BP recebeu Renan Santos (14/08) e Pablo Marçal (17/08) em sabatinas presidenciais, com
percepção de "boa receita e custo marginal" nesses dias. Hipótese levantada internamente:
**relevância de marca baixa a resistência na adesão**. Pedido: medir o lift e, se possível,
extrair uma métrica acompanhável.

Metas verificáveis:
1. As sabatinas geraram lift em atenção e em vendas vs contrafactual?
2. O lift é de volume ou de conversão (resistência menor)?
3. Que métrica acompanhar daqui pra frente?

## Resposta curta

**A hipótese não se sustenta como formulada, mas há um efeito real e mensurável — em outro lugar.**

1. **Não houve lift de atenção nem de vendas atribuível às sabatinas no agregado.** A receita
   alta de 14–19/08 é explicada por escala de mídia (spend +55–81%, puxado por BP10/ENE/FNC),
   não por relevância. Nenhuma série de atenção passou do teste placebo.
2. **A "resistência" não caiu — ao escalar, piorou**, como manda a saturação normal: intra-campanha
   o ROAS caiu em 6 de 8 campanhas. Exceção: BP10 (CPA −25%, ROAS +16% escalando 51%).
3. **Mas no nível individual há efeito robusto**: membro de engajamento leve/médio que assiste
   uma sabatina compra **1,4–1,65× mais** nos 14 dias seguintes e gera **1,5–2,2× mais receita**
   (p<0,005, controlado por playlist-placebo, engajamento prévio e compra recente).
   Em freemium o efeito é **nulo ou negativo** — relevância pública **não** reduz resistência
   de aquisição; **ativa a base existente**.

A inversão importa para decisão: sabatina é instrumento de **ativação/upsell da base**, não
de aquisição. Distribuí-la como conteúdo de topo de funil para não-membros não é sustentado
pelos dados.

## Decisões de abordagem

| Decisão | Por quê |
|---|---|
| Janela da série: 01/08/2025 → 20/08/2026 | Spend Meta só existe desde 2025-08-01 (`meta-insider-ads.md`); sem spend não há controle do confundidor principal |
| Leads como proxy **secundário** de atenção | Nota do André: leads seguem campanha/LP ativa, não relevância. Primários: direct + busca de marca (GA4/Trends) |
| Janela de evento D0..D+2 | D+3 do Renan = D0 do Marçal; janelas maiores se sobrepõem |
| Significância por **placebo**, não por t-test | n=2 eventos; Lewis & Rao (2015) — vendas são ruidosas demais para lift pequeno. Placebo = todas as janelas de 3 dias fora dos eventos |
| Migrar do agregado para **pessoa-dia** | As sabatinas estão na plataforma (playlist `BP nas Eleições`) com e-mail identificável — desenho individual tem muito mais poder que o agregado |
| Comparador = top-8 playlists + resto | "Todo outro conteúdo" mistura catálogo antigo; o placebo justo é quem também escolheu assistir conteúdo popular |
| Outcome D+1..D+14 (não D+0) | Causalidade reversa: quem compra hoje assiste hoje. D+0 contaminava o estrato "novo" |
| Condicionar em **sem compra nos 60d** | Os viewers de sabatina tinham taxa de compra prévia *menor* (14,8% vs 22,2%) — confundidor "quem acabou de comprar não recompra" |

## Achados principais

### 1. Agregado: nenhum lift atribuível (etapa de contrafactual)

Resíduo de `log1p(y) ~ DOW + mês + log1p(spend) + fase de campanha + tendência`, percentil na
distribuição placebo (`data/resultado_event_study.csv`):

| Série | Renan (14/08) | Marçal (17/08) |
|---|---|---|
| Sessões Direct (GA4) | −16,4% (p32) | −5,2% (p50) |
| Sessões Organic Search | −24,1% (p12) | −22,3% (p14) |
| Sessões Organic Video | +6,5% (p63) | +55,4% (p82) |
| Leads orgânicos | +81,8% (p91) | +65,1% (p86) |
| Receita total | +13,9% (p71) | +6,6% (p63) |
| Receita canais orgânicos | +18,3% (p69) | +55,5% (p90) |
| CAC ads (menor é melhor) | −20,1% (p9) | −16,8% (p14) |
| Conversão por abordagem Comercial | +2,7% (p98) | −1,9% (p3) |

Nada cruza o p95 de forma consistente nos dois eventos. A conversão por abordagem Comercial
tem sinais **opostos** entre os dois eventos — ruído, não efeito. O **IRO** (índice composto de
atenção orgânica) nas datas foi **0,19 (Renan) e 0,45 (Marçal)**, contra 1,0–1,8 nos picos
históricos: as sabatinas não estão entre os eventos de atenção do último ano.

### 2. O que explica a receita alta: mídia, não relevância

Spend nas janelas vs pré (14–19/08 vs 17/07–13/08, equivalente 6 dias):

| Sigla | Spend janelas | Spend pré-equiv. | Escala |
|---|---|---|---|
| BP10 | R$ 788k | R$ 521k | +51% |
| ENE | R$ 193k | R$ 53k | +265% |
| FNC | R$ 93k | R$ 36k | +159% |
| MEC | R$ 71k | R$ 28k | +150% |
| ELS | R$ 137k | R$ 87k | +58% |

Intra-campanha (controla mix), o **ROAS caiu em 6 de 8**: ELS 2,06→1,34 · TLR 2,00→0,80 ·
ENE 1,66→1,30 · FNC 1,54→1,01 · 10R 1,33→1,00 · ODI 1,40→1,35. Só **BP10 melhorou**
(1,52→1,77, CPA R$679→R$507) e **MEC** (CPA R$626→R$517). Comportamento de saturação normal —
e consistente com a dose-resposta da wiki (saltos >50% → mCAC pior).

### 3. Individual: o efeito real (teste principal)

Playlist `BP nas Eleições` = 9 sabatinas (Caiado, Cury, Aldo Rebelo, Zema, Marçal, Salles,
Caroline de Toni, Derrite, Renan). Pessoa-dia, membros sem compra nos 60d anteriores,
engajamento prévio ≥1 dia, outcome D+1..D+14 (`data/adesao_condicionado.csv`):

| Estrato | Sabatina | vs top-playlists | vs outro conteúdo | RPP-14 sabatina | razão RPP |
|---|---|---|---|---|---|
| Membro engaj. **leve** (1–2 dias/30d) | 1,970% | 1,194% → **1,65×** *** | 1,225% → 1,61× *** | R$ 28,59 | 1,8–2,2× |
| Membro engaj. **médio** (3–8 dias) | 2,174% | 1,511% → **1,44×** *** | 1,568% → 1,39× *** | R$ 32,54 | 1,5–1,7× |
| Membro **heavy** (9+ dias) | 2,224% | 2,564% → 0,87× (ns) | 2,355% → 0,94× (ns) | R$ 39,25 | 1,26× |
| **Freemium** (todas as faixas) | 0,98–1,65% | **0,28–0,83×** (ns) | 0,32–0,66× (ns) | R$ 1–11 | 0,1–1,3× |

*** p<0,005 (Fisher exato). IC95 da diferença em membro leve: [+0,24, +1,31] pp.

Teste de seleção (pré-tendência): os viewers de sabatina tinham taxa de compra nos 15d
**anteriores** *menor* que os comparadores (14,8% vs 22,2% no leve) — o grupo tratado não é
selecionado por propensão de compra, o que reforça o achado em vez de explicá-lo.

### 4. Onde a sabatina se posiciona no catálogo

IAC (Índice de Ativação Comercial) = RPP-14 da playlist ÷ RPP-14 mediano do catálogo
(R$ 15,54; 172 playlists com ≥500 pessoa-dias — `data/iac_ranking_com_indice.csv`):

- `BP nas Eleições`: RPP-14 **R$ 30,75**, IAC **1,98×**, **rank 22 de 172**.
- Topo dominado por conteúdo **com oferta associada**: Clube do Livro BP 9,73× · Certificação
  Política Internacional 7,78× · Os Falsários 7,09× · Travessia 5,48×.
- ⚠️ **Nuance que importa:** `BP Entrevista` (formato irmão, sem pauta eleitoral) tem IAC
  **2,70×** — *acima* da sabatina. Ou seja, o poder de ativação vem do **formato entrevista**,
  não da relevância eleitoral em si. Esse é o teste que falta fechar (ver pendências).
- Base do ranking: conteúdo de curiosidade/catálogo (BPeiro 0,24–0,31×, docs antigos ~0,30×).

## Rodada 2 — relação contínua: relevância × vendas (volume e eficiência)

**Pergunta:** olhando redes sociais, portal, YouTube etc., existe relação entre relevância e
nossas vendas? Aqui o desenho troca 2 eventos por **385 dias**, que é onde há poder de fato.

**Método:** cada canal orgânico é comparado em dias de audiência **alta vs baixa** dentro do
mesmo quintil de spend × fim-de-semana × fase de venda (pareamento não-paramétrico, bootstrap
2.000 reps). Isso é mais rigoroso que residualizar contra `log(spend)`: se a relação com mídia
for curva, o resíduo linear guarda spend e o "efeito de relevância" é mídia disfarçada. A linha
`Spend [checagem]` mostra se o pareamento funcionou. Script:
[scripts/teste_pareado_spend.py](scripts/teste_pareado_spend.py) · saída em
`data/teste_pareado_resultado.txt`.

### Resposta: sim, mas só em alguns canais — e o mais óbvio é o único que não vale

| Canal orgânico | Transações | Receita | CAC de ads | ROAS | Conv/1k sessões | Spend pareou? |
|---|---|---|---|---|---|---|
| **YouTube orgânico** (Organic Video) | **+24,7%** *** | +13,6% *** | **−11,9%** *** | **+15,2%** *** | **+28,8%** *** | ✅ +0,4% ns |
| **Busca orgânica** | +21,9% *** | +8,8% ** | **−9,2%** *** | +12,0% *** | +8,1% * | ✅ −3,0% ns |
| Referral | +19,8% *** | +24,1% *** | −0,1% ns | +17,7% *** | +5,3% ns | ⚠️ +4,8% ** |
| Tráfego direto | +9,3% *** | +18,9% *** | +2,9% ns | +13,5% *** | **−11,7%** ** | ⚠️ +4,4% ** |
| **Social orgânico** | +2,1% ns | +18,8% *** | **+12,9% (pior)** *** | −1,8% ns | **−20,6%** *** | ❌ **+16,8%** *** |

*** p<0,01 · ** p<0,05 · * p<0,10 (bootstrap). IC95 do CAC no YouTube orgânico: [−16,2%, −6,4%].

**1. YouTube orgânico é o único indicador com sinal limpo nas duas dimensões.** Com o **mesmo
spend** (pareamento perfeito: +0,4%, ns), dias de audiência alta têm **24,7% mais transações e
CAC 11,9% menor**. Não é composição de mídia nem de calendário: é o mesmo dinheiro comprando
mais. A conversão por sessão sobe 28,8%, que é a assinatura de "porta mais aberta" — a mesma
visita converte melhor. Esse é o achado que a rodada 1 não conseguiu enxergar com n=2 eventos.

**2. Busca orgânica repete o padrão, com uma ressalva de ticket.** Volume +21,9% e CAC −9,2%,
mas a receita sobe bem menos (+8,8%) porque o **ticket médio cai ~11%** — traz mais gente, de
compra menor. Consistente com Blake, Nosko & Tadelis: parte de quem busca a marca já viria.

**3. "Social orgânico" — o que todo mundo chamaria de relevância nas redes — é mídia
disfarçada.** É o único canal onde o pareamento por spend **falha** (+16,8%, p<0,001): dias de
social orgânico alto são simplesmente dias de campanha grande. Depois de pareado o que dá:
transações não sobem (+2,1% ns), a conversão por sessão **cai 20,6%** e o **CAC piora 12,9%**.
A receita +18,8% é o spend, não a relevância. Isso faz sentido mecanicamente: o GA4 classifica
como Organic Social o clique em link de bio/stories, que sobe junto com a campanha.
**Consequência prática: não usar engajamento/alcance de rede social como termômetro de
relevância comercial** — ele anda com a mídia e, condicionado a ela, anda contra a eficiência.

**4. Direto e Referral movem volume e ROAS, mas não a eficiência de aquisição** (CAC neutro), e
o direto tem conversão por sessão *negativa*. Provável mecânica: são canais de gente que já é
cliente voltando (ticket +8,7% no direto), não de porta se abrindo.

### Como os canais foram comparados (e o que NÃO foi comparado)

⚠️ **Os cinco canais nunca foram comparados entre si em nível.** Cada linha da tabela é um
teste independente do canal **contra ele mesmo**: dias de audiência alta daquele canal vs dias
de audiência baixa **do mesmo canal**, dentro do mesmo estrato. Comparar níveis seria sem
sentido — as escalas diferem em duas ordens de grandeza:

| Canal (GA4, sessões/dia) | Mediana | p10 | p90 | % do tráfego orgânico |
|---|---:|---:|---:|---:|
| Social orgânico | 52.643 | 20.377 | 165.192 | 69,7% |
| Busca orgânica | 15.991 | 2.514 | 27.187 | 16,9% |
| Tráfego direto | 9.215 | 5.891 | 19.985 | 12,1% |
| YouTube orgânico | 767 | 379 | 2.052 | 1,0% |
| Referral | 165 | 87 | 348 | 0,3% |

Social orgânico é **69× o YouTube orgânico** em nível. O que torna os cinco testes comparáveis
em *método* é a fonte única: todos são `sessions` por dia do mesmo `sessionDefaultChannelGroup`
do GA4 — mesma unidade, mesma instrumentação, mesma janela. O corte alta/baixa é a mediana
**local** (dentro de cada um dos 16 estratos de spend × calendário), nunca a mediana global.

**A ressalva que isso cria:** a "dose" entre alta e baixa não é igual entre canais — o YouTube
varia 2,7× entre os grupos, o social só 1,8×. Então os percentuais brutos não estão na mesma
régua. Normalizando por dose (elasticidade = ln efeito ÷ ln dose):

| Canal | Dose | Efeito tx | **Elast. tx** | Efeito CAC | **Elast. CAC** |
|---|---:|---:|---:|---:|---:|
| Busca orgânica | 2,1× | +21,9% | **0,267** | −9,2% | **−0,130** |
| YouTube orgânico | 2,7× | +24,7% | **0,222** | −11,9% | **−0,128** |
| Referral | 4,0× | +19,8% | 0,130 | −0,1% | −0,001 |
| Tráfego direto | 2,2× | +9,3% | 0,113 | +2,9% | +0,036 |
| Social orgânico | 1,8× | +2,1% | 0,035 | +12,9% | +0,206 |

Na régua bruta o YouTube lidera em volume; **normalizado por dose, YouTube e busca orgânica
empatam** (elasticidade de CAC −0,128 vs −0,130) e a busca fica até ligeiramente à frente em
volume. A conclusão qualitativa não muda — os dois são os únicos com sinal limpo, e o social é
último nas duas réguas — mas **não se deve dizer que o YouTube é "mais forte" que a busca**.
A vantagem prática do YouTube é outra: por ser um canal pequeno e volátil (p90/p10 = 5,4×), ele
se move mais e mais cedo, o que o torna melhor *termômetro* — não necessariamente melhor alavanca.

### Escopo dos números da rodada 2 — decomposição por canal (25/08)

Pergunta do André: "+24,7% de transações e CAC −11,9% é no total?" **Transações: sim, total
(todos os canais, Comercial incluído). CAC: não — é spend ÷ tx atribuídas a ads.** Pareamento
por spend do YouTube orgânico (GA4 Organic Video), mesmos estratos; spend igual (+0,4% ns):

| Alvo | Baixa | Alta | Δ | IC95 |
|---|---:|---:|---:|---|
| Transações TOTAL | 1.120 | 1.388 | **+24,7%** | [+17,4, +34,3] |
| ↳ Comercial | 276 | 306 | +14,6% | [+6,4, +29,8] |
| ↳ Digital | 843 | 1.083 | +29,6% | [+21,9, +41,2] |
| — atribuídas a ads (FB/Google) | 478 | 587 | +17,5% | [+11,3, +25,6] |
| — canais orgânicos (Portal/Organic) | 94 | 129 | +43,0% | [+29,6, +68,6] |
| — CRM (e-mail/WhatsApp) | 170 | 224 | **+50,1%** | [+31,5, +93,5] |
| — canal YouTube | 23 | 29 | +56,1% | [+19,1, +137,7] |
| Receita TOTAL | R$ 470,6k | R$ 505,8k | +13,6% | [+6,0, +26,8] |
| spend ÷ tx atribuídas a ads (**CAC reportado**) | R$ 316 | R$ 273 | −11,9% | [−16,2, −6,3] |
| spend ÷ tx digitais | R$ 176 | R$ 141 | −16,7% | [−21,2, −10,1] |
| spend ÷ tx TOTAL | R$ 127 | R$ 103 | −15,8% | [−20,2, −10,0] |

- **O efeito é maior onde não há mídia**: ads +17,5% vs CRM +50% e orgânico +43% — coerente com a
  rodada 1 (relevância ativa a base). Até o Comercial sobe 14,6%.
- Receita sobe menos que transações (+13,6% vs +24,7%) porque o ticket cai.
- O CAC de ads (−11,9%) é a régua mais **conservadora** e a única que é um CAC de verdade; as
  outras dividem spend por vendas que a mídia não gerou.

### Mecanismo: volume de tráfego ou qualidade do dia? (25/08)

Pergunta do André: "isso tem a ver com o volume de tráfego? preciso de tráfego para vender; aparecendo
mais em orgânico, gasto menos". Teste em três partes (pareamento por spend do YouTube orgânico +
regressões diárias, 385 dias):

| Em dias de YT orgânico alto (spend igual) | Baixa | Alta | Δ |
|---|---:|---:|---:|
| Sessões TOTAIS do site | 134.843 | 133.620 | +2,4% ns |
| ↳ pagas | 16.371 | 16.619 | −1,0% ns |
| ↳ orgânicas (direto+busca+vídeo+referral) | 28.405 | 34.530 | **+26,2%** |
| Conv: tx digitais / 1k sessões | 6,6 | 8,2 | **+28,8%** |
| Conv: tx ads / 1k sessões **pagas** | 36,5 | 41,1 | **+12,7%** |
| Conv: tx orgânicas / 1k sessões orgânicas | 3,8 | 4,2 | +15,2% |

- **O tráfego total não muda**; o +24,7% de transações vem de **conversão**, não de volume. A visita
  paga também converte melhor (+12,7%). Controlar sessões totais na regressão quase não altera o
  efeito do YT orgânico (β 0,141 → 0,132, t=6,5) — não é mediado por tráfego.
- **Elasticidades** (log tx ~ controles + log spend + log sessões por tipo): pagas β=−0,03 ns (não
  acrescentam além do spend); **orgânicas β=+0,137 (t=4,5)**: +10% sessões orgânicas ≈ +1,3% tx;
  CRM +0,083; social ≈ 0.
- **Nuance sobre "tráfego"**: boa parte do orgânico (sobretudo direto) é membro entrando para
  assistir, não prospect — conversão por sessão orgânica é 10× menor que por sessão paga (4 vs 41/1k).
  "Mais tráfego orgânico" ≠ "mais prospect na porta".
- **Implicação**: se fosse volume, a alavanca seria comprar menos tráfego em dia orgânico alto. Como é
  conversão, é a inversa — dia de relevância alta é dia em que o real de mídia rende mais (manter/
  escalar), sempre com a ressalva do confundidor "lançamento bom". Coerente com CRM +50% e Comercial
  +14,6% (nenhum depende de tráfego do site).

### O que é "dia com muitas sessões" — o corte, em números (25/08)

Não existe um corte absoluto. "Alta" = acima da **mediana do próprio estrato** (quintil de spend ×
dia útil/fds × fase). Os 16 cortes vão de **515 a 1.282 sessões/dia** de YouTube orgânico — o mesmo
número pode ser alta num contexto e baixa em outro (ex.: Q1-spend dia útil sem venda corta em 1.282;
Q1 dia útil com venda aberta corta em 515). Alta média ≈ 1.571/dia; baixa média ≈ 580/dia.

**Regra operacional equivalente** (para acompanhar sem recalcular estratos): sessões do dia ÷ média
móvel dos 28 dias anteriores.

| Regra | % dos dias marcados | Precisão (é alta no pareamento) | Cobertura (dos dias alta) |
|---|---:|---:|---:|
| > 1,00× MM28 | 32% | 89% | 57% |
| > 1,15× MM28 | 24% | 94% | 46% |
| **> 1,30× MM28** | **18%** | **98%** | 36% |
| > 1,50× MM28 | 13% | 98% | 25% |

Recomendação: **> 1,3× MM28** = "dia de relevância alta" (quase sem falso positivo, ~1 dia em 5).
Referência: mediana 767 · p75 1.173 · p90 2.052 sessões/dia.

### A correlação relevância × resistência sobrevive a efeito fixo de semana (25/08)

Pergunta do André: "a tabela de conversão não é a prova da correlação relevância × resistência?"
**Sim.** Conversão por sessão (digital e, sobretudo, **paga**) sobe em dias de relevância alta com
spend e tráfego iguais — é a definição operacional de resistência menor. Para afastar a explicação
"semana de lançamento bom", regressão de log(conv/sessão) com **efeito fixo de semana** (só variação
dia a dia dentro da mesma semana/campanha/mídia), + log spend + log sessões + DOW + fase:

| log(conv/sessão) ~ … + log(YT orgânico) | só controles + mês | + log leads (intensidade) | **+ EF semana** | + EF semana + leads |
|---|---:|---:|---:|---:|
| conv. digital | β +0,146 (t 6,0) | +0,133 (t 5,4) | **+0,192 (t 7,8)** | +0,189 (t 7,7) |
| conv. de ads por sessão **paga** | +0,088 (t 1,8) | +0,049 (t 1,0) | **+0,127 (t 2,8)** | +0,113 (t 2,6) |

A correlação **fica mais forte** dentro da semana (+10% chegadas do YT ≈ +1,8% de conversão digital,
+1,2% na paga). "Semana boa" descartada. O que resta entre correlação e causa: um evento **do dia**
(vídeo viral, menção) pode elevar simultaneamente chegadas do YT e disposição de compra — as duas
seriam o mesmo fenômeno. Só variação exógena (geo lift) fecha isso.

**Veredito revisado da hipótese:** *correlacionalmente sustentada* — sobrevive a spend, tráfego e
semana; causalidade e magnitude causal em aberto. Substitui a redação "associação diária".

### Não existe um "fator de relevância" único

Correlação Spearman entre os resíduos semanais dos indicadores:

| | Trends | YT orgânico | Social orgânico |
|---|---|---|---|
| **Trends (busca de marca)** | 1,000 | **−0,119** | +0,199 |
| **YouTube orgânico** | −0,119 | 1,000 | **−0,198** |
| **Social orgânico** | +0,199 | −0,198 | 1,000 |

Os indicadores são **ortogonais ou negativamente correlacionados** — não medem a mesma coisa
subjacente. Isso mata a ideia de um índice composto de relevância (testei: o índice combinado
performa **pior** que o YouTube orgânico isolado). Cada canal orgânico tem dinâmica própria;
tratar "relevância" como uma variável só é erro de medida.

### Google Trends: sinal na direção certa, mas frágil

Na frequência semanal (n=56, líquido de spend), busca de marca correlaciona com transações
(+0,285*), tx orgânicas (+0,446*), conversão por sessão (+0,372*) e **CAC (−0,455*)**. Mas ao
quantificar por quartis com bootstrap, nada sobrevive (CAC −10,4%, p=0,19, IC [−27%, +11%]) —
n=14 por quartil não sustenta. **Trends fica como sinal exploratório, não métrica de decisão.**

### Sobre a direção da causalidade

Testei atenção(t)→receita(t+k) contra receita(t)→atenção(t+k): nenhuma direção tem sinal
significativo em lag ≥1 (o único que aparece é receita→atenção em k=7, rho=+0,112, p=0,03).
O efeito é **contemporâneo** (mesmo dia), o que é esperado — a audiência e a venda são o mesmo
evento de atenção — mas **impede afirmar causalidade**. A leitura defensável é: audiência
orgânica no YouTube é um **indicador coincidente** de dias comercialmente melhores, útil como
termômetro e como sinalizador de eficiência, não uma alavanca provada.

### Portal (Mixpanel)

`fct_mixpanel__portal_page_view_events` existe mas **só desde 01/05/2026**, com instrumentação
crescendo (5 devices/dia no início vs ~21k na média) — série curta e não estacionária, ficou
fora da análise. Reavaliar em 2026Q4, quando houver ~12 meses estáveis. Query pronta:
[16_portal_diario.sql](queries/16_portal_diario.sql).

## Rodada 3 — mCAC (custo da venda adicional) × audiência

**Pergunta (André, 25/08):** pegar a audiência do YouTube e correlacionar com volume de vendas
e **custo marginal**. Duas correções de rumo em relação às rodadas 1–2:

1. **Custo marginal ≠ CAC médio.** As rodadas anteriores usaram `spend ÷ transações`, que é o
   custo *médio*. O custo da venda **adicional** exige desenho quasi-experimental — o método já
   validado em `midia-paga/VALIDACOES.md` (pooling de saltos naturais de budget).
2. **A audiência real do YouTube não existe no warehouse.** Verificado: só há
   `fct_leads_funnel.youtube_registration_d7/d15/d30` (leads atribuídos). O `Organic Video` do
   GA4 é o reflexo no site — mediana de **767 sessões/dia**, contra views do canal na casa das
   centenas de milhares. Integração criada em `~/meu_projeto/BigQuery/youtube-analytics/`
   (README com setup); **pendente de autenticação OAuth do André**.

### Método (replica midia-paga)

Cada campanha-dia com `|Δspend| ≥ 25%` sobre base de 3 dias estável (CV ≤ 0,35) é um evento.
Contrafactual = mediana do ratio de vendas das campanhas **estáveis** (|Δspend| ≤ 10%) do mesmo
dia, exigindo ≥ 5 controles — absorve o choque de demanda comum. `mCAC = Δspend ÷ Δvendas_ajustado`,
só interpretável quando spend e vendas se movem no mesmo sentido.
Query: [17_spend_vendas_por_campanha_diario.sql](queries/17_spend_vendas_por_campanha_diario.sql) ·
script: [mcac_vs_audiencia.py](scripts/mcac_vs_audiencia.py).

**Validação contra a referência da wiki** (pooling de 307 saltos, jul/2026) — 1.069 eventos
detectados, 851 com mCAC interpretável:

| Regime | Direção | n | mCAC medido | Referência wiki | Bate? |
|---|---|---:|---:|---|---|
| PPT | up | 134 | R$ 195 | R$ 188 (IC 151–261) | ✅ dentro do IC |
| PPT | down | 134 | R$ 207 | R$ 188 | ✅ próximo |
| LAN | down | 326 | R$ 271 | R$ 250 | ✅ próximo |
| LAN | up | 249 | R$ 212 | R$ 145 (IC 129–196) | ⚠️ acima do IC |

3 de 4 batem. O LAN-up sai alto provavelmente por diferença de janela (aqui ago/2025+, lá
fev/2024–jul/2026) e de estimador (mediana de ratio vs Callaway–Sant'Anna). Pipeline
direcionalmente calibrado, não substitui o pooling oficial.

### Resultado preliminar (com o PROXY do GA4 — não é a audiência do canal)

| Recorte | n | mCAC audiência baixa | mCAC audiência alta | Variação | p |
|---|---:|---:|---:|---:|---:|
| Saltos **up**, campanhas `[VENDA]` | 328 | R$ 204 | R$ 184 | **−10,0%** | 0,028 |
| Saltos up, todos | 383 | R$ 210 | R$ 200 | −4,7% | 0,183 |
| Saltos up, campanhas `[LEAD]` | 55 | R$ 417 | R$ 640 | **+53,5%** | 0,115 |
| Saltos **down** (qualquer) | 461 | R$ 254 | R$ 256 | +0,7% | 0,670 |

- **O sinal existe mas é fraco.** Em `[VENDA]`-up o mCAC cai 10% com audiência alta (Spearman
  −0,109, p=0,049), mas o IC95 da razão de médias é **[−36%, +22%]** — atravessa zero.
- ⚠️ **`[LEAD]` vai na direção oposta** (+53,5%, Spearman +0,284, p=0,036, n=55). Escalar
  captação em dia de audiência alta sai *mais caro*. Se confirmar com dado real, é um achado
  operacional relevante — e por ora impede qualquer regra única de "escalar quando a marca está em alta".
- **O efeito no marginal é bem menor que no médio** (−10% vs −11,9% no CAC médio, com
  significância muito mais frágil). Coerente: o marginal é mais ruidoso por construção.

**Conclusão desta rodada:** com o proxy, não há base para uma regra de bidding. A pergunta só
fecha com a série real do YouTube — o pipeline está pronto e roda com um argumento
(`--audiencia yt_diario.csv --coluna views`).

## Rodada 4 — inventário de fontes de relevância diária

**Pergunta (André, 25/08):** o que mais dá para usar para medir o tamanho da relevância por dia?

Critério de aceitação de um indicador (script: [avaliar_fontes.py](scripts/avaliar_fontes.py)):
1. **existe série diária utilizável** na janela com spend (ago/2025+);
2. **é independente de spend** — senão mede orçamento, como o social orgânico;
3. **move com vendas e/ou eficiência** depois de controlar mídia, DOW, mês, fase e tendência.

| Indicador | Fonte | ρ c/ spend | Indep.? | ρ→vendas | ρ→CAC | Veredito |
|---|---|---:|---|---:|---:|---|
| YouTube orgânico | GA4 | 0,162 | sim | +0,265* | −0,143* | ★ volume + eficiência |
| Busca orgânica | GA4 | −0,188 | sim | +0,184* | −0,197* | ★ volume + eficiência |
| **Wikipedia — verbete BP** | **API Wikimedia** | 0,315 | meio | **+0,243\*** | **−0,208\*** | **★ volume + eficiência** |
| Tráfego direto | GA4 | 0,371 | meio | +0,163* | −0,118* | ★ volume + eficiência |
| Referral | GA4 | −0,071 | sim | +0,211* | −0,070 | só volume |
| Contatos novos no Zenvia | `dim_zenvia_contacts` | 0,060 | sim | +0,327* | −0,083 | só volume |
| Contatos de Suporte (inbound) | `dim_zenvia_contacts` | 0,300 | sim | +0,257* | −0,094 | só volume |
| Cliques busca de marca | Google Ads `[KW] Institucional` | 0,518 | meio | +0,239* | −0,090 | só volume |
| Leads orgânicos | `dtm_analytics_lead_conversion` | −0,025 | sim | +0,112* | +0,014 | só volume |
| Impressões busca de marca | Google Ads `[KW] Institucional` | 0,384 | meio | +0,041 | +0,058 | sem sinal |
| **Social orgânico** | GA4 | **0,861** | **NÃO** | +0,013 | −0,137* | **mede orçamento** |

\* p<0,05. ρ→CAC negativo é bom (aquisição mais barata).

### Wikipedia é a descoberta desta rodada

`pt.wikipedia.org/wiki/Brasil_Paralelo`, via [API pública da Wikimedia](https://wikimedia.org/api/rest_v1/)
— 385 dias, mediana **96 views/dia**, sem custo nem autenticação. Query no
[avaliar_fontes.py](scripts/avaliar_fontes.py); série em `data/wikipedia.csv`.

Por que importa mais do que o volume sugere: **ninguém compra tráfego para a Wikipedia.**
É estruturalmente imune ao confundidor que derrubou o social orgânico. É o indicador com o
**segundo melhor sinal de eficiência** de toda a lista (ρ→CAC −0,208, atrás só da busca orgânica),
e mede curiosidade sobre *a empresa* — não sobre um produto em campanha.

⚠️ Volume baixo (mediana 96) = ruído alto no diário; ler em média móvel de 7 dias ou semanal.
Validação cruzada independente: o pico de 04/06/2026 aparece **simultaneamente** no Trends
(índice 100, o máximo do período) e na Wikipedia (207 views) — duas fontes sem relação técnica
concordando no mesmo dia.

### O que a rodada elimina

- **Social orgânico está oficialmente descartado** como indicador: ρ com spend de **0,861**.
  Não é "meio confundido", é essencialmente uma medida de orçamento.
- **Impressões de busca de marca no Google Ads não servem** (sem sinal em nada). Motivo provável:
  impressão depende de lance e budget da campanha, não do volume de busca. Os **cliques** salvam
  algum sinal de volume, mas nada de eficiência. Para medir busca de marca de verdade seria
  preciso *impression share*, que **não existe** em `dtm_analytics_google_ads_funnel`
  (colunas conferidas) — o caminho certo é o Search Console.
- **Zenvia e leads orgânicos** movem volume mas não eficiência — são termômetro de demanda,
  não de "porta mais aberta".

### Fontes que valem destravar (ordem de custo-benefício)

| Fonte | O que dá | Custo | Status |
|---|---|---|---|
| **Google Search Console** | impressões e cliques **por query** de marca, sem depender de budget — o "share of search" real | grátis, API própria | não integrado; exige acesso à propriedade do site |
| **YouTube Analytics** | views/dia, watch time, inscritos do canal | grátis | integração pronta, **bloqueada por permissão** (ver `youtube-analytics/README.md`) |
| Meta/Instagram Insights | alcance e seguidores orgânicos por dia | Graph API | não avaliado |
| GA4 `newUsers` | usuários novos/dia — conceitualmente melhor que sessões | já temos acesso | candidato imediato, ainda não testado |
| Firebase / lojas de app | installs por dia | já temos Firebase | não avaliado (ver `freemium-app.md`) |
| Menções na imprensa | GDELT ou News API | grátis/barato | não avaliado |

## Rodada 5 — Fase 1 do PLANO executada: Share of Search com denominador ⚠️ (veredito revisado na rodada 6)

Decisão do André (25/08): três denominadores — mídias, streamings e todos. Coleta via pytrends
com âncora encadeada BP↔Globoplay↔Netflix (o Trends normaliza pelo máximo do grupo; contra a
Netflix a BP arredondaria a zero). 260 semanas (set/2021→ago/2026), BR.
Scripts: [share_of_search.py](scripts/share_of_search.py) · [sos_backtest.py](scripts/sos_backtest.py) ·
[sos_controle_spend.py](scripts/sos_controle_spend.py) · série em `data/share_of_search.csv`.

**Níveis** (média histórica → últimas 4 semanas): SoS-mídias **7,6% → 12,2%** · SoS-streamings
0,74% → 0,70% · SoS-todos 0,66% → 0,67%. Categoria mídias = Jovem Pan, Revista Oeste, Gazeta do
Povo, O Antagonista; streamings = Netflix, Prime Video, Globoplay, Disney+.

**Backtest mensal (59 meses), z vs média móvel 12m, Spearman SoS(t) × alvo(t+lead):**

| Indicador | L0 | **L1** | L2 | L3 | L1 em 2021-23 | L1 em 2024-26 | L1 parcial (−spend) |
|---|---:|---:|---:|---:|---:|---:|---:|
| SoS todos × transações | +0,83* | **+0,55*** | +0,43* | +0,28 | +0,56* | +0,58* | +0,46* |
| SoS streamings × tx | +0,82* | +0,54* | +0,41* | +0,26 | +0,55* | +0,58* | +0,44* |
| SoS mídias × tx | +0,69* | +0,47* | +0,46* | +0,31* | +0,43* | +0,56* | **+0,49*** |
| Busca BP absoluta × tx | +0,79* | +0,52* | +0,50* | +0,28 | +0,50* | +0,53* | +0,42* |

Em Δlog MoM o sinal é só contemporâneo (L0 +0,54–0,63*, L1 nulo) — o lead vive na frequência
de regime (desvio da MM12), não no choque mês a mês. SoS-mídias segura lead mais longo em
receita (L3 +0,38*, L4 +0,32*).

**Veredito inicial (25/08, manhã):** passou — lead de 1–2 meses, estável nos subperíodos, sobrevive
ao controle de spend **do mês do SoS** (+0,44 a +0,49). ⚠️ **Revisado na rodada 6: o lead NÃO
sobrevive ao controle do spend do mês ALVO** (+0,52 → +0,18 ns). O que sobrevive é o sinal
contemporâneo (+0,58* controlado por spend). Ver abaixo.

**Caveats honestos:**
- O controle de spend usa a planilha histórica (subreporta até −32%; sem Google/CRM) — é um
  controle parcial. Refazer com spend BQ quando a série ago/2025+ amadurecer.
- O denominador agrega pouco sobre a busca absoluta da BP no backtest (L1 +0,55 vs +0,52) — o
  valor do denominador é interpretabilidade (share, não volume) e proteção contra choques de
  mercado; não é ele que cria o sinal.
- Alvo é a **nossa** receita, não market share externo (que não temos) — leads mais curtos que
  os 6–12m da IPA são esperados.

**Métrica adotada:** SoS-todos mensal (z vs MM12) como indicador antecedente de 1–2 meses;
SoS-mídias como leitura de share competitivo. Atualização mensal via `share_of_search.py`.

## Rodada 6 — o resultado completo usando o Share of Search

**Pergunta (André):** usando o SoS como indicador de relevância, como fica o resultado (volume e eficiência)?
Script: [sos_vs_resultado.py](scripts/sos_vs_resultado.py). Quatro testes, mesma máquina das rodadas anteriores.

### A) Semanal com spend BQ (56 semanas) — eficiência: nada

Resíduo de SoS × resíduo de alvo (controlando mês, log spend, tendência), lags 0–2:

| SoS-todos × | L0 | L1 | L2 |
|---|---:|---:|---:|
| Transações | +0,16 | +0,03 | −0,22 |
| Receita | +0,10 | +0,06 | −0,04 |
| **CAC ads** | +0,06 | +0,03 | +0,24 |
| **ROAS** | +0,09 | +0,07 | −0,04 |
| Conv/1k sessões | +0,16 | −0,02 | −0,17 |

Nenhuma célula significativa. Quartis Q4 vs Q1 (n=14/14): CAC **+16,2%** (pior, p=0,16, IC [−5%, +40%]),
transações −8,8% (ns). **Na frequência semanal e com spend real, o SoS não move eficiência.**

### C) mCAC nos saltos de budget × SoS da semana — nada

| Saltos | n | mCAC SoS baixo | mCAC SoS alto | Δ | p |
|---|---:|---:|---:|---:|---:|
| up | 383 | R$ 207 | R$ 205 | −0,9% | 0,44 |
| down | 461 | R$ 254 | R$ 256 | +0,7% | 0,77 |
| `[VENDA]` up | 328 | R$ 196 | R$ 194 | −1,4% | 0,49 |

Spearman SoS×mCAC = −0,019. **O custo da venda adicional não depende do SoS.** (Com o proxy de
YouTube havia −10% em `[VENDA]`-up; com SoS, zero.)

### D) Mensal longo (48 meses, spend-planilha) — o que o SoS realmente antecede

| SoS-todos(t) × alvo(t+lead) | L0 | L1 | L2 | L3 |
|---|---:|---:|---:|---:|
| **Spend Meta** | **+0,68\*** | **+0,62\*** | **+0,55\*** | **+0,42\*** |
| Transações | +0,82* | +0,52* | +0,39* | +0,25 |
| Receita | +0,72* | +0,55* | +0,45* | +0,42* |
| Ticket médio | −0,59* | −0,25 | −0,19 | −0,11 |
| CAC | −0,34* | +0,06 | +0,11 | +0,04 |
| ROAS | −0,26 | **−0,45\*** | **−0,43\*** | **−0,34\*** |

**O SoS antecede spend tanto quanto antecede vendas.** SoS alto em t → a empresa escala mídia em
t+1..t+3 → vendas sobem junto → **ROAS cai** (saturação). O "lead" da rodada 5 era isso.

### O teste decisivo: lead controlando spend do mês alvo

| SoS(t) → alvo(t+1) | bruta | −spend(t) | **−spend(t) e spend(t+1)** |
|---|---:|---:|---:|
| SoS-todos → tx | +0,52 | +0,46 | **+0,18** (ns) |
| SoS-todos → receita | +0,55 | +0,50 | **+0,04** (ns) |
| SoS-mídias → tx | +0,54 | +0,49 | +0,25 (ns) |
| Busca BP absoluta → tx | +0,49 | +0,46 | +0,07 (ns) |

**O lead desaparece.** Já o **contemporâneo** sobrevive: SoS(t) × tx(t) controlado por spend(t) =
**+0,58\*** (n=43) — mais forte que qualquer indicador diário da rodada 4.

### Conclusão da rodada 6

1. **SoS é o melhor indicador coincidente de relevância que temos** — mais limpo que os diários e
   com 5 anos de história — mas **não é antecedente de vendas**. É antecedente da **nossa própria
   decisão de mídia** ("escalar no calor"), o que é interessante para gestão, não para previsão.
2. **Relevância (via SoS) não melhora eficiência** em nenhuma frequência com spend real: CAC
   semanal ns, mCAC ns, ROAS mensal *negativo* pelo efeito da escala que se segue.
3. O único lugar onde CAC responde ao SoS é o **contemporâneo mensal** (−0,34*) — coerente com o
   +0,58 em transações: mês de SoS alto é mês bom, mesmo dinheiro rende mais. É o mesmo achado
   da rodada 2, agora numa métrica única e de 5 anos.
4. **Ticket médio cai** quando SoS sobe (−0,59* em L0): relevância traz comprador de ticket
   menor — repete o padrão da busca orgânica (rodada 2).

**Métrica adotada (revisada):** SoS-todos mensal como **termômetro coincidente** de regime
(z vs MM12), não como previsor. Para o time de mídia a leitura útil é a inversa: **quando o SoS
sobe, historicamente escalamos e o ROAS caiu nos 3 meses seguintes** — vale checar se a escala
que se segue a um bom momento está sendo calibrada pelo mCAC ou pelo entusiasmo.

## Rodada 6b — fatia vs bolo: o share sozinho engana

**Pergunta (André):** "vale mais um pedaço de um bolo grande do que um bolo pequeno inteiro?"
Decomposição `log(BP) = log(SoS) + log(categoria)`, 48 meses. Script:
[sos_decomposicao_bolo.py](scripts/sos_decomposicao_bolo.py).

**O episódio recente prova o ponto.** O SoS-mídias saltou de 7,6% para 12,2% nas últimas 4 semanas
— e **não foi a BP que cresceu, foi o bolo que encolheu**:

| Série (índice Trends, escala encadeada) | Histórico 5a | Últimas 4 sem | Δ |
|---|---:|---:|---:|
| Busca BP | 0,61 | 0,47 | **−24%** |
| Bolo mídias (BP + 4 concorrentes) | 9,41 | 3,84 | **−59%** |
| — Jovem Pan | 5,08 | 1,93 | −62% |
| — O Antagonista | 1,68 | 0,48 | −71% |
| — Revista Oeste | 1,04 | 0,48 | −54% |
| — Gazeta do Povo | 1,00 | 0,48 | −52% |
| **SoS mídias** | **7,6%** | **12,2%** | **+61%** |

Fatia recorde com busca própria em queda. Lido sozinho, o 12,2% seria uma boa notícia falsa.

**Decomposição de variância (MoM):** na categoria mídias, 72% da variação da busca BP vem da fatia
e 28% do bolo, com correlação **negativa** entre os dois (−0,33) — quando a categoria cai, nossa
fatia sobe mecanicamente. Na categoria "todos" a fatia explica ~100% porque os streamings dominam
o bolo e a BP é 0,66% dele — o share vira quase a própria busca BP reescalada.

**Mas é a fatia, não o bolo, que anda com vendas** (contemporâneo, z vs MM12, controlado por spend):

| Componente | × transações | × CAC | × ticket |
|---|---:|---:|---:|
| Fatia: SoS todos | **+0,58\*** | **−0,53\*** | −0,50* |
| Busca BP (fatia × bolo) | +0,49* | −0,58* | −0,44* |
| Fatia: SoS mídias | +0,48* | −0,47* | −0,53* |
| Bolo: categoria todos | −0,28 | +0,13 | +0,24 |
| Bolo: categoria mídias | +0,01 | +0,07 | +0,18 |

**Conclusão:** o share carrega o sinal coincidente (o bolo não), **mas o nível do share não pode ser
lido sozinho** — precisa vir sempre acompanhado do tamanho do bolo e da busca absoluta da BP. Um
relatório de SoS tem três linhas obrigatórias: fatia, bolo, fatia×bolo. Hoje elas dizem coisas
opostas (fatia recorde, bolo e BP em queda), e é exatamente esse desencontro que importa.

⚠️ Trends é índice relativo: o "bolo" aqui é o índice da categoria na nossa escala encadeada, não
volume absoluto de buscas. Volume absoluto exige Keyword Planner ou Search Console (Fase 2 do plano).

## Métrica proposta

Duas, uma para cada pergunta.

### (a) Termômetro diário: sessões de YouTube orgânico (GA4 Organic Video)

O indicador de relevância com sinal limpo em volume **e** eficiência. Lido como desvio da média
móvel de 28 dias, dentro da faixa de spend corrente. Dias no topo entregam +25% de transações e
CAC ~12% menor com o mesmo dinheiro. **Não substituir por engajamento de rede social** — esse
anda com a mídia e, condicionado a ela, anda contra a eficiência.

Uso operacional: se a audiência orgânica no YouTube está alta e o CAC ainda não caiu, há espaço
para escalar; se está baixa, escalar tende a sair mais caro que o mCAC de referência
(R$145 LAN / R$188 PPT — `metricas-referencia.md`).

### (b) IAC-14 por playlist

`queries/15_iac_ranking_playlists.sql`, lida mensalmente:

> Entre membros de engajamento leve/médio sem compra nos 60 dias anteriores, receita por
> pessoa-dia nos 14 dias seguintes ao consumo, dividida pela mediana do catálogo.

Por que essa e não o "índice de relevância orgânica" do plano original: o IRO (direct + busca
de marca + leads orgânicos) **não detectou as sabatinas** e é confundido por spend — anúncios
geram busca de marca. O IAC mede o que interessa (conteúdo → venda), tem denominador honesto
(pessoa-dia, não impressão) e é acionável: diz qual conteúdo pautar para a base morna.

Leitura operacional: IAC > 2 = conteúdo que ativa; IAC < 0,5 = conteúdo de retenção/marca, não
de venda. Não usar para comparar conteúdo com oferta associada vs editorial puro — são ligas
diferentes (Clube do Livro 9,7× é funil de produto, não ativação).

## Pendências / próximos passos

1. **Fechar a atribuição do efeito**: sabatina (1,98×) vs BP Entrevista (2,70×) sugere que é o
   formato, não a relevância eleitoral. Teste: comparar sabatinas *entre si* por notoriedade do
   entrevistado (Marçal/Renan vs Derrite/Caroline de Toni) — se o lift não escala com a
   notoriedade, é formato.
2. **Efeito de médio prazo**: a janela D+14 pode ser curta demais. Não-membro converte em ~421
   dias (`regras-negocio.md`) — o lift de aquisição, se existir, não aparece em 14 dias.
3. **YouTube Analytics**: a sabatina acontece no YouTube; views/inscritos ficam fora do BQ e do
   GA4. Sem isso, o lado "atenção" da medição é parcial. Pedir acesso ao YT Analytics.
4. **Freemium negativo** (0,28–0,83×) é direcionalmente consistente em 3 estratos mas n pequeno
   (102–486 pessoa-dias). Vale reconferir em 2–3 meses com mais volume.
5. ✅ (02/09/2026) Publicado como relatório HTML no portal (seção Mídia Paga, badge Snapshot). O acompanhamento recorrente do IAC segue em aberto (Fase 3 do plano).

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [01_vendas_diarias_agosto_youtube.sql](queries/01_vendas_diarias_agosto_youtube.sql) | Datar as sabatinas por vendas/atribuição YT | ✅ |
| [02_serie_vendas_diaria.sql](queries/02_serie_vendas_diaria.sql) | Série diária de vendas por canal (385 dias) | ✅ |
| [03_spend_diario.sql](queries/03_spend_diario.sql) | Spend diário Meta+Google+PMax | ✅ |
| [04_zenvia_diario.sql](queries/04_zenvia_diario.sql) | Abordagens Comercial/dia (esforço) | ✅ |
| [05_leads_diario.sql](queries/05_leads_diario.sql) | Leads pagos vs orgânicos/dia | ✅ |
| [06_campanhas_periodos.sql](queries/06_campanhas_periodos.sql) | Fases de campanha (dummies) | ✅ |
| [07_spend_por_campanha_agosto.sql](queries/07_spend_por_campanha_agosto.sql) | O que puxou o spend nas janelas | ✅ |
| [08_cpa_intra_campanha.sql](queries/08_cpa_intra_campanha.sql) | CPA/ROAS intra-campanha (controla mix) | ✅ |
| [09_viewers_eleicoes_perfil.sql](queries/09_viewers_eleicoes_perfil.sql) | Viewers da playlist por mídia/dia | ✅ |
| [10_adesao_freemium_sabatina.sql](queries/10_adesao_freemium_sabatina.sql) | 1ª versão (coorte freemium) — superada | ✅ |
| [11_adesao_pessoa_dia.sql](queries/11_adesao_pessoa_dia.sql) | v2 pessoa-dia — tinha causalidade reversa | ✅ |
| [12_adesao_placebo_playlists.sql](queries/12_adesao_placebo_playlists.sql) | v3 com placebo de playlist + D+1..D+14 | ✅ |
| [13_pretendencia_selecao.sql](queries/13_pretendencia_selecao.sql) | Teste de seleção (pré-tendência) | ✅ |
| [14_adesao_condicionado.sql](queries/14_adesao_condicionado.sql) | **Teste final** (sem compra 60d) | ✅ |
| [15_iac_ranking_playlists.sql](queries/15_iac_ranking_playlists.sql) | **Métrica IAC** — ranking de 172 playlists | ✅ |
| [16_portal_diario.sql](queries/16_portal_diario.sql) | Portal Mixpanel por origem | ✅ (série curta, fora da análise) |

Scripts:
- [event_study.py](scripts/event_study.py) — painel diário, contrafactual e placebo (rodada 1)
- [detectar_picos.py](scripts/detectar_picos.py) — IRO e picos históricos de atenção
- [relevancia_vs_vendas.py](scripts/relevancia_vs_vendas.py) — correlação bruta vs parcial, lags, direção, semanal + Trends
- [quantificar_relevancia.py](scripts/quantificar_relevancia.py) — quartis de relevância em termos de negócio
- [teste_pareado_spend.py](scripts/teste_pareado_spend.py) — **teste decisivo** (pareamento por spend × DOW × fase)

## Referências metodológicas

> **Bibliografia completa e comentada: [REFERENCIAS.md](REFERENCIAS.md)** — inclui share of search (IPA/Hankins), nowcasting (Choi & Varian), Wikipedia como proxy de atenção (Moat/Preis) e brand equity em MMM (Cain).

- Brodersen et al. (2015), *Inferring causal impact using Bayesian structural time-series models*
  — desenho de contrafactual com covariáveis. Aqui implementado como OLS + placebo (série curta:
  spend só desde ago/2025 não sustenta BSTS com prior de sazonalidade anual).
- MacKinlay (1997), *Event Studies* — janela de evento vs janela de estimação, p bicaudal.
- Lewis & Rao (2015), *The Unfavorable Economics of Measuring the Returns to Advertising* —
  justifica o placebo e o reporte por intervalo. Confirmado na prática: n=2 não detecta nada.
- Binet (IPA EffWorks 2020), *Share of Search* — motivou usar busca de marca como núcleo do IRO;
  descartada como métrica primária por confundimento com spend.
- Blake, Nosko & Tadelis (2015) — busca de marca não é incrementalidade automática.

## Wiki atualizada

- `wiki-bp/pages/metricas-referencia.md` — nova seção "Ativação por conteúdo (IAC-14)".
- `wiki-brasil-paralelo/pages/relevancia-marca.md` — criada, achados de relevância/ativação.
- `wiki-bp/pages/bq-regras.md` — gotcha de causalidade reversa em análise conteúdo→venda.
