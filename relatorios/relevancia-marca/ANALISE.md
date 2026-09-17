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

> ⚠️ **Auditoria 14/09/2026 (rodada 9a, abaixo):** quatro frases desta seção estão mais fortes do
> que o dado permite — "freemium nulo / não usar como topo de funil" (é ausência de evidência,
> MDE ≥1,6–1,9×), "médio 1,44× p<0,005" (p=0,02 com cluster por pessoa), "estreia tardia zera"
> (D+7, 2 sabatinas) e "com o mesmo dinheiro +24,7% e CAC −11,9%" (um fato, spend não pareia
> perfeitamente, mix de campanha solto). O núcleo (membro leve 1,65× [1,22–2,23]; volume do YT
> orgânico) sobrevive. Correções ao texto publicado aguardam decisão do André.

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

## Rodada 7 — testes de setembro (02/09/2026, executados em paralelo por 3 agentes)

Relatórios completos: [TESTE_A_FORMATO_VS_PAUTA.md](TESTE_A_FORMATO_VS_PAUTA.md) ·
[TESTE_B_MEDIO_PRAZO.md](TESTE_B_MEDIO_PRAZO.md) · [TESTE_C_GA4_NEWUSERS.md](TESTE_C_GA4_NEWUSERS.md)

### Teste A — o lift é do formato, não da pauta eleitoral

**Descoberta que muda a premissa:** Renan e Marçal só entraram na plataforma em **19/08** (as
lives de 14 e 17/08 foram no YouTube) — o IAC 1,98× da playlist foi medido **sem nenhum
pessoa-dia deles** (cobre 7 sabatinas, não 9).

- Lift por sabatina (D+14, controle top-8 pareado por dia): Zema **2,06×***, Aldo Rebelo
  **1,78×***, Caiado **1,69×***, Salles 1,53× ns, Cury 1,22× ns, de Toni 0,99× ns, Derrite
  0,93× ns. No D+7: **Marçal 0,81× ns e Renan 0,48× ns** — os dois nomes de maior projeção são
  os únicos sem lift.
- ALTA vs BAIXA notoriedade (pooled): 0,70 [0,30–1,15] vs 1,65 [1,34–1,95], p=0,001 — direção
  **oposta** à hipótese da pauta. Sensibilidades (Zema/Salles como ALTA): ns.
- **Régua de formato:** sabatinas pooled D+14 **1,61×** = top-5 BP Entrevista **1,61×** (p=0,95).
  O 2,70× vs 1,98× do IAC era razão de receita sensível a cauda; em taxa de conversão pareada
  **os formatos empatam**.
- **Veredito: é FORMATO** (condição pré-registrada satisfeita). Caveat: o grupo ALTA-puro está
  confundido pela estreia tardia (audiência = replay frio pós-YouTube) e janela D+7.
- ⚠️ **Achado operacional novo:** publicar a sabatina na plataforma dias depois da live no
  YouTube **zerou a ativação** — o timing da estreia importa mais que a notoriedade do
  entrevistado.

### Teste B — incremento real, não pull-forward; freemium nulo até D+60

Universo único com follow-up completo (6 sabatinas de jun–jul; última data íntegra de
`fct_transactions` = 01/09; **D+90 infactível até ~05/10**):

| Estrato | D+14 | D+30 | D+60 | razão D+60/D+14 |
|---|---|---|---|---|
| Membro leve | 1,64× [1,21–2,23] | 1,56× | **1,64× [1,35–1,99]** | **1,00** |
| Membro médio | 1,30× | 1,31× | 1,26× [1,09–1,47] | 0,97 |
| Heavy | 0,84× ns | 0,99× ns | 0,97× ns | — |
| Freemium | 1,15× ns | 1,41× ns | 1,13× ns | 0,99 |

O lift do leve **não decai** e a diferença absoluta **cresce** (+0,93pp → +2,23pp; receita extra
R$ 20 → R$ 54/pessoa-dia) — o oposto do que pull-forward prevê. **Freemium segue nulo até
D+60**: alongar a janela não revelou lift de aquisição. A leitura "sabatina ativa a base morna"
sai fortalecida. ICs de janela longa são anti-conservadores (autocorrelação de pessoa-dias).

### Teste C — GA4 newUsers: passa no crivo, mas não é sinal novo (descartado)

newUsers por canal correlaciona 0,95–0,99 com as sessões do mesmo canal — é a mesma série.
Organic Video empata com sessões YT (+0,268/−0,156 vs +0,265/−0,143), busca fica levemente
pior; TOTAL (ρ spend 0,79) e Social (0,83) **medem orçamento**. Razão conceitual: "novo" no GA4
é **cookie novo, não pessoa nova** (64% do Direct conta como "novo") — o filtro de "membro
voltando" que o newUsers prometia não existe. **Painel diário inalterado** (sessões YT orgânico
+ busca orgânica + Wikipedia); newUsers Organic Video registrado como substituto se a série de
sessões quebrar.

## Rodada 8 — revisão pedida pela Bárbara (11/09/2026): lançamentos e fechamento de lote

**Pedido (thread do Luan/Bárbara):** (a) deixar a conclusão mais didática — dois parágrafos;
(b) checar se os dias de YT orgânico alto batem com **fechamento de lote**; (c) refazer o
+24,7% **excluindo os docs de lançamento** (El Salvador, Vida dos Santos etc.), porque grande
parte dos dias altos vem de estreia.

**Método:** mesmo teste pareado da rodada 2, com calendário **corrigido** da wiki
(o `campanhas_periodos.csv` da `tb_campaign_period` não tem DOM/ELS/CDL/EVG/ODI/ENE — a dummy
`em_venda` original não cobria abr–jul/2026). Janela de lançamento = venda_start ±3d (21
campanhas, 124 dias); fechamento de lote = venda_end −2..0 (39 dias).
Script: [teste_pareado_sem_lancamento.py](scripts/teste_pareado_sem_lancamento.py) · saída em
`data/teste_pareado_sem_lancamento.txt`.

**Diagnóstico de sobreposição:** dos dias de YT orgânico ALTO, **37,8% são janela de
lançamento** (vs 26,9% dos baixos) — a Bárbara estava certa. Fechamento de lote: 11,2% vs 9,1%
— não é confundidor. No top-15 de dias: BMA (23 e 20/02), PAP/sabatina Renan (14/08), TLR
(16/09), BNO25 (01/11), CDL+ELS (20/05).

| Variante | n dias | Transações | CAC ads | Conv/1k sessões | Spend pareou? |
|---|---:|---:|---:|---:|---|
| Baseline (fases corrigidas) | 385 | **+25,6%*** | −10,9%*** | +21,7%*** | +3,7% (p=0,08) |
| **Sem lançamentos** (venda_start ±3d) | 261 | **+18,9%*** [+9,9, +31,2] | −6,8% (p=0,051) | **+2,2% ns** | +3,9% ns |
| Sem fechamento de lote | 346 | +27,8%*** | −13,6%*** | +23,8%*** | +4,2% (p=0,06) |
| Sem ambos | 239 | +20,9%*** | −6,4% (p=0,10) | +3,9% ns | +5,4% (p=0,047) |

**Conclusões da rodada:**
1. **Fechamento de lote não explica os picos** — quase não coincide com dias altos e, excluído,
   o efeito até sobe.
2. **O sinal de conversão ("porta mais aberta") é fenômeno de lançamento.** Fora das janelas de
   estreia, transações ainda sobem +18,9% (p<0,001) mas conv/sessão zera (+2,2% ns) e o CAC
   enfraquece para −6,8% (p=0,05, IC toca zero). A estreia do doc no YouTube gera simultaneamente
   o pico de Organic Video e o pico de venda — era o confundidor "lançamento bom" da ressalva,
   agora quantificado.
3. **Leitura revisada do termômetro:** YT orgânico alto fora de lançamento ainda marca dia de
   mais volume de vendas, mas não sustenta mais a leitura de "resistência menor / mesma visita
   converte melhor" como fenômeno cotidiano. A frase "com o mesmo orçamento, +24,7% de transações
   e CAC −11,9%" só vale com lançamentos incluídos.
4. ⚠️ Caveat: a exclusão remove 124 de 385 dias (32%) e o pareamento de spend degrada um pouco
   nas variantes menores (+3,9% a +5,4%) — parte do +18,9% residual pode ser spend. Fechamentos
   de lote intermediários (dentro da janela de venda) não estão no calendário; só o fim da venda
   foi testado.
5. Relatório atualizado: conclusão em 2 parágrafos na aba "Resposta ao pedido" + flags de
   revisão nas duas abas.

## Rodada 9a — auditoria das rodadas 1–8 (14/09/2026)

**Por quê:** pedido da Bárbara/Luan (14/09, #squad-cac) para refinar a análise com os cases
sabatinas e 11 de Setembro. Antes de rodar análise nova, passada adversarial no `ANALISE.md`,
nos `TESTE_*.md`, nos scripts e nos dados: 11 pontos cegos suspeitos + o que mais aparecesse.
Tudo recomputado está em [scripts/auditoria_r9a.py](scripts/auditoria_r9a.py) (saída
`data/r9a_auditoria.txt`) e nas queries [27](queries/27_cluster_robusto_q14.sql),
[28](queries/28_cluster_robusto_q25.sql), [29](queries/29_spend_google_video_diario.sql).
Integridade: `fct_transactions` aprovadas fechadas até **13/09/2026** (14/09 parcial).

**Resumo em uma linha:** o núcleo sobrevive (membro leve 1,65× e o sinal de volume do YouTube
orgânico), mas **quatro conclusões publicadas estão mais fortes do que o dado permite** —
"freemium nulo → não usar como topo de funil", "membro médio 1,44× (p<0,005)", "estreia tardia
zera a ativação" e "com o mesmo dinheiro, +24,7% e CAC −11,9%" — e o relatório responde a uma
pergunta diferente da que a Bárbara está fazendo. Ordenado por quanto muda a conclusão:

### 1. O desenho individual não responde "o vídeo no YouTube vendeu?" — CONFIRMADO (muda a moldura)

Checado: toda a máquina pessoa-dia (queries 11–15, 22–26) parte de `obt_kafka__view_sessions`,
isto é, **consumo na plataforma**. O lado YouTube tem só duas pontes no warehouse: sessões
`Organic Video` do GA4 (chegadas ao site, mediana 767/dia) e transações com
`nm_pptc_tracking_publisher = 'YouTube'` (mediana **13/dia, ~1% das transações**; 23 em 13/09,
máximo de setembro). Nenhuma métrica de views/retenção/inscritos existe (verificado de novo:
`datamart`, `dbt_abe`, GA4).

- **Efeito prático:** o que está publicado responde "quem assiste na plataforma compra mais nos
  14 dias seguintes?" (sim, membro leve). **Não** responde "o vídeo no YouTube gerou venda?".
  As sabatinas Renan/Marçal ilustram: 1.822 e 3.995 pessoas na plataforma contra uma live no
  YouTube de ordem de grandeza maior — o pessoa-dia mede a cauda que entrou, não a audiência.
- A resposta curta e a aba "Resposta ao pedido" do relatório precisam abrir com essa fronteira.
  Para a rodada 9b, o bloco "impacto relacionável" da Bárbara só fecha com YouTube Studio
  (item 0 da semana) + UTM/CTA; sem isso, entregar plataforma + GA4 + UTM com o gap no topo.

### 2. "Freemium nulo → não distribuir como topo de funil" — CONFIRMADO: é ausência de evidência

Efeito mínimo detectável (80% de poder, α 5%) dos testes em que o "nulo" se apoia:

| Teste | n tratado | lift observado [IC95] | **só detectaria lift ≥** |
|---|---:|---|---:|
| Q14 freemium leve | 486 | 0,83× [0,41–1,66] | **1,91×** |
| Q14 freemium médio | 363 | 0,58× [0,26–1,30] | 1,88× |
| Q14 freemium heavy | 102 | 0,28× [0,04–1,99] | 2,49× |
| Teste B freemium D+14 | 558 | 1,15× [0,60–2,21] | 2,00× |
| Teste B freemium D+60 | 558 | 1,13× [0,77–1,66] | 1,58× |

O efeito de referência do membro leve (**1,65×**) está **dentro** de todos esses ICs e abaixo
do MDE de quase todos. Os point estimates oscilam de 0,28–0,83× (Q14) para 1,13–1,41× (Teste B)
— assinatura de ruído, não de efeito negativo. **Efeito prático:** trocar "nulo / zero / nada"
por "sem evidência; o teste só excluiria lift acima de ~1,6–1,9×". A recomendação "não usar
sabatina como topo de funil" **não é sustentada pelos dados** (nem refutada) — vira "sem base
para recomendar nem para vetar; exige n ≥ ~2.500 pessoa-dias freemium". Aparece em: ANALISE
(resposta curta, §3, Teste B), `index.html` (linhas ~188, 261, 527, 546), wiki
`relevancia-marca.md` e `metricas-referencia.md`.

### 3. Erro-padrão com pessoa-dia repetida — CONFIRMADO PARCIALMENTE: leve sobrevive, médio fica frágil

Queries 27/28 agregam a máquina da query 14 e do Teste B por **pessoa** e calculam a variância
robusta (cluster = e-mail). Design effect: tratado leve 1,23 (1,14 pessoa-dias por pessoa),
médio 1,97, heavy 1,6; controles 1,3–4,7 (heavy repete muito).

| Estrato (Q14, D+14) | lift | IC naive · p | **IC robusto · p** |
|---|---:|---|---|
| Membro leve | 1,65× | [1,26–2,17] · 0,0003 | **[1,22–2,23] · 0,001** |
| Membro médio | 1,44× | [1,16–1,80] · 0,001 | **[1,06–1,96] · 0,021** |
| Heavy / freemium | 0,28–0,87× | ns | ns |

Teste B (janelas longas): leve resiste em todas (D+60 **1,65× [1,32–2,04]**, p<0,0001); médio
vira **ns em D+14 (p=0,16) e D+30 (p=0,08)** e fica no limite em D+60 (1,27× [1,01–1,60],
p=0,044). **Efeito prático:** "1,4–1,65× com p<0,005" → "leve 1,65× [1,2–2,2], sólido; médio
1,44× [1,06–1,96], frágil". O achado principal sobrevive.

### 4. "Estreia tardia zera a ativação" — NÃO LISTADO, rebaixar para provisório

Apoia-se em Renan+Marçal pooled D+7: **0,70× [0,30–1,15]**, MDE 1,82×; individualmente
Marçal 0,81× [0,25–1,45] (MDE 1,98×) e Renan 0,48× [0,00–1,16] (MDE 2,39×) — 7 e 2 compradores.
O IC pooled exclui 1,65 por pouco e a janela é D+7. Está na wiki como "gotcha central" e no
relatório como regra ("desde que o conteúdo entre na plataforma no dia da live"). **Agora dá para
fechar D+14 e D+30 dos dois** (transações íntegras até 13/09) — é o item mais barato da 9b e
pode confirmar ou derrubar a regra. Até lá: "indício, D+7, n pequeno".

### 5. "+24,7% E CAC −11,9% com o mesmo dinheiro" — P2 CONFIRMADO (um fato), P7 CONFIRMADO (mix solto)

**P2 — volume e eficiência não são duas evidências.** Com spend pareado, `tx_ads` +20,7%
[+13,8, +29,1] e CAC −10,9% [−15,7, −4,8] são a mesma coisa (CAC implícito
(1+Δspend)/(1+Δtx_ads) = −14,1%). A evidência **independente** é outra: as transações **não
atribuídas a ads** subiram **+27,9%** [+18,9, +41,3] — mais que as de ads — e o Comercial
+14,6%. Reescrever: "um fato lido de dois ângulos; o que é independente é que o efeito é maior
fora da mídia".

**P7 — o pareamento controla fase, não mix.** Campanha Meta dominante do dia vs alta/baixa de
YT orgânico, na mesma estratificação do teste:

| Campanha dominante | dias | % dias "alta" |
|---|---:|---:|
| BP10 | 27 | **7%** (2 de 27) |
| PAP | 16 | 6% |
| DOM | 12 | 25% |
| 10R / GOD / TLR / BNO25 | 122 / 25 / 14 / 30 | 55–57% |
| ELS / CDL | 32 / 19 | 62–63% |
| SDC | 16 | **100%** |

O mix está fortemente associado ao lado do corte — e **BP10, o case da Bárbara, é a campanha
cujos dias quase nunca são "alta" de YouTube** (é exatamente o que ela viu: "Google teve o pior
desempenho"). Reestratificando por campanha dominante × fds × lançamento: transações +26,5%
[+16,5, +41,3] e CAC −8,1% [−12,6, −2,7] **mas o spend não pareia** (+18,1%, p<0,001); com
tercil de spend dentro da campanha (95 dias): +33,2% / CAC −11,1% / spend +8,2% (p=0,07).
**Efeito prático:** a direção é robusta a mix; a frase "com o mesmo orçamento" não é — trocar por
"dias de YT alto têm ~20–30% mais transações e CAC 6–11% menor; a igualdade de spend não é
garantida (pareamento entre +3,7% e +8%)". Registrar também que a rodada 2 publicada ("spend
pareou +0,4%") usou a dummy `em_venda` incompleta; com fases corrigidas o pareamento já era
+3,7% (p=0,08).

### 6. Multiplicidade e o topo do IAC — CONFIRMADO para o IAC; parcial para o resto

~130 p-valores/estrelas reportados nos 4 documentos, mais 172 playlists ranqueadas e 1.069
eventos de mCAC. Correção de Bonferroni por família:
- Teste principal (6 contrastes, α 0,0083): leve passa (p 0,001 robusto); **médio não passa**
  (0,021). Teste A por sabatina (7, α 0,007): Zema, Caiado (<0,001) e Rebelo (0,003) passam.
  Pareado YT (p<0,001) passa qualquer correção.
- **Não sobrevivem a correção nenhuma** e devem ser lidos como exploratórios: mCAC −10% em
  `[VENDA]`-up (p=0,028, IC cruza zero), `[LEAD]` +53% (p=0,04/0,12), CAC −6,8% sem lançamento
  (p=0,05), Trends semanal (já rebaixado).
- **IAC:** o n mínimo é 500 pessoa-dias, não compradores. **53% das 172 playlists têm <30
  compradores; 19 têm <10.** O topo é selecionado por cauda de receita: *Os Falsários* (rank 3,
  IAC 7,09×) tem **10 compradores** e é rank **110** por taxa de conversão; *Miss Potter* rank
  12 → 145; *Entre Facas e Segredos* 4 → 71. `BP nas Eleições` (21 por taxa vs 22 por RPP) e
  `BP Entrevista` (13 vs 14) são estáveis. **Efeito prático:** IAC precisa de (a) n mínimo de
  **compradores** (≥30), (b) versão por taxa de conversão com IC ao lado do RPP, (c) aviso de que
  o ranking por RPP não distingue as posições 3–20. A query 15 deve ganhar essas colunas antes
  de qualquer uso mensal.

### 7. Potência para n=1 evento (11 de Setembro) — CONFIRMADO, declarar antes de rodar

| Desenho | o que detecta (80% poder) |
|---|---|
| Event study diário, janela 3d (rodada 1) | receita ≥ **+62%** (p95 placebo; MDE 80% ≈ +114%); transações ≥ +34%; CAC ≤ −26% |
| Pessoa-dia, 1.757 usuários → ~966 pd membro leve/médio, D+7 | lift ≥ **2,06×** |
| idem, D+14 | lift ≥ **1,76×** (acima do 1,65× de referência) |
| idem, D+60 | lift ≥ 1,48× |
| só membro leve (~527 pd), D+14 | lift ≥ 2,02× |

**Um "não significativo" do 11 de Setembro na sexta é garantido por construção** (D+7, n pequeno)
e não pode ser reportado como "o vídeo não teve efeito". Reportar sempre IC + MDE; a resposta
honesta em 18/09 é "compatível com 0,5× a 2×", e o D+14 (21/09) ainda só detecta ≥1,76×.

### 8. Três eventos na mesma janela — CONFIRMADO; o dia não separa, a pessoa separa em parte

Calendário real levantado (Meta + `fct_transactions`, 03→13/09): spend BP10 **R$ 49k → R$ 255k**
(vendas Meta BP10 102 → 444); transações com UTM BP10 **163 → 585** (20% → 38% do total);
Technocracia spend R$ 2k → 22k, vendas 0–12/dia; estreia do 11 de Setembro na plataforma 07/09
(tx publisher YouTube no dia: 7). A receita do fim de semana 12–13/09 (R$ 846k / 967k) acompanha
a escalada de BP10. **O teste diário não separa os três** (item 7). O que separa:
(i) pessoa-dia dos viewers do 11 de Setembro vs top-8 **no mesmo calendário** (mesmos dias de
BP10 para tratados e controle — isola "assistiu" de "era dia de fechamento"), com o MDE do item
7 declarado; (ii) decomposição das transações do fim de semana por UTM/publisher (BP10 / TEC /
YouTube / orgânico / CRM) contra o mesmo fim de semana anterior — descritivo, responde "quanto
é rastreável"; (iii) a hipótese da Bárbara ("todo o efeito é BP10") é testável assim: se as
transações **sem** UTM BP10 não subiram mais que a MM28 pareada por spend, ela está certa.

### 9. Indicador coincidente usado como gatilho — DERRUBADO EM PARTE (a favor do uso)

A premissa "lag ≥1 é nulo" valia para **inovações** (resíduos), não para o **nível**: a série é
persistente (ρ lag-1 do resíduo de YT orgânico **0,68**; P(alta hoje | alta ontem) = 75,5% vs
48,8% na base). Em nível, pareado por spend de hoje: **YT de ontem** → transações hoje +16,3%
[+9,2, +25,6], CAC −7,7% [−13,0, −1,5] (p=0,017); **sem dias de lançamento (dia e véspera):
+23,0% / CAC −10,6% [−16,3, −3,3] (p=0,002)**. A regra operacional "YT ontem > 1,3× MM28"
marca 67/356 dias e nesses dias o CAC de hoje sai −16,2% (−19,4% sem lançamento), com spend
igual. **Efeito prático:** a recomendação "se o YT orgânico está alto, há espaço" é **mais**
defensável do que o texto dizia — a informação de ontem está disponível hoje. Corrigir a frase
"lag ≥1 nulo nas duas direções" → "as inovações não se antecedem, mas o nível é persistente".
Segue sem prova de que **escalar** nesses dias baixa o mCAC (rodada 3: −10%, IC [−36%, +22%]).

### 10. Seleção dos cases por percepção — CONFIRMADO, sem efeito no publicado

"Sucesso no YouTube" nunca foi medido; todos os rankings são de consumo na plataforma. Proxy
disponível: dias de `Organic Video` alto (14/08, Renan, está no top-15 do ano) e `tx` com
publisher YouTube. Para o 11 de Setembro, o GA4 de setembro ainda não foi puxado (9b).

### 11. Contaminação de vídeo pago no Organic Video — DERRUBADO

Spend Google `[YT]` (43% do Google, 4,7% do total; query 29): ρ com Organic Video **−0,066**
(ns); com views pagas `[YT]` −0,077; com sessões GA4 `Paid Video` −0,069. Dias "alta" têm spend
de vídeo **13% menor** que dias "baixa". Adicionando tercil de spend de vídeo ao estrato:
transações +20,6% [+13,1, +32,3], conversão/sessão +22,7%, CAC −5,6% (p=0,10), spend de vídeo
−1,6%. O termômetro **não** mede orçamento de vídeo.

### Não listados

- **Remarketing fora do CAC (a favor).** `tx_ads` = FB Ads + Adwords; exclui `Adwords
  Remarketing` + `Instagram Ads` (7,4% das tx de ads). O share deles sobe nos dias alta (9,3% vs
  5,0%); com denominador completo o CAC sai **−15,2%** [−20,0, −9,3] em vez de −10,9%.
  O número publicado é conservador.
- **Dias autocorrelacionados no bootstrap.** ρ lag-1 dos resíduos: transações 0,47, CAC 0,60.
  n efetivo ≈ **140 de 385 dias**. Os p<0,001 do pareado YT sobrevivem; qualquer p entre 0,01 e
  0,10 nos testes diários (CAC −6,8%, mCAC −10%, spend "pareou" p=0,07) não deve ser lido como
  significativo.
- **Comparador do IAC/Q14 sem pareamento de calendário** — já tratado no Teste B (1,65× → 1,64×
  pareado); não muda nada, mas a query 15 mensal herda o problema.

### O que muda no que está publicado (proposta — aguardando André)

| Onde | Hoje | Proposta |
|---|---|---|
| ANALISE resposta curta · `index.html` ~188/527/546 · wiki | "freemium nulo / zero / nada" | "sem evidência (IC até 1,7–2,0×; MDE ≥1,6–1,9×)" |
| ANALISE · `index.html` ~261/527 · wiki | "não usar sabatina como topo de funil" | "sem base para recomendar nem vetar; testar com n ≥ 2.500 pd freemium" |
| ANALISE §3 · wiki · metricas-referencia | "médio 1,44× (p=0,002)" | "médio 1,44× [1,06–1,96], p=0,02 (cluster por pessoa); frágil" |
| ANALISE Teste A · wiki ("gotcha central") · `index.html` ~527 | "estreia tardia zera a ativação" | "indício (D+7, 0,70× [0,30–1,15]); fechar D+14/30 na 9b" |
| ANALISE rodada 2 · `index.html` ~533 · wiki · metricas-referencia | "com o mesmo spend, +24,7% E CAC −11,9%" | "um fato (tx de ads +21%); tx fora de mídia +28%; spend pareia entre +3,7% e +8%; mix de campanha não balanceado" |
| ANALISE rodada 2 · wiki | "lag ≥1 nulo nas duas direções" | "inovações não se antecedem; nível persistente — YT ontem prediz CAC hoje (−8 a −11%)" |
| IAC (query 15, metricas-referencia) | ranking por RPP, n≥500 pd | + n≥30 compradores, taxa com IC; topo 3–20 indistinguível |
| Rodada 3 / 8 | mCAC −10%, CAC −6,8% "p=0,05" | exploratórios; n efetivo ~140 dias |

### Adendo 16/09 — "sucesso no YouTube" medido pela primeira vez (Data API v3, chave da Bárbara)

Views públicas acumuladas em 16/09 (`data/yt_videos_publico.csv`, script
`BigQuery/youtube-analytics/fetch_youtube_public.py`). Muda dois fatos dos cases:

| Vídeo (YouTube) | Data | Views | Nota |
|---|---|---:|---|
| **PABLO MARÇAL \| BP NAS ELEIÇÕES** (live) | 17/08 | **833.641** | 9º maior do canal desde junho; + cortes de 348k, 210k, 73k |
| **RENAN SANTOS \| BP NAS ELEIÇÕES** (live) | 14/08 | **380.434** | |
| AUGUSTO CURY \| BP NAS ELEIÇÕES | 28/06 | 53.730 | |
| RONALDO CAIADO / ROMEU ZEMA / RICARDO SALLES / ALDO REBELO / DERRITE | jun | 47.674 / 40.135 / 16.349 / 12.922 / 9.028 | |
| **25 ANOS DO 11 DE SETEMBRO** (live) | **10/09** | **2.981.782** | 3º maior do canal desde junho |
| MASTER X STF EXPLICADO EM 20 MINUTOS (live) | 03/09 | 4.351.851 | maior do período |
| AO VIVO: STF JULGA … MORAES (live) | 15/09 | 3.532.532 | |

1. **Ponto 9 fecha:** a notoriedade no YouTube é o inverso do lift na plataforma. Marçal e Renan
   têm 10–90× as views das sabatinas de junho e são as duas **sem** lift medido; Zema, Rebelo e
   Caiado, com 9–48 mil views, têm os maiores lifts. A leitura "é formato, não fama" ganha o dado
   que faltava — com a ressalva de que o lift deles é D+7 e n pequeno (item 4 da auditoria).
2. **O case "11 de Setembro" no YouTube é a live de 10/09 (quinta), não a estreia de 07/09 na
   plataforma.** São dois eventos: doc na plataforma 07/09 (1.757 usuários) e live no YouTube
   10/09 (2,98M views). Receita de 10/09: R$ 822k vs R$ 673k na véspera (+22%), com spend BP10
   +16% no dia. O desenho da 9b precisa tratar os dois separadamente; o pareado diário de 10/09
   segue sem potência (item 7), mas o pessoa-dia da plataforma pode usar 07/09 e 10/09 como duas
   exposições distintas.
3. ⚠️ Views são **acumuladas até a consulta** — vídeos mais antigos tiveram mais tempo. Para série
   diária real (views/dia, retenção, origem, cliques em tela final) continua faltando a Analytics
   API, que a chave não abre (401). Caminho: convite de Visualizador ou consentimento OAuth de um
   gestor do canal (`youtube-analytics/README.md`).

### Implicação para a rodada 9b

1. **Item 0 continua sendo o acesso ao YouTube Studio** — sem ele, o bloco "impacto relacionável"
   da Bárbara é parcial e isso vai no topo da entrega.
2. **Mais barato e mais informativo:** D+14/D+30 de Renan e Marçal (queries 22/25 com cutoff
   13/09) — decide o item 4 e responde direto "os vídeos de mais sucesso vendem (na plataforma)?".
3. **11 de Setembro:** pessoa-dia com calendário pareado + decomposição por UTM do fim de semana;
   **reportar MDE junto** (D+7 ≥2,06×; D+14 ≥1,76×).
4. **Teste da hipótese da Bárbara:** transações sem UTM BP10 vs MM28 pareada por spend nos dias
   05–07/09 e 12–13/09.
5. Não gastar tempo em: contaminação de vídeo pago (derrubado), Instagram como indicador
   comercial (social mede orçamento), pareado diário do 11 de Setembro (sem potência).

## Rodada 9b — audiência real do YouTube e os dois cases (16/09/2026)

Acesso à YouTube Analytics API destravado às 14h (OAuth com client da Bárbara + conta gestora;
`youtube-analytics/README.md`). Séries: `data/yt_diario.csv` (canal/dia desde 01/08/2025),
`data/yt_cases_diario.csv` (views/dia dos 3 vídeos-case), `data/yt_videos_publico.csv`.
Script: [r9b_youtube_real.py](scripts/r9b_youtube_real.py) → `data/r9b_youtube_real.txt`.
Queries novas: [31](queries/31_lift_por_sabatina_d14_set.sql) (sabatinas D+14 com compras até 15/09),
[32](queries/32_lift_11setembro_plataforma.sql) (11 de Setembro na plataforma). Painel emendado
com `performance-diaria` até 12/09 (Analytics defasa ~2 dias). `fct_transactions` íntegra até 15/09.

### 1. O proxy do GA4 era fraco — e a audiência real confirma o termômetro, mais forte

ρ(views reais, GA4 Organic Video) = **0,43**. Um ano de análise rodou com um termômetro que
explicava menos de 20% da variância da audiência. Com views reais (408 dias), crivo da rodada 4:

| Indicador | ρ spend | ρ→tx | ρ→CAC |
|---|---:|---:|---:|
| views/dia | 0,17 | +0,21* | −0,17* |
| **minutos assistidos/dia** | 0,16 | **+0,34*** | **−0,32*** |
| **inscritos ganhos/dia** | 0,05 | **+0,34*** | **−0,30*** |
| GA4 Organic Video (antigo) | 0,10 | +0,27* | −0,15* |

Pareado alta vs baixa de **views reais** (quintil de spend × fds × fase): transações **+18,2%**
[+11,1, +26,8], receita +16,2%, **CAC −12,2%** [−16,9, −6,6], spend **−0,0%** (pareou perfeito).
**Sem lançamentos: tx +21,8%, receita +26,5%, CAC −10,9%** [−16,7, −4,1], p<0,001 — o efeito
que com o proxy caía para −6,8% (p=0,05) **resiste com a audiência real**. Conversão por
sessão do site segue ns (+5%): o canal não passa pelo site, passa pela base. Lag: views de
ontem → CAC hoje −12,7% [−17,3, −6,9]; persistência 0,78. **Minutos assistidos e inscritos
ganhos são termômetros melhores que views** — trocar no painel.

⚠️ Ressalvas que continuam: mix de campanha não balanceado (9a §5), n efetivo ~140 dias,
direcional (Gordon 2023). mCAC por saltos de budget com audiência real: `[VENDA]`-up
**−13,3%** (R$ 209 → 182, p=0,04; Spearman −0,19, p=0,001), IC da razão [−37%, +15%] —
direção certa, magnitude aberta. `[LEAD]` não inverte mais (−11%, ns) — o "+53%" da rodada 3
era artefato do proxy.

### 2. Jun–set/2026 semanal: audiência e mídia são independentes; audiência anda com ROAS

15 semanas: views×spend **+0,02**, views×receita +0,41, views×ROAS +0,42, views×CAC −0,29
(n=15, nenhum p<0,05). O canal fez 6–8M views/sem em junho (El Salvador), caiu para 2–3M em
jul–ago e voltou a 6–8M em set (STF/Master, 11 de Setembro). A receita não seguiu: junho
R$ 5–8M/sem com spend R$ 1,6–2,6M; setembro R$ 4,4–4,5M com spend R$ 1,5M — ROAS 2,9 nas
duas semanas de set contra 2,2–2,5 em ago (spend maior, audiência menor). Leitura: a
audiência não vende sozinha, mas as semanas de audiência alta rendem mais por real.

### 3. Sabatinas em D+14 completo (Renan e Marçal entram pela primeira vez)

| Sabatina | n pd | lift D+14 [IC95] | p | MDE |
|---|---:|---|---:|---:|
| Zema | 1.517 | **2,03× [1,52–2,56]** | <0,001 | 1,62× |
| Aldo Rebelo | 1.397 | **1,82× [1,30–2,40]** | 0,001 | 1,66× |
| Caiado | 2.523 | **1,71× [1,15–2,27]** | <0,001 | 1,48× |
| Salles | 745 | 1,39× [0,48–2,03] | 0,24 | 1,91× |
| **Marçal** | 1.835 | **1,14× [0,63–1,65]** | 0,52 | 1,60× |
| **Renan** | 920 | **1,14× [0,43–1,97]** | 0,65 | 1,83× |
| Cury / de Toni / Derrite | 1.822 / 419 / 461 | 1,10× / 1,10× / 1,04× | ns | 1,6–2,2× |

Pooled: Marçal+Renan **1,14×** (n=2.755, 39 obs vs 34 esperados) vs demais **1,57×** (n=8.884).
No YouTube, Marçal (834k) e Renan (380k) têm 10–90× as views dos outros. **"É formato, não
fama" fecha com dado**: a audiência externa do vídeo não prediz a ativação da base na
plataforma. **"Estreia tardia zera a ativação" perde força**: o 0,70× de D+7 vira 1,14× em D+14
— compatível com 1× e com o 1,57× dos demais (IC até 1,65). Continua indício, não regra.

### 4. Os dias dos vídeos-case: views do vídeo × resíduo de receita

| Case | dia | views do vídeo (% do canal) | receita vs esperado | tx vs esp. | spend vs esp. |
|---|---|---:|---:|---:|---:|
| Renan | 14/08 | 221k (50%) | +3% | +14% | +39% |
| Marçal | 17/08 | 292k (45%) | +130% | +101% | **+147%** |
| **11 de Setembro** | 10/09 | 481k (39%) | **+24%** | −4% | −3% |
| | **11/09** | **1,33M (64%)** | **+12%** | −8% | **−12%** |
| | 12/09 | 639k (40%) | +34% | 0% | +13% |

Renan e Marçal: a receita seguiu o spend (rodada 1 confirmada). **11 de Setembro é diferente**:
em 10 e 11/09 a receita ficou 12–24% acima do esperado **com spend igual ou 12% abaixo** e
transações abaixo — foi ticket (Vitalício BP10: 29% → 65% da receita ao longo da semana). Duas
leituras não separáveis no diário: a live trouxe base morna para o fechamento, ou o fechamento
de lote sozinho fez o mix. O pessoa-dia decide.

### 5. 11 de Setembro na plataforma — e um gotcha

**A "estreia de 07/09" era 1 usuário (QA).** A audiência real do doc na plataforma começa em
**11/09**, dia seguinte à live no YouTube: 734 / 726 / 607 / 348 usuários em 11–14/09. Mesmo
padrão do Technocracia. Com compras até 15/09 só existe **D+3** para exposição 11–12/09:

| Estrato | n pd | taxa D+3 | controle | lift [IC95] | p | MDE |
|---|---:|---:|---:|---|---:|---:|
| Membro leve/médio | 595 | 0,50% | 0,21% | **2,44× [0,67–8,83]** | 0,16 | 3,67× |
| Membro heavy | 194 | 0,52% | 0,44% | 1,16× | ns | 4,4× |
| Freemium | 64 | 1,56% | 0,86% | 1,82× | ns | 4,9× |

3 compradores contra 1,3 esperados. **Não é conclusão** — o MDE é 3,7× — mas a direção é a da
hipótese contrária à da Bárbara. D+7 fecha em 19/09, D+14 em 26/09; agendado.

### 6. Falso positivo por campanha? Separando orgânico de anúncio e tirando aberturas e fechamentos (16/09, noite)

Views por origem de tráfego (`data/yt_diario_origem.csv`, 313 dias — a API falhou em 19 janelas):
Shorts 37% · inscritos 31% · sugeridos 13% · busca 7% · externo 4% · **anúncio 1,4%**. Views de
anúncio têm ρ −0,03 com spend (mediana 0/dia) — a mídia paga em vídeo quase não aparece no canal.
Dias "alta" de views orgânicas de vídeo longo (sem anúncio, sem Shorts) coincidem com abertura
de campanha em **30% vs 33% dos dias "baixa"**, e com fechamento em **11% vs 12%** — não há
sobre-representação de fechamento nos dias de audiência alta.

| Recorte (views orgânicas de vídeo longo) | Transações | CAC ads | Spend pareou |
|---|---|---|---|
| todos os dias | +22,8% [+14,1, +34,1] | **−13,6%** [−18,7, −7,5] | +2,3% ns |
| sem abertura (±3d) | +16,8% | −10,0% [−16,2, −2,6] | +0,5% ns |
| sem fechamento (−2..0) | +24,1% | **−17,6%** [−22,7, −11,7] | −1,1% ns |
| **sem abertura nem fechamento** (169 dias) | **+15,8%** [+7,3, +27,5] | **−12,6%** [−18,6, −5,2] | −2,2% ns |
| controle negativo: views de **anúncio** | +6,0% ns | **+8,7% (pior)** | +2,4% ns |
| só views de **inscritos**, sem abertura/fechamento | +19,0% | −13,4% | −1,0% ns |
| só **Shorts**, sem abertura/fechamento | +5,6% ns | −12,5% | +1,1% ns |

Leitura: (a) tirar fechamento **aumenta** o efeito — fechamento não é a fonte do sinal; (b) o
controle negativo funciona: dias de mais views **pagas** têm CAC **pior**, o oposto do orgânico;
(c) a audiência de **inscritos** (a base própria, imune a viral e a anúncio) carrega o efeito
inteiro; (d) Shorts não movem transações. **Não é falso positivo de campanha.** O que sobra em
aberto é o mix de campanha (9a §5) e a direção causal — para isso só geo.

### 7. Instagram entra na régua (16/09, noite) — Graph API do @brasilparalelo (token do Ailson)

Série diária desde 01/08/2025 (`data/ig_diario.csv`; `BigQuery/instagram-insights/fetch_instagram_daily.py`):
alcance, contas engajadas (só desde 01/03/2026), interações, shares, saves, views, cliques no site,
visitas ao perfil. `follower_count` só existe para os últimos 30 dias — coleta diária a partir de agora.
Mídias de 05–14/09 com alcance/interações em `data/ig_midias_set.csv`. Script: [r9b_instagram.py](scripts/r9b_instagram.py).

| Indicador | ρ spend | ρ→tx | ρ→CAC | Pareado s/ abertura+fechamento (tx · CAC · spend pareou?) |
|---|---:|---:|---:|---|
| **IG alcance** | **0,59** | −0,04 | −0,02 | +8% · −0,5% ns · **spend +8,3%** ❌ |
| IG contas engajadas | 0,60 | −0,17* | +0,05 | ns · ns · ok |
| IG compartilhamentos | 0,31 | +0,12* | −0,03 | ns · **CAC +8,9% pior** · ok |
| IG cliques no site | 0,43 | +0,38* | −0,33* | +40% · −24% · **spend +10,4%** ❌ (é clique de campanha) |
| GA4 Organic Social | 0,88 | +0,06 | −0,08 | — |
| YT views orgânicas longo | 0,01 | +0,34* | −0,27* | +17% · **−13,4%** · ok ✅ |
| YT views de inscritos | −0,03 | +0,28* | −0,24* | +20% · **−13,9%** · ok ✅ |

- **Nenhuma métrica do Instagram passa no crivo.** Alcance e engajamento medem orçamento (ρ 0,6 com
  spend — a conta impulsiona posts e o alcance sobe com campanha); cliques no site têm sinal forte
  mas o pareamento por spend falha: é o clique da campanha, não relevância. Compartilhamentos, a
  métrica mais "orgânica", dão CAC **pior**. Repete o que o GA4 social já dizia, agora com o dado nativo.
- **Instagram e YouTube não medem a mesma coisa**: resíduos correlacionam 0,06–0,13.
- Dias dos cases: Marçal 17/08 foi também o maior dia de Instagram do período (+86% de alcance);
  11–12/09 alcance +44% / +25%. Posts sobre 11 de Setembro no feed: ~640k de alcance somado.
- **Uso legítimo do Instagram no relatório**: atenção (alcance, seguidores) e funil rastreado
  (leads e vendas com UTM de Instagram orgânico, 8–33 mil leads/mês) — **nunca** como termômetro
  comercial. O único que sobrevive como termômetro é o YouTube.

### 7b. Alcance pago × orgânico no Instagram (Marketing API, mesmo token) — 16/09, noite

O token do Instagram é o `META_ACCESS_TOKEN` do `meta_api/.env` (Ailson; não expira; *data access*
até 10/11/2026) e tem `ads_read` → alcance/impressões/spend **pagos no placement Instagram por dia**,
14 contas (`instagram-insights/separar_pago_organico.py` → `data/ig_pago_diario.csv`, 410 dias).
Alcance pago IG mediana 1,49M/dia vs alcance da conta 2,38M/dia; **ρ(conta, pago) = 0,61**,
ρ(conta, spend Meta) = 0,60. Residualizar a conta pelo pago **não** produz uma série orgânica limpa
(resíduo ainda ρ 0,52 com spend): o que infla a conta não são os dark posts das contas de anúncio e
sim posts impulsionados + halo de campanha, que a Insights API não separa. Separar de verdade exige
identificar por mídia os posts impulsionados (ads com `effective_instagram_media_id`) e subtrair — fica
como pendência. Conclusão mantida: Instagram não serve como termômetro; serve como atenção e funil.

### 8. Calendário completo da wiki (estreias medidas, aberturas, fechamentos, lotes, ofertas) — o efeito sobrevive? (16/09, noite)

Com as páginas novas `lancamentos.md` e `cenario-comercial.md` (+ `campanhas-calendario.md`), 56% dos
dias do painel têm algum evento interno (estreia ±1, abertura ±3, fechamento −2..0, lote/virada ±1,
oferta nova). Script: [r9b_calendario_completo.py](scripts/r9b_calendario_completo.py).

| Recorte (views orgânicas de vídeo longo) | Transações | CAC ads | Spend pareou |
|---|---|---|---|
| todos (408 dias) | +24,8% | −15,6% | ✅ |
| sem estreia / sem abertura / sem fechamento / sem oferta nova | +19 a +26% | −14 a −17% | ✅ |
| sem lote/virada | +18,7% | −11,1% | +4,6% (p=0,05) |
| **só dias limpos** (181 dias, nenhum evento) | **+15,8%** [+4,9, +30,7] p=0,006 | −9,0% [−17,7, +2,1] p=0,12 | ✅ |

- **Regressão com todos os dummies de calendário + spend + DOW + mês + tendência (HAC):** elasticidade
  de transações a views **+0,17** [+0,08, +0,26]; minutos **+0,18**; inscritos ganhos **+0,20**; CAC
  −0,13 a −0,14, todos p<0,001. Para comparar: abertura de carrinho vale +5% e fechamento +11% em
  transações no mesmo modelo — o YouTube não é um dummy de calendário disfarçado.
- **Placebo por permutação** (série de YouTube embaralhada dentro dos estratos, 500×): efeito espúrio
  fica em [−7,6%, +10,1%] para transações e [−6,4%, +8,4%] para CAC; o observado (+24,8% / −15,6%)
  está fora — p_placebo < 0,002.
- **Preditivo fora da amostra** (treino ago/25–mai/26, teste jun–set/26): YouTube de ontem reduz o
  erro de previsão do CAC de hoje (RMSE 0,442 → 0,419), mas o modelo inteiro prevê mal em 2026 (R²
  fora negativo — mudança de regime de ticket, a mesma que quebrou o MMM). Sinal útil, previsão fraca.

**O que isso fecha e o que não fecha.** Fecha: não é fechamento, não é lote, não é oferta, não é
estreia, não é anúncio em vídeo, não é ruído (placebo). **Não fecha: causalidade.** Um terceiro fator
que mova ao mesmo tempo a base a assistir e a comprar (notícia quente, clima político, o próprio
"momento" da marca) produz exatamente este padrão sem que o vídeo cause a venda. A audiência de
inscritos carregar o efeito é compatível com as duas leituras. O teste que decide não é observacional:
**regra pré-registrada de escala** — em dias com YouTube de ontem > 1,3× MM28, subir spend +20% em metade
das campanhas [VENDA] sorteadas, manter a outra metade, medir mCAC das duas por 6–8 semanas. Se o mCAC
da metade escalada nesses dias ficar abaixo do mCAC das escaladas em dias normais, a alavanca é real
para a decisão que importa (quanto gastar). É barato, não exige geo e usa o recomendador que já existe.

### Veredito para a Bárbara (o que dá para dizer na sexta)

1. **Atenção**: 11 de Setembro = 2,86M views, 4,5k inscritos, pico 1,33M em 11/09; 2,5k usuários
   na plataforma a partir de 11/09. Sabatinas: 834k + 380k views; 3,9k + 1,8k na plataforma.
2. **Venda rastreável**: publisher YouTube 23 tx em 13/09 (máximo de set), 1% do total; CTA na LP
   ainda sem UTM específico do vídeo — pedir tagging por vídeo nas telas finais.
3. **Não rastreável**: no diário, 10–11/09 renderam 12–24% acima do esperado com spend igual ou
   menor — o único dos três cases em que a receita não segue o spend. No fim de semana 12–13/09
   o spend BP10 explica mais que o crescimento (BP10 por UTM 1.679 → 2.758; o resto caiu 2,5%).
4. **Veredito**: **ela está certa para 12–13/09 e provavelmente errada para 10–11/09** — mas
   "provavelmente" é o teto honesto: o teste de pessoa-dia só detecta ≥3,7× hoje e fecha em 19/09
   (D+7) e 26/09 (D+14). O pareado com audiência real diz que dias de canal forte rendem CAC
   ~11–12% menor com o mesmo dinheiro, sem lançamento — é o argumento estrutural a favor dela
   estar errada no geral, mesmo que certa no fim de semana.

### Escala de mídia sem perder eficiência — semana 07–13/09 (pergunta do André, 14/09)

Query: [30_semana_meta_google_por_campanha.sql](queries/30_semana_meta_google_por_campanha.sql).
Comparação 07–13/09 vs 31/08–06/09, por campanha e fonte (atribuição das plataformas):

| | 31/08–06/09 | 07–13/09 | Δ |
|---|---:|---:|---:|
| Spend total | R$ 1,51M | R$ 1,91M | **+26%** |
| Receita (fct_transactions) | R$ 4,35M | R$ 5,51M | **+26%** |
| ROAS total | 2,88 | 2,88 | **igual** |
| Transações | 7.432 | 8.365 | +13% |
| Receita por transação | R$ 586 | R$ 658 | +12% |

- **BP10 escalou sem saturar**: spend Meta R$ 669k → R$ 1,16M (**+73%**), vendas 1.304 → 2.216
  (+70%), CPA R$ 513 → R$ 523, **ROAS 1,73 → 2,08**. mCAC da escalada ≈ R$ 538, igual ao CPA médio.
- **Saturou fora do BP10**: CBR +84% de spend com CPA +14%; TLR triplicou spend e o CPA foi de
  R$ 272 para R$ 864. Campanhas que cortaram spend (10R, ELS, ENE, FNC, PMax) melhoraram CPA.
- Google busca de marca cortado 84% (R$ 40k → R$ 6k); YouTube Ads flat com ROAS 5,55 → 3,09 — o
  "Google teve o pior desempenho" da Bárbara é isso, sobre base pequena.
- **Teste da hipótese dela**: tx com UTM BP10 1.679 → 2.758 (**+1.079**); o total subiu **+933**.
  Tudo que não é BP10 **caiu 2,5%**. No semanal, BP10 explica mais que o crescimento inteiro.

⚠️ Correção de método que isso trouxe para a rodada 1: **"o ROAS caiu em 6 de 8 campanhas ao escalar"
conta campanhas, não reais.** Ponderado por spend, a BP escalou 26% duas vezes em um mês com ROAS
constante, e a campanha dominante escalou 70% com custo marginal igual ao médio. A frase "resistência
não caiu, piorou" não se sustenta ponderada por dinheiro — corrigir na §Resposta curta.

### O que o `mmm_project` já tem e este estudo reusou (revisão de 16/09)

| Peça | Onde | Uso aqui |
|---|---|---|
| **Índice de demanda não-Meta** | `mmm_project/scripts/09_bidding/06_demand_index.py` | Validado no overspend de 09–10/05 (índice 0,72 = o pico foi gasto, não demanda). Entrou como contexto no `performance-diaria`. ⚠️ Precisa de variante que exclua UTM da campanha dominante. |
| **Harness de overspend por evento** | `09_bidding/05_overspend_event.py` | Baseline "mesmo DOW ±3 semanas" adotado no `performance-diaria`. |
| **GeoLift desenhado** | `output/geolift/` (3 cidades, potência, scripts R) | Viabilidade já feita; **MDE 25% em 2 semanas** — reforça o argumento de potência da §9a. |
| **Lição do OOS 2026** | `output/oos_2026/interpretacao_oos_2026.md` | Unidades e receita divergiram em 2026 (conversões −26%, receita +23% por mix de ticket). **É a mesma divergência das §9d/§9e** — target em unidades quebrou lá e engana aqui. |
| **Não-identificabilidade Meta × Google** | `revisao_mmm_2026-09-10.md` | ρ(spend Meta, Google) = 0,874 → nunca separar canais pagos; somar. |
| **Saturação quase linear** | idem | b≈0,93 medido aqui bate — ⚠️ mas ambos podem ser endogeneidade do spend (§9g). |

**Dívida comum aos dois projetos:** o calendário de campanhas de 2026 estava faltando nos dois
(`tb_campaign_period` sem DOM/ELS/CDL/EVG/ODI/ENE; `campaign_calendar.csv` do MMM para em VDS).
Resolvido pelas páginas novas da wiki (`campanhas-calendario.md`, `lancamentos.md`,
`cenario-comercial.md`) — usar essas como fonte única até a API do marketing-bp subir.


## Rodada 9c — insights novos (17/09/2026, skill data-analyst)

Oito hipóteses que as rodadas 1–9b não testaram, cada uma com hipótese nula declarada.
Script: [r9c_insights.py](scripts/r9c_insights.py) · saída `data/r9c_insights.txt`. Painel de 313 dias
com audiência real (views orgânicas de vídeo longo, sem anúncio/Shorts), controles de DOW, mês×ano,
spend, fase, lançamento e fechamento.

### 1. ⭐ O efeito é MAIOR fora da mídia paga — e o Comercial é a prova do mecanismo

Pareado por spend, sem abertura nem fechamento, por canal de venda (placebo por permutação 500×):

| Canal | % das tx | Efeito | IC95 | p_placebo |
|---|---:|---:|---|---:|
| **Orgânico + YouTube** | 8% | **+63,4%** | [+41,3, +100,5] | <0,002 |
| **Comercial** | 22% | **+30,6%** | [+16,8, +59,4] | <0,002 |
| Ads (Meta+Google) | 41% | +21,3% | [+11,7, +34,0] | <0,002 |
| CRM | 14% | +7,2% | [−13,0, +40,5] | 0,52 (ns) |
| **Tudo menos ads** | 55% | **+22,8%** | [+12,8, +37,0] | — |
| Ticket médio | — | −5,4% ns | [−13,3, +4,0] | — |

**O Comercial é o achado central desta rodada.** O time comercial vende por telefone/WhatsApp — não
depende de tráfego do site, não é alcançado por remarketing, não vê o vídeo como canal. Decompondo
(n=79 dias com dado de Zenvia): **abordagens +25,1%** (esforço — há mais gente para abordar) e
**conversão por abordagem +18,0%** (a mesma abordagem fecha mais). A segunda metade não tem
explicação por volume de tráfego: é a assinatura de **base mais receptiva**, o mesmo mecanismo que o
pessoa-dia mostra dentro da plataforma. Se o efeito fosse artefato de mídia ou de tráfego, o
Comercial seria o canal com menos efeito, não o segundo com mais.

### 2. ⭐ Em dia de audiência alta, o real de mídia rende mais — e mais ainda quando o spend é alto

Efeito dentro de cada quintil de spend (não entre quintis):

| Quintil de spend | Spend mediano | Δ transações | **Δ CAC** |
|---|---:|---:|---:|
| Q1 | R$ 46k | +35,8% | −19,3% |
| Q2 | R$ 81k | +44,0% | −24,0% |
| Q3 | R$ 115k | +11,3% | −7,2% |
| Q4 | R$ 182k | +21,5% | **−29,2%** |
| Q5 | R$ 311k | +24,8% | **−27,9%** |

Em dias de **spend alto (Q4+Q5)**: CAC médio **R$ 270** com audiência alta vs **R$ 379** com audiência
baixa — **R$ 109 por aquisição**. É a leitura operacional mais direta do programa: não é "gastar mais
porque o canal está bom", é **escolher o dia de escalar**. (Correlacional; o teste de escala
pré-registrado da §9b.8 é o que transforma isso em regra.)

### 3. Dose-resposta monotônica, com salto no topo — e um limiar utilizável

Quintis de audiência **dentro** do quintil de spend (resíduo controlado):

| Quintil de audiência | Views/dia (mediana) | tx vs esperado | CAC vs esperado |
|---|---:|---:|---:|
| Q1 (mais baixa) | 189k | −7,7% | +5,7% |
| Q2 | 245k | −2,2% | +7,8% |
| Q3 | 299k | −2,0% | +2,2% |
| Q4 | 362k | +2,6% | −4,1% |
| **Q5 (mais alta)** | **554k** | **+10,1%** | **−8,2%** |

A curva é monotônica em CAC e o ganho se concentra no quintil de cima: **acima de ~450–550k views/dia**
de vídeo longo orgânico. Serve como corte operacional melhor que o "1,3× a MM28" (que era do proxy GA4).

### 4. O efeito é contemporâneo — não existe adstock de audiência orgânica

Regressão de defasagem distribuída (D a D−10, HAC-14): **D0 +0,177 (p<0,001)**; a soma dos 11 lags é
**+0,194**, ou seja **91% do efeito está no próprio dia**. Só D−3 (−0,077, p=0,003) e D−6 (+0,051,
p=0,089) aparecem, com sinais opostos — ruído, não cauda. **Consequência prática: audiência de ontem
não é "estoque" acumulável.** Um vídeo que rende hoje não deixa saldo para a semana.

### 5. Inscritos: só o fluxo vale; o estoque acumulado não prediz nada

Semanal (n=50): inscritos líquidos **da própria semana** → transações elast. **+0,206 (p=0,001)**;
inscritos líquidos **acumulados nas 4 semanas anteriores** → **−0,020 (p=0,69)**; audiência acumulada
de 4 semanas → −0,136 (p=0,10). **Não há construção de marca mensurável por inscrito no nosso dado.**
O canal funciona como fluxo de atenção, não como ativo que se acumula — pelo menos no horizonte de
13 meses e com a nossa variância.

### 6. Um vídeo gigante isolado NÃO move a venda de forma detectável

10 programas com +1M views desde ago/2025 (El Salvador 4,16M · Master×STF 4,02M · 11 de Setembro
2,86M · Rio 2,70M · Epstein 2,22M · Banco Master 2,14M…). Event study com resíduo controlado:

| Janela | n | tx vs esperado | percentil no placebo | CAC |
|---|---:|---:|---:|---:|
| D+0 | 9 | +4,1% | p61 | −4,5% |
| D+1 | 7 | +11,5% | p73 | −3,0% |
| D+2 | 6 | +12,0% | p74 | −6,2% |

Nenhum passa do p95. **Esta é a resposta direta ao Luan**: "dois hits recentes no YT" não é uma
amostra — é n=2 dentro de uma série onde nem os 10 maiores vídeos do ano somados produzem efeito
destacável. O sinal existe no **regime** (dias de canal forte), não no **evento**.

### 7. Entrevista vende; live de notícia não

Dias classificados pelo programa mais visto publicado em D..D−2 (base de vídeos da §BASE_VIDEOS):

| Tipo do programa | n dias | Views medianas | tx vs esperado | CAC vs esperado |
|---|---:|---:|---:|---:|
| **Entrevista / sabatina** | 12 | 647k | **+7,6%** | **−8,9%** |
| Outro programa | 212 | 345k | +1,3% | −2,1% |
| **Live de notícia / react** | 15 | 448k | **−5,6%** | −1,2% |
| Sem programa > 100k | 65 | — | −2,8% | +9,7% |

Consistente com o pessoa-dia (formato entrevista ativa a base; 1,61× = BP Entrevista). **Live de
notícia traz audiência grande e não vende** — é o caso do Master×STF e do STF de 15/09. n pequeno
(12 e 15 dias), leitura direcional.

### 8. O efeito é quase simétrico — dia ruim custa tanto quanto dia bom rende

Decil mais alto de audiência: **+6,7%** de transações vs esperado. Decil mais baixo: **−7,5%**. Meio
(80% dos dias): 0,0%. Não há limiar de "tudo ou nada" nem efeito só na cauda boa — o que reforça ler
a audiência como **termômetro contínuo**, não como gatilho binário.

### O que muda na recomendação

1. **Parar de perguntar "o vídeo X vendeu?"** — a pergunta certa é "o canal está em regime alto?".
   Evento único não tem potência (§6); regime tem (§1–3).
2. **A régua operacional vira o quintil de audiência** (~450–550k views/dia de vídeo longo orgânico),
   não o 1,3× MM28 do proxy antigo.
3. **A decisão que vale dinheiro é quando escalar**: R$ 270 vs R$ 379 de CAC em dias de spend alto.
4. **Pautar entrevista, não react de notícia**, se o objetivo é comercial (react serve a alcance).
5. **Avisar o Comercial** nos dias de audiência alta: a conversão por abordagem sobe 18%.

## Rodada 9d — a eficiência é função só de (spend, audiência)? (17/09/2026)

**Pergunta do André:** no spend alto, a audiência é a única variável? A curva depende de estar
subindo ou descendo? O próximo passo é aumentar, manter ou reduzir?
Script: [r9d_curva_direcao.py](scripts/r9d_curva_direcao.py) · saída `data/r9d_curva_direcao.txt`.

> ⚠️ **Esta rodada CORRIGE a §9c.2.** O "CAC R$ 270 vs R$ 379 em dias de spend alto" está certo como
> número e **errado como recomendação**: é custo por **transação**, e some quando se mede custo por
> **receita**. A recomendação "escolher o dia de escalar" não se sustenta — ver C abaixo.

### A. A audiência NÃO é a única coisa que muda (balanço da célula de spend alto, Q4+Q5)

| Variável | Aud. alta (n=62) | Aud. baixa (n=63) | Δ | p |
|---|---:|---:|---:|---:|
| Views orgânicas | 516.935 | 231.014 | +124% | <0,001 |
| Spend | R$ 275,8k | R$ 253,9k | +8,6% | 0,18 |
| Transações | 1.913 | 1.555 | **+23,1%** | <0,001 |
| CAC de ads | R$ 267 | R$ 376 | **−28,9%** | <0,001 |
| **Ticket médio** | **R$ 399** | **R$ 479** | **−16,7%** | **0,009** |
| **% fim de semana** | **45%** | **27%** | **+67%** | **0,035** |
| % em janela de lançamento | 8% | 22% | −64% | 0,028 |
| Nº de campanhas ativas | 23,9 | 22,0 | +8,4% | 0,007 |
| Concentração do spend (HHI) | 0,282 | 0,263 | +7,5% | 0,23 |

Dias de audiência alta são **mais fim de semana, menos lançamento, ticket menor e mais campanhas
simultâneas**. O mix de campanha (HHI, share do dominante) está balanceado — isso fecha a pendência
da §9a.5. Mas ticket e fim de semana não estavam controlados.

### B. ⭐ A audiência desloca o NÍVEL da curva, não a INCLINAÇÃO

`log(tx_ads) = a + b·log(spend) + c·log(YT) + d·log(spend)×log(YT) + DOW + mês×ano + fase` (HAC-7):

| Parâmetro | Estimativa | IC95 | p |
|---|---:|---|---:|
| **b** — elasticidade ao spend | **+0,932** | [+0,792, +1,071] | <0,001 |
| **c** — efeito da audiência | +0,153 | — | 0,0005 |
| **d** — interação spend × audiência | **+0,051** | **[−0,064, +0,167]** | **0,38 (ns)** |

Elasticidade ao spend em dia de audiência baixa **0,909**; em dia de audiência alta **0,955** —
indistinguíveis. **O próximo real rende o mesmo nos dois tipos de dia.** O dia inteiro é melhor
(c>0), mas a curva não inclina. Corolário: **"escalar em dia de audiência alta" não tem base** —
você venderia mais naquele dia de qualquer jeito, e o real incremental performa igual.
(Nota lateral: b≈0,93 significa resposta **quase linear** ao spend no regime atual, batendo com o
achado do MMM de que a saturação assumida estava errada.)

### C. ⭐ O ganho é em UNIDADES, não em receita — o CAC engana

Painel completo, sem abertura nem fechamento, pareado por spend:

| Métrica | Efeito | IC95 | p |
|---|---:|---|---:|
| Transações | **+15,8%** | [+7,2, +26,2] | <0,001 |
| **CAC por transação** | **−17,0%** | [−22,6, −10,5] | <0,001 |
| Receita | +8,2% | [−1,9, +23,2] | 0,11 |
| **Custo por R$ 1.000 de receita** | **−6,3%** | **[−13,3, +2,7]** | **0,21 (ns)** |
| ROAS | +8,0% | [−1,3, +23,7] | 0,10 |
| Ticket médio | −5,4% | [−12,8, +4,3] | 0,29 |

Na célula de spend alto o contraste é mais duro: **receita +1,1% (p=0,87) e ROAS −7,3%** com CAC
−28,9%. Vendem-se 23% mais unidades de ticket 17% menor, e a receita fica igual. **O sinal forte
do YouTube é em aquisição de clientes, não em receita.** Sobrevive em dia útil e em fim de semana
(CAC −27,2% e −22,5%), então não é só composição de calendário — mas a régua de receita não confirma.

### D. ⭐ Histerese: o caminho importa mais que o nível

CAC no mesmo quintil de spend, conforme o spend vinha **subindo** ou **descendo** (vs MM7):

| Quintil de spend | CAC subindo | CAC descendo | Δ | p |
|---|---:|---:|---:|---:|
| Q4 | R$ 289 (n=34) | R$ 319 (n=25) | **−9,6%** | **0,041** |
| **Q5** | **R$ 334** (n=44) | **R$ 436** (n=10) | **−23,5%** | **0,013** |
| Q1–Q3 | — | — | −11% a +5% | ns |

**Chegar ao spend alto descendo custa 24% mais caro que chegar subindo.** É a "ressaca" pós-pico
que a `cenario-comercial.md` descreve (queda de 10–30% por 7–14 dias após fechamento): o mesmo
nível de investimento, com demanda já drenada. Matriz de estados (todos os dias):

| Estado | n | CAC | tx/dia | vs CAC médio |
|---|---:|---:|---:|---:|
| **spend ↑ · audiência ↑** | 71 | **R$ 277** | 1.514 | **−9,2%** |
| spend ↓ · audiência ↑ | 55 | R$ 288 | 1.028 | −5,8% |
| spend ↓ · audiência ↓ | 94 | R$ 323 | 930 | +5,6% |
| **spend ↑ · audiência ↓** | 73 | **R$ 324** | 1.479 | **+6,1%** |

**A direção da audiência separa melhor que a direção do spend.** O pior estado é escalar com
audiência caindo — mesmo CAC de quando se está reduzindo.

### E. Mas o mCAC não segue: a audiência não prediz o retorno de escalar

119 dias em que o spend subiu >5% no dia seguinte e as vendas de ads subiram; mCAC = Δspend/Δtx:

| Estado de hoje | n | mCAC mediano | vs geral |
|---|---:|---:|---:|
| Spend já vinha subindo | 52 | R$ 207 | −10,0% |
| Audiência baixa e caindo | 51 | R$ 216 | −5,9% |
| Audiência alta (no quintil) | 55 | R$ 224 | −2,5% |
| Audiência alta E subindo | 39 | R$ 224 | −2,5% |
| **Audiência subindo** | 52 | **R$ 264** | **+15,1%** |

Mediana geral R$ 229 — **acima do teto de margem de R$ 180** e das referências (LAN R$ 145 / PPT
R$ 188). "Alta e subindo" vs resto: p=0,194. **A audiência não prediz o mCAC de escalar**, o que é
exatamente o que B previa. O único estado que aparece com mCAC melhor é *o spend já vir subindo* —
inércia da própria campanha, não relevância.

### Resposta às três perguntas

1. **"A audiência é a única variável no spend alto?"** Não. Ticket (−17%), fim de semana (+67%),
   lançamento (−64%) e nº de campanhas também mudam. O mix de campanha, esse sim, está balanceado.
2. **"A curva vem de subida ou de queda, e isso impacta?"** Impacta, e muito: no Q5, chegar
   descendo custa **+23,5%** de CAC. Direção da audiência é o melhor separador de estado.
3. **"O próximo passo é aumentar, reduzir ou manter?"** **A audiência não responde isso.** Ela
   prevê o resultado do dia, não o retorno do próximo real (d ns; mCAC ns). Quem responde é o
   mCAC contra o teto: mediana R$ 229 hoje, acima do teto de R$ 180 → o padrão recente é de
   sobre-escala. A regra operacional continua sendo a do recomendador (mCAC × teto de margem),
   com a audiência entrando como **contexto do dia**, não como gatilho.

### O que isso muda no que já foi dito

| Antes (9b/9c) | Agora (9d) |
|---|---|
| "CAC −12% a −16% em dia de canal forte" | Certo **por transação**; em receita o efeito não é significativo (custo por R$1k: −6,3%, p=0,21) |
| "R$ 270 vs R$ 379 — a decisão que vale dinheiro é quando escalar" | **Retirado.** É custo por unidade, com ticket 17% menor; escalar não rende mais nesses dias (interação ns) |
| "Termômetro para decidir escala" | **Termômetro de resultado do dia**, não de retorno marginal |
| Mix de campanha era pendência (9a.5) | **Fechada**: HHI e share do dominante balanceados entre alta e baixa |

## Rodada 9e — o cliente que entra em dia de audiência alta vale menos? (17/09/2026)

A §9d levantou que o ticket médio cai 17% na célula de spend alto e concluiu que "o ganho é em
unidades, não em receita". Faltava a pergunta seguinte: **esse cliente mais barato vale menos?**
Query: [34_ltv_por_dia_aquisicao.sql](queries/34_ltv_por_dia_aquisicao.sql) · dados
`data/r9e_ltv_por_dia.csv`. **282.989 primeiras compras** em 234 dias (ago/2025–15/06/2026, todas
com 180 dias de maturação), cohort pelo dia da aquisição.

### Resposta: vale o mesmo — e o "ticket menor" da §9d era composição, não qualidade

Dias de audiência alta vs baixa, dentro do quintil de spend, sem abertura nem fechamento:

| Métrica do cliente adquirido | Aud. alta | Aud. baixa | Δ | p |
|---|---:|---:|---:|---:|
| Clientes novos/dia | 1.391 | 1.136 | **+22,5%** | 0,022 |
| **Ticket da 1ª compra** | **R$ 339** | **R$ 332** | **+1,9%** | **0,57 (ns)** |
| Receita extra em 90d | R$ 41 | R$ 37 | +11,8% | 0,92 |
| Receita extra em 180d | R$ 67 | R$ 71 | −5,6% | 0,27 |
| **LTV 180d** | **R$ 405** | **R$ 403** | **+0,6%** | **0,81 (ns)** |
| % recomprou em 180d | 6,6% | 6,0% | +9,4% | 0,35 |
| **LTV 180d ÷ CAC** | **1,59** | **1,37** | **+16,0%** | — |

**O ticket da primeira compra NÃO é menor.** O −17% da §9d era **efeito de composição**: em dia de
audiência alta entram 22,5% mais clientes novos (que sempre compram produto de entrada, ~R$ 339) e
vende-se relativamente menos high-ticket para a base (Vitalício/upgrade, R$ 1.500+), porque esses
dias são mais fim de semana (45% vs 27%) e menos janela de lançamento (8% vs 22%). O ticket médio do
dia cai porque o **mix** muda, não porque o cliente é pior.

### Por canal de aquisição, o cliente de dia de audiência alta é igual ou melhor

| Canal | n (alta/baixa) | Ticket 1ª compra | LTV 180d |
|---|---|---:|---:|
| **Ads** | 42,2k / 40,2k | R$ 203 vs 184 (**+10,5%**) | R$ 244 vs 219 (**+11,4%**) |
| **CRM** | 11,4k / 12,5k | R$ 246 vs 231 (+6,6%) | R$ 328 vs 301 (+8,7%) |
| Comercial | 19,8k / 19,6k | R$ 753 vs 772 (−2,4%) | R$ 892 vs 938 (−5,0%) |
| Outros | 14,2k / 12,9k | R$ 192 vs 193 (−0,6%) | R$ 213 vs 219 (−2,6%) |

**No canal pago, o cliente adquirido em dia de audiência alta tem LTV 11% maior.** Nenhuma
diferença é significativa isoladamente, mas a direção é consistente nos dois canais de volume.

### O que isso corrige na §9d

| §9d dizia | §9e mostra |
|---|---|
| "Ticket 17% menor → o CAC engana" | O ticket **do cliente** não muda; o do **dia** muda por mix (mais clientes novos, menos high-ticket da base) |
| "O ganho é em unidades, não em receita" | Correto para a **receita do dia**; mas as unidades são **clientes de mesmo valor** — LTV/CAC **+16%** |
| "Nunca reportar CAC sem receita ao lado" | Continua valendo; **acrescentar LTV/CAC**, que é a régua que reconcilia as duas |

**Leitura final das três rodadas (9c → 9d → 9e):** em dia de audiência alta a empresa **adquire mais
clientes do mesmo valor, a um custo menor por cliente**, sem ganhar receita no próprio dia (porque
troca venda de base por aquisição). Isso é bom para crescimento de base e neutro para caixa imediato
— e explica por que o efeito aparece em unidades e não em receita sem que nenhuma das duas medidas
esteja errada. O que segue **não** sustentado é usar a audiência como gatilho de escala (§9d B/E):
o retorno do próximo real continua igual.

## Rodada 9g — revisão estatística independente (17/09/2026)

Auditoria adversarial encomendada a um revisor independente (subagente Model QA), com acesso ao
`ANALISE.md`, aos scripts, às queries e ao BigQuery. Ele reconstruiu o painel e recomputou o que dava.
**Veredito: o núcleo sobrevive; quase tudo construído sobre ele nas rodadas 9c–9e não.**

### Erros confirmados (não usar)

| # | Achado derrubado | Por quê |
|---|---|---|
| 1 | **§9c.1 — "o Comercial prova o mecanismo"** (abordagens +25,1%, conversão/abordagem +18,0%) | **Não reproduzível e inverte**: com a máquina padrão e 300 dias, conversão/abordagem vira **+7,7% (IC [−12,5, +35,2], p=0,57)**. `tx_comercial` +30,6% se confirma, mas a decomposição — único elo declarado entre o painel diário e o mecanismo pessoa-dia — cai. **Não existe script commitado** que gere os números publicados. |
| 2 | **§9d.D — histerese "chegar descendo custa +23,5%"** | Confundida: no Q5, os dias "descendo" têm spend **35% menor** e **0% de fim de semana** (vs 52% nos "subindo"). Com controles: coef −0,053, **p=0,48**. A matriz de estados tem o mesmo defeito (compara R$200k/dia com R$104k/dia). **Retirar a seção inteira.** |
| 3 | **§9c.6 — "vídeo gigante não move a venda"** | **Bug** em `r9c_insights.py:159`: compara a média de n dias contra a distribuição de dias **individuais** — conservador por construção. Corrigido: D+1 e D+2 vão para **p91** com ~+12% (bicaudal p≈0,18). Somado à falta de poder (MDE 22%), o correto é "direcionalmente positivo, sem potência". |
| 4 | **§9e — "LTV/CAC +16%"** | Mistura populações: LTV é de **todas** as primeiras compras; CAC é **só de mídia paga**. Além de ser aritmética do CAC (−13,4% → +15,5%). É a única linha da tabela sem p. |
| 5 | **§9e corrigindo a §9d** | Períodos quase não se sobrepõem: o dado de LTV vai até 15/06/2026 e **44% das células de spend alto da §9d são posteriores** — justo o regime BP10/Vitalício (ticket mediano do dia R$ 398 → R$ 551). Além disso, "LTV 180d" é ~80% ticket inicial (só 1,33% renovaram em 180d; plano anual renova em 365d), então "LTV não muda" depois de "ticket não muda" é quase tautológico. Ponderando por cliente: clientes +13,1% (não +22,5%), LTV +0,3%, Ads +6,8% (não +11,4%). |

### Fragilidades graves (corrigir antes de usar)

- **Bootstrap iid em todos os scripts.** Autocorrelação dos resíduos: tx ρ₁ +0,42 (n efetivo 122/300),
  CAC +0,51 (97), audiência +0,46. Com **moving-block bootstrap** os IC alargam **1,6–1,9×** e
  **nenhum p<0,001 sobrevive** (o melhor vira 0,002–0,007). O Comercial vai a p=0,029.
- **Placebo por permutação faz a mesma suposição** do bootstrap (embaralha dentro do estrato,
  destruindo a autocorrelação). Com **deslocamento circular**, a banda nula é 30–40% mais larga —
  mas **o efeito continua fora dela** (tx p<0,001; CAC p=0,008). Conclusão "não é ruído" sobrevive.
- **Multiplicidade.** 40 p-valores explícitos nas rodadas 9a–9e; BH a 5% mantém **18**, corte p≤0,020.
  A família **executada** é de 250–400 testes → corte real p≤0,002. Combinando com o block bootstrap,
  o Comercial (p=0,029) **não passa**. As rodadas 9b–9e não aplicaram correção nenhuma.
- **§9d.B — "o próximo real rende o mesmo" é falta de poder.** MDE de *d* = 0,165, 3,2× a estimativa;
  o IC da diferença de elasticidade é [−0,057, +0,150] — compatível com 0,86 em dia ruim vs 1,01 em
  dia bom, diferença economicamente enorme. Além disso **b=+0,932 é endógeno** (spend escolhido em
  resposta à demanda) — a nota "bate com o MMM" deve sair.
- **27% dos dias faltavam** em `yt_diario_origem.csv` (95 de 408) e os ausentes tinham **mais**
  audiência (637k vs 500k, p=0,057) → censura correlacionada com o tratamento. ✅ **Corrigido na §9f**.
- **Estratos degenerados.** 6 de 14 células descartadas pela regra `len(g)<10`; no recorte principal
  sobram 8 estratos e **30 dias de fim de semana**. `em_venda`=1 em 88% dos dias (EVG/BP10/ODI/ENE sem
  data de fim) → a dimensão "fase" quase não separa; na prática o estrato é spend × fds.
- **CAC e transações continuam reportados como duas evidências** em §9b.1, §9b.6, §9b.8, §9c.2,
  §9d.A e §9d.C. Identidade verificada no dado real: spend pareia −0,4%, tx_ads +21,3%, CAC −16,5%,
  identidade prevê −17,9%. **É um fato só.** A §9a item 5 estava certa e foi ignorada.

### Bugs de código a corrigir

- `r9c_insights.py:77,154` — resíduo de CAC ajustado sobre dados **imputados pela mediana**.
- `r9c_insights.py:140-142` — regressões de CAC da §9c.F retornam `+inf (p=nan)`; o texto omite.
- `r9c_insights.py:25` — **`tx_organico` muda de definição no ponto de emenda (20/08)**: antes sem
  YouTube, depois com. São os 23 dias mais recentes e de maior audiência → afeta o "+63,4%" da §9c.1.
- `r9d_curva_direcao.py:122` — o mCAC condiciona em `Δtx > 0`, **selecionando pelo denominador do
  próprio desfecho**; 8 estados não-exclusivos, um p escolhido depois de ver os resultados.
- **A §9e não tem script.** Só query e CSV; os números são irreproduzíveis.

### Conclusões além do dado que eu não tinha visto

1. A seção **"Métrica proposta"** ainda recomenda o **proxy do GA4** (ρ 0,43 com as views reais) e a
   regra **"se o YT está alto há espaço para escalar"** — que a §9d retirou. É a única parte que vai
   para o painel, e está internamente contraditória.
2. **§9c.3** — o corte "450–550k views/dia" é a **mediana do quintil superior**, não a fronteira:
   recomendá-lo como limiar deixa metade dos dias "bons" de fora.
3. **§9c.4 — "sem adstock"** é assumido, não medido: a soma dos lags vem **sem erro-padrão**, os lags
   são colineares (ρ₁ 0,46) e o modelo controla só o spend **contemporâneo**.
4. **§9d.A — "mix de campanha balanceado fecha a §9a.5"** é aceitação da nula com n=125 e p=0,23/0,45.
   O HHI mede concentração, não o desbalanço por campanha que a §9a.5 apontou (BP10 7% vs SDC 100%).
5. **§9c.8 — "quase simétrico"** não tinha teste; recomputado dá p=0,031 e p=0,059, não sobrevive a FDR.
6. **§9c.7 — entrevista vs react**: o contraste direto é p=0,017 (Welch), melhor do que eu julguei,
   **mas é post-hoc entre 2 de 4 grupos**, com classificação por regex de título e n=12/15. Sustenta
   "vale um teste dedicado", não a recomendação de pauta.
7. **§9b.1 — "views de ontem → CAC hoje"**: com ρ(hoje, ontem)=0,78 é ~o mesmo fato contemporâneo.
   Precedência exigiria condicionar em views de hoje.

### O achado que ele trouxe a favor — e que virou contra na §9f

O revisor propôs **renovações como controle negativo** e, com a série de 313 dias, elas davam +0,5%
(p=0,51) contra +15,9% das vendas novas — ele chamou de "o teste mais forte a favor que existe no
material". **Com a série completa de 408 dias o teste inverte** e é o que a §9f documenta: renovação
no cartão +0,116 vs venda nova +0,174, razão ns. Registrar os dois resultados é importante: a
diferença veio exclusivamente da correção da censura de 27% dos dias.

### Desenhos causais — a avaliação dele

- **O holdout de conteúdo na plataforma (que eu propus) não responde a pergunta** — testa o que a
  máquina pessoa-dia já testa, que a §9a item 1 identificou como pergunta **diferente**.
- **O teste de escala da §9b.8 também não** — mede o parâmetro *d* da §9d.B, sem sinal e sem poder;
  produziria um nulo quase garantido que não diria nada sobre causa.
- **O que responde**, em ordem de custo-benefício:
  1. **Encorajamento aleatorizado na base** — sortear metade para receber push/e-mail apontando ao
     vídeo no YouTube; medir compra D+1..D+14 por intenção de tratar. Randomiza no nível da pessoa,
     usa a infra de CRM, detecta lift de **1,2×** (vs 1,6–2,0× do pessoa-dia observacional).
  2. **Aleatorizar o dia de publicação** de conteúdo evergreen, em pares bloqueados por DOW e fase.
     Torna a audiência exógena **no nível do dia**, que é a unidade do painel. Precisa de ~40 estreias
     → programa de 12 meses.
  3. **Aleatorizar o empurrão externo** (push no Instagram/CRM/app) por vídeo. Roda imediato, mais fraco.
- **Não funciona** (registrar para não tentar): geo (o YouTube não recorta por UF), IV com notícia
  externa (é o confundidor, não o instrumento), synthetic control (não há unidade de controle).

## ⛔ Rodada 9f — o controle negativo FALHA: o efeito não é específico de venda nova (17/09/2026)

Depois da revisão independente (§9g), corrigi dois defeitos e o resultado principal mudou de leitura.
Script: [nucleo_corrigido.py](scripts/nucleo_corrigido.py) · saída `data/nucleo_corrigido.txt`.

**Correções aplicadas:** (1) série de origem **completa** — os 95 dias que faltavam foram recuperados
dia a dia (`youtube-analytics/fetch_origem_diario.py`), e eles tinham **mais** audiência que a média,
então a censura era correlacionada com o tratamento; (2) **moving-block bootstrap** no lugar do iid.

### Com a série completa e bootstrap correto, o efeito bruto é maior

| Desfecho (262 dias, sem abertura nem fechamento) | Efeito | IC95 (bloco L=14) | p |
|---|---:|---|---:|
| Transações não-renovação | **+19,5%** | [+8,6, +42,4] | 0,004 |
| Receita | +18,0% | [−2,9, +48,6] | 0,114 |
| CAC de ads (**o mesmo fato**) | −13,7% | [−25,0, −6,6] | 0,007 |
| Spend [checagem do pareamento] | +1,2% | [−3,7, +10,7] | 0,29 |

Robusto a L = 7, 14, 21 e 28 dias. Com 313 dias era +15,8%.

### Mas as renovações — cobranças automáticas — sobem quase igual

**98,8% das renovações são no cartão**, cobrança automática na data de aniversário da assinatura.
Um vídeo publicado hoje **não pode causar** uma cobrança automática de hoje. Regressão com efeito
fixo de dia da semana, **dia do mês**, mês×ano e log(spend), HAC-14, 262 dias:

| Série | Elasticidade à audiência | IC95 | p |
|---|---:|---|---:|
| Não-renovação (o desfecho do estudo) | **+0,174** | [+0,085, +0,263] | <0,001 |
| ⊗ **Renovação no cartão (automática)** | **+0,116** | [−0,021, +0,253] | 0,096 |
| Renovação manual (boleto/pix, 1,2%) | +0,164 | [−0,049, +0,378] | 0,13 |
| **Razão: nova ÷ renovação cartão** | **+0,058** | **[−0,109, +0,224]** | **0,50** |

**A razão não responde.** Ou seja: em dia de audiência alta sobem, na mesma proporção, tanto as
vendas novas quanto cobranças que o vídeo não pode ter causado. A parte do efeito que é **específica
de venda nova** — a única que o YouTube poderia gerar — **não se distingue de zero**.

O dia do mês não explica (Kruskal-Wallis p=0,87 para renovações por faixa do mês; audiência por faixa
do mês p=0,59). O que resta é um **fator comum de nível de dia**.

### Leituras possíveis, não separáveis com este dado

1. **Confundidor de dia** (a hipótese que o estudo nunca conseguiu descartar): algo move junto a
   audiência e o volume total de transações do dia, inclusive processamento de cobrança.
2. **Mecânica de coorte**: quem foi adquirido em dia de audiência alta há 12 meses renova hoje em
   dia de padrão semelhante. Nesse caso a renovação é **desfecho defasado**, não controle — e o
   teste não é válido, mas também não salva a conclusão causal.
3. **Controle grosseiro**: a renovação varia **14,8×** por dia da semana; dummies de DOW podem não
   bastar.

### Efeito prático

- **A associação continua real e forte** (+19,5% de transações, IC [+8,6, +42,4], p=0,004, com spend
  pareado). Isso não mudou.
- **A interpretação de que o YouTube causa venda nova perdeu o principal teste que a sustentaria.**
  Antes o estudo dizia "não conseguimos descartar um fator comum"; agora há **medida** de que esse
  fator explica a maior parte do movimento.
- Qualquer apresentação deve dizer: *dias de audiência alta são dias de mais venda, mas também de
  mais cobrança automática — o padrão é de "dia bom" no agregado, não de efeito do vídeo.*
- Isso **eleva** a prioridade do experimento (§9g): sem randomização, este dado não separa.

## Métrica proposta

> ⛔ **OBSOLETA (17/09/2026).** Esta seção recomenda (a) o **proxy do GA4 Organic Video**, que tem
> ρ 0,43 com a audiência real (§9b.1), e (b) a regra "se o YT está alto há espaço para escalar",
> **retirada pela §9d** (a audiência não muda o retorno marginal) e agora sem sustentação causal
> (§9f). **Não usar em painel nem em apresentação.** A métrica que resta defensável é descritiva:
> minutos assistidos e inscritos ganhos do canal como leitura de **regime do dia**, sem implicação
> de decisão de mídia. Reescrever quando o experimento (§9g) der resposta.


Duas, uma para cada pergunta.

### (a) Termômetro diário: sessões de YouTube orgânico (GA4 Organic Video)

O indicador de relevância com sinal limpo em volume **e** eficiência. Lido como desvio da média
móvel de 28 dias, dentro da faixa de spend corrente. Dias no topo entregam +25% de transações e
CAC ~12% menor com o mesmo dinheiro — ⚠️ **com lançamentos incluídos** (rodada 8): fora das
janelas de estreia sobra +18,9% de volume, CAC −6,8% (p=0,05) e conversão por sessão nula.
**Não substituir por engajamento de rede social** — esse
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

1. ✅ (02/09/2026, Teste A) **É formato, não pauta**: lift não escala com notoriedade (direção
   até oposta — Marçal/Renan sem lift, confundidos pela estreia tardia na plataforma) e
   sabatinas pooled = BP Entrevista em taxa pareada (1,61× = 1,61×). Novo gotcha operacional:
   estreia tardia na plataforma (replay frio pós-YouTube) zera a ativação.
2. 🔶 (02/09/2026, Teste B) **Médio prazo: incremento real até D+60** (leve 1,64× estável,
   freemium nulo). Falta o D+90: **reexecutar `queries/25_janelas_medio_prazo.sql` após
   ~05/10/2026** (universo completa 90d de follow-up em 01/10).
3. **YouTube Analytics**: a sabatina acontece no YouTube; views/inscritos ficam fora do BQ e do
   GA4. Sem isso, o lado "atenção" da medição é parcial. Pedir acesso ao YT Analytics.
4. **Freemium negativo** (0,28–0,83×) é direcionalmente consistente em 3 estratos mas n pequeno
   (102–486 pessoa-dias). Vale reconferir em 2–3 meses com mais volume.
5. ✅ (02/09/2026) Publicado como relatório HTML no portal (seção Mídia Paga, badge Snapshot). O acompanhamento recorrente do IAC segue em aberto (Fase 3 do plano).
6. ✅ (11/09/2026, rodada 8) Revisão da Bárbara atendida: conclusão em 2 parágrafos, teste de
   fechamento de lote (não é confundidor) e exclusão de lançamentos (conversão zera; volume
   +18,9% resiste).
7. ⚠️ `tb_campaign_period` está incompleta — faltam DOM, ELS, CDL, EVG, ODI e ENE (2026). Afeta
   qualquer análise que use `campanhas_periodos.csv`/`em_venda`. Corrigir a tabela no BQ; o
   script da rodada 8 usa calendário hardcoded da wiki como paliativo.
9. 🔶 (14/09/2026, rodada 9a) **Auditoria concluída — correções ao publicado aguardam André** (tabela
   "O que muda" na rodada 9a): freemium "nulo"→"sem evidência", médio frágil, estreia tardia
   provisória, "+24,7% E CAC −11,9%" como um fato, lag em nível, IAC com n mínimo de compradores.
10. 🔲 (rodada 9b) Sabatinas Renan/Marçal em D+14/D+30 (cutoff 13/09) · 11 de Setembro pessoa-dia
   com calendário pareado + decomposição UTM do fim de semana 12–13/09 · teste da hipótese
   "todo o efeito é BP10" · GA4 Organic Video de setembro · YouTube Studio (bloqueado).
8. Fechamentos de lote intermediários (dentro da janela de venda) não existem em nenhuma tabela —
   só o fim da venda foi testável. Se o Comercial tiver as datas de virada de lote, dá para
   refinar o teste da rodada 8.

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
| [17_spend_vendas_por_campanha_diario.sql](queries/17_spend_vendas_por_campanha_diario.sql) | Campanha-dia para saltos de mCAC (rodada 3) | ✅ |
| [18_busca_marca_google_ads.sql](queries/18_busca_marca_google_ads.sql) | Cliques/impressões [KW] Institucional (rodada 4) | ✅ |
| [19_zenvia_contatos_novos.sql](queries/19_zenvia_contatos_novos.sql) | Contatos novos/inbound Zenvia (rodada 4) | ✅ |
| [20_receita_mensal_historico.sql](queries/20_receita_mensal_historico.sql) | Receita mensal 59 meses (rodadas 5–6) | ✅ |
| [21_sabatinas_inventario.sql](queries/21_sabatinas_inventario.sql) | Inventário das 9 sabatinas: estreia e pessoa-dias (teste A) | ✅ |
| [22_lift_por_sabatina.sql](queries/22_lift_por_sabatina.sql) | Lift D+14/D+7 por sabatina individual (teste A) | ✅ |
| [23_lift_bp_entrevista.sql](queries/23_lift_bp_entrevista.sql) | Lift por episódio da BP Entrevista (teste A) | ✅ |
| [24_censura_sabatinas.sql](queries/24_censura_sabatinas.sql) | Elegibilidade por janela / censura à direita (teste B) | ✅ |
| [25_janelas_medio_prazo.sql](queries/25_janelas_medio_prazo.sql) | Lift D+14/30/60/90 no universo fixo (teste B) | ✅ (D+90: reexecutar após ~05/10) |
| [26_sensibilidade_periodo_amplo.sql](queries/26_sensibilidade_periodo_amplo.sql) | Sensibilidade com comparador mar–jul (teste B) | ✅ |
| [27_cluster_robusto_q14.sql](queries/27_cluster_robusto_q14.sql) | Variância clusterizada por pessoa do teste principal (rodada 9a) | ✅ |
| [28_cluster_robusto_q25.sql](queries/28_cluster_robusto_q25.sql) | Idem para o Teste B, 3 janelas (rodada 9a) | ✅ |
| [29_spend_google_video_diario.sql](queries/29_spend_google_video_diario.sql) | Spend Google por tipo ([YT]/PMax/display/marca) p/ teste de contaminação (rodada 9a) | ✅ |
| [31_lift_por_sabatina_d14_set.sql](queries/31_lift_por_sabatina_d14_set.sql) | Query 22 com compras até 15/09 — D+14 das 9 sabatinas (rodada 9b) | ✅ |
| [32_lift_11setembro_plataforma.sql](queries/32_lift_11setembro_plataforma.sql) | Pessoa-dia do doc 11 de Setembro (exposição 11–12/09, D+3) — reexecutar 19/09 (D+7) e 26/09 (D+14) | ✅ parcial |

Scripts:
- [event_study.py](scripts/event_study.py) — painel diário, contrafactual e placebo (rodada 1)
- [detectar_picos.py](scripts/detectar_picos.py) — IRO e picos históricos de atenção
- [relevancia_vs_vendas.py](scripts/relevancia_vs_vendas.py) — correlação bruta vs parcial, lags, direção, semanal + Trends
- [quantificar_relevancia.py](scripts/quantificar_relevancia.py) — quartis de relevância em termos de negócio
- [teste_pareado_spend.py](scripts/teste_pareado_spend.py) — **teste decisivo** (pareamento por spend × DOW × fase)
- [teste_pareado_sem_lancamento.py](scripts/teste_pareado_sem_lancamento.py) — robustez da rodada 8: exclui janelas de lançamento e fechamento de lote (calendário corrigido da wiki)
- [nucleo_corrigido.py](scripts/nucleo_corrigido.py) — **rodada 9f: núcleo com série completa, block bootstrap e controle negativo de renovações (o teste que falha)**
- [r9d_curva_direcao.py](scripts/r9d_curva_direcao.py) — rodada 9d: balanço da célula de spend alto, nível vs inclinação da curva, histerese (subindo/descendo), mCAC por estado
- [r9c_insights.py](scripts/r9c_insights.py) — rodada 9c: duração do efeito (lags), dose-resposta, heterogeneidade por canal, interação com spend, assimetria, estoque de inscritos, vídeos gigantes, tipo de conteúdo
- [r9b_youtube_real.py](scripts/r9b_youtube_real.py) — rodada 9b: audiência real do YouTube (Analytics) × vendas: crivo, pareado, lag, jun–set semanal, dias dos vídeos-case
- [auditoria_r9a.py](scripts/auditoria_r9a.py) — rodada 9a: decomposição volume×CAC, MDE, estabilidade do IAC, cluster por pessoa, contaminação de vídeo pago, mix de campanha, persistência/lag, remarketing, autocorrelação (saída `data/r9a_auditoria.txt`)

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

- `wiki-bp/pages/metricas-referencia.md` — nova seção "Ativação por conteúdo (IAC-14)";
  11/09: caveat de lançamento na tabela de canais orgânicos.
- `wiki-brasil-paralelo/pages/relevancia-marca.md` — criada, achados de relevância/ativação;
  11/09: veredito da hipótese revisado (conversão = fenômeno de lançamento) + gotcha da
  tb_campaign_period.
- `wiki-bp/pages/bq-regras.md` — gotcha de causalidade reversa em análise conteúdo→venda.
- `wiki-brasil-paralelo/pages/campanhas-calendario.md` — 11/09: aviso de que a
  tb_campaign_period não tem DOM/ELS/CDL/EVG/ODI/ENE.

## Para retomar (17/09/2026 — pós-revisão independente; NÃO apresentar 9c–9e)

**Estado:** a associação é real (+19,5% de transações, IC [+8,6, +42,4], p=0,004, série completa de
408 dias, block bootstrap, spend pareado). **A causalidade perdeu sustentação**: o controle negativo
de renovações falha (§9f) e a revisão independente derrubou tudo que foi construído nas rodadas
9c–9e (§9g). Prazo com a Bárbara era 18/09 — entregar o núcleo + os blocos que ela pediu, sem os
achados derrubados.

**Correções pendentes (ordem):**
1. Trocar o bootstrap iid por **moving-block** em `teste_pareado_spend.py`, `teste_pareado_sem_lancamento.py`,
   `r9b_youtube_real.py`, `r9b_calendario_completo.py`, `r9c_insights.py`, `r9d_curva_direcao.py`
   (padrão já implementado em `nucleo_corrigido.py`).
2. **Refazer os números das rodadas 9b–9e com a série completa** — a censura de 27% dos dias mudou o
   principal de +15,8% para +19,5%; todos os demais precisam ser recomputados ou marcados como obsoletos.
3. Corrigir os bugs listados na §9g: placebo de `r9c_insights.py:159`, resíduo de CAC imputado (:77,154),
   CAC infinito (:140-142), **`tx_organico` mudando de definição em 20/08 (:25)**, seleção por `Δtx>0`
   em `r9d_curva_direcao.py:122`.
4. **Escrever e commitar o script da §9e** (hoje só há query e CSV) e o da decomposição do Comercial
   (§9c.1) — ou retirar os dois achados.
5. Aplicar **FDR** à família de p-valores e republicar só o que passa.
6. Reescrever a §Métrica proposta (marcada obsoleta) e a §Resposta curta (a frase "resistência piorou"
   não se sustenta ponderada por spend — ver §Escala de mídia 07–13/09).
7. `index.html` in-place com o estado corrigido; hoje o publicado é de 02/09 e está desatualizado.

**Análises agendadas por data:** D+7 do 11 de Setembro em **19/09** e D+14 em **26/09**
(`queries/32_lift_11setembro_plataforma.sql`, trocar a janela). D+90 do Teste B após **05/10**
(`queries/25_janelas_medio_prazo.sql`).

**Experimento (o que de fato resolve):** encorajamento aleatorizado na base — sortear metade para
receber push/e-mail apontando ao vídeo, medir compra D+1..D+14 por intenção de tratar. Detecta 1,2×.
Desenho a escrever; depende do squad de CRM.

**Acessos:** YouTube (Data + Analytics) e Instagram funcionando — ver `wiki-bp/youtube-instagram-acesso.md`.
**Search Console pendente** (pedir acesso; histórico só 16 meses). **Coleta ainda manual** — agendar
launchd 9h com os 3 scripts de YouTube + o do Instagram, senão a série de seguidores do IG se perde.

**Pendências operacionais herdadas:** rodada 8 e tudo desta sessão **não commitados**; thread do
#performance-e-bi sem resposta desde 11/09; patch da `api-mappings` aguardando André aplicar na Lovable.
