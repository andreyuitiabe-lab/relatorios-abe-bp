# High-ticket: por que o CAC subiu — Travessia (2023) → BP10 (2026)

**Data:** 2026-09-17 | **Status:** concluída (relatório vivo) · **revisado por agente independente
em 17/09** — 6 erros corrigidos e 2 testes de robustez incorporados (ver §Revisão independente)
**Relatório:** [index.html](index.html)
**Pedido (André):** nos últimos anos lançamos produtos de alto ticket. No começo vendíamos bem
com CAC baixo e alta eficiência de CRM; ultimamente dependemos mais de anúncios e o CAC subiu.
Entender se **(1)** fizemos algo diferente, **(2)** o perfil do público está saturando, ou
**(3)** tínhamos demanda reprimida que está se esgotando.

Campanhas: Travessia, Travessia relançamento, BNO24, Bitcoin 1, Bitcoin 2, BNO25, CDL, ODI, BP10.

---

## Decisões de abordagem

**Janelas e universo.** Cada campanha é medida em três universos (`rastro`, `janela`, `produto`)
e só um vale como principal — a margem de erro de uma campanha é a regra de atribuição, não o
dado (mesma lição de `relatorios/atribuicao-filmes`). Detalhe e justificativa no cabeçalho de
[queries/01_universo_compradores.sql](queries/01_universo_compradores.sql).

| Campanha | Janela | Universo principal | Por quê |
|---|---|---|---|
| TRA — Travessia | 01/04 → 31/05/2023 | rastro | inclui Mecenas Travessia (R$ 1,57 mi), que é da campanha |
| TRA2 — Travessia 2ª turma | 01/04 → 31/05/2024 | rastro | idem |
| BNO24 — Black November 2024 | nov/2024 | janela | promoção do catálogo inteiro |
| BIT — Cert. Bitcoin 1 | 09/04 → 31/05/2025 | rastro | monetiza em upsell de Black; produto puro perde 70% |
| BNO25 — Black November 2025 | nov/2025 | janela | promoção do catálogo inteiro |
| DBI — Cert. Bitcoin 2 | 04/02 → 31/03/2026 | rastro | idem BIT |
| CDL — Clube do Livro | 05/05 → 30/06/2026 | rastro | inclui Black Vitalício do cashback |
| BP10 — BP 10 Anos | 11/06 → 15/09/2026 | rastro | convive com ODI e CBR na mesma janela |
| ODI — Odisseia | 17/07 → 16/09/2026 | rastro | inclui upsell Black do cashback |

**Validações do universo** (o método reproduz as referências conhecidas):

| Medida | Esta análise | Referência | Fonte da referência |
|---|---|---|---|
| BNO24 receita | R$ 40,28 mi | R$ 40,33 mi | planilha do time de tráfego |
| BNO25 receita | R$ 18,72 mi | R$ 18,83 mi | planilha do time de tráfego |
| BIT compradores / receita | 1.549 / R$ 2,61 mi | 1.540 / R$ 2,6 mi | `relatorios/aquecimento-vendas` |
| DBI receita | R$ 0,22 mi | R$ 244 k | `campanhas-contexto.md` |
| Base ativa em 01/04/2023 | 558.624 | 558.769 | `cbo_daily_members` (pagantes ativos) — ⚠️ ver ressalva abaixo |

**Status do comprador** (membro / ex-membro / não-membro) avaliado na data da primeira compra da
campanha, com **whitelist de membership** — sem ela todo comprador de livro viraria "membro",
porque `dim_subscriptions` grava produto avulso (CDL, Odisseia, Travessia, certificações) como
assinatura ativa. Legados `patriota` (304k) e `bp-select` entram como membership; os clubes de
conteúdo de 2021 não.

⚠️ **Correção importante (revisão de 17/09) — a whitelist NÃO reproduz o indicador oficial.**
A versão anterior afirmava isso com base numa única data (01/04/2023: 558.624 vs 558.769).
Testando em 3 datas, quem reproduz o `cbo_daily_members` é a contagem **sem whitelist nenhuma**:

| data | com whitelist | **sem whitelist** | oficial |
|---|---|---|---|
| 2023-04-01 | 558.624 | **558.752** | 558.769 |
| 2024-11-01 | 464.794 | **465.356** | 465.367 |
| 2026-07-17 | 610.639 | **635.343** | 635.355 |

A whitelist coincidia com o oficial em 2023 **só porque produto avulso quase não existia então**.
Em jul/2026 ela exclui `clube-do-livro` (23,4k), `teller` (19,1k), `funil-bitcoin` (8,1k) e outros —
e fica **3,9% abaixo** do oficial.

**A whitelist continua sendo a escolha certa** para classificar membro/ex/não-membro (sem ela o
comprador de CDL vira "membro" pelo próprio ato de comprar). O que não se sustentava era a
validação. **Consequência para o achado 4:** a distância do denominador em relação ao oficial cresce
de ~0% (2023) para 3,9% (2026) ao longo da própria série usada para argumentar saturação — a
penetração de 2026 está inflada ~4% contra a de 2023. Os 11,9% do BP10 seriam ~11,5% na base oficial.
A direção do achado sobrevive; a magnitude tem essa deriva embutida.

⚠️ Nota relacionada: a série anual (`data.json.anual`) usa `cbo_daily_members` como base, enquanto o
consolidado por campanha usa a whitelist. São duas bases diferentes no mesmo relatório, de propósito
(uma é indicador oficial da casa, a outra precisa excluir produto avulso) — mas não devem ser
comparadas entre si.

**CAC** = mídia ÷ compradores da campanha (decisão do André). Reportado também o CAC só de
não-membro, como leitura de aquisição pura.

---

## Cobertura de dados — o que dá e o que não dá para medir

| Fonte | Cobertura real | Consequência |
|---|---|---|
| Spend Meta (warehouse) | desde **ago/2025** | não serve para TRA, TRA2, BNO24, BIT |
| Spend Meta (**Marketing API**) | desde **17/08/2023** (limite de 37 meses) | resolve tudo menos a Travessia original |
| Spend Google / PMax (warehouse) | desde **jan/2025** | TRA, TRA2 e BNO24 sem Google auditável |
| Planilha do time de tráfego | custo e faturamento por lançamento até BNO25; **nada de 2026** | única fonte para TRA (abr–mai/2023) |
| CRM (Insider) | desde **30/01/2024** | Travessia (2023) sem CRM medível |
| Zenvia (abordagens) | desde **28/09/2022** | cobre todas as campanhas |

⚠️ A Travessia original é a única campanha sem spend granular. Para ela o custo vem da planilha do
time de tráfego (aba matriz, coluna `TRA-2023`), e a verba usada é a **soma de três linhas**:

| linha da planilha | valor |
|---|---|
| Investimento em captação | R$ 178.970,39 |
| Investimento em lembrete/nutrição | R$ 35.845,38 |
| Investimento em venda | R$ 655.000,00 |
| **total usado como verba da TRA** | **R$ 869.815,77** |

Esse número comanda o CAC (R$ 179) e o ROAS (9,20×) da campanha-âncora da narrativa "no começo
vendíamos bem com CAC baixo", então precisa estar declarado — a versão anterior citava só os
R$ 178.970 da captação, e quem refizesse a conta com eles chegaria a um CAC de R$ 36,85.
**A planilha não está no repo: este é o único insumo de custo da análise que não é verificável no
warehouse.** O que dá para checar é o outro lado: a mesma planilha diz faturamento de R$ 8,10 mi e
o warehouse mede R$ 8,01 mi (1,2% de diferença), o que dá confiança na linha, não no número.

---

## Achados principais

### Enquadramento — duas alavancas, dois donos (correção do André, 17/09)

⚠️ **O anúncio dessas campanhas não vende um produto: compra atenção para a campanha inteira, e
quem decide o que a pessoa leva é a oferta.** Isso não é detalhe — é o que define qual pergunta os
números conseguem responder.

Consequência: a mídia compra **comprador**; a oferta define o **ticket**. E isso dá uma identidade
exata (não aproximação), que confere na 2ª casa decimal nas nove campanhas:

> **ROAS = ticket médio ÷ CAC** &nbsp;&nbsp; porque receita ÷ verba = (compradores × ticket) ÷ (compradores × CAC)

| Alavanca | Dono | BNO24 | BP10 |
|---|---|---|---|
| **CAC** — custo de trazer um comprador | mídia | R$ 186 | R$ 426 |
| **Ticket** — quanto ele paga | oferta | R$ 1.374 | R$ 1.003 |
| **ROAS** | os dois | 7,37× | 2,35× |

**Decomposição logarítmica da queda do ROAS.** Em dois fatores: **72% do movimento é CAC, 28% é
ticket**. Mas como o CAC é ele próprio `CAC_canal × share` (achado 0), a decomposição fiel tem
**três** fatores — e ela mostra uma coisa que a de dois esconde:

| fator | Δ log | % do movimento líquido | direção |
|---|---|---|---|
| **share de mídia** (mix de canal) | −0,969 | **85%** | contra |
| **ticket** (oferta) | −0,315 | 28% | contra |
| **CAC do canal mídia** (preço) | +0,142 | −12% | **a favor** |
| soma | −1,140 | 100% | ROAS 7,37× → 2,35× |

O "72% é CAC" agrega num só termo um efeito de **mix (85%)** e um **ganho de preço (−12%)**. Em
termos de responsabilidade: a conta que chega na mídia é majoritariamente mix, e o preço que ela
controla melhorou. (Normalizando pela soma dos valores absolutos em vez do líquido: 68% / 22% / 10%.)

⚠️ **Limite da decomposição de dois fatores:** `ticket` e `CAC` compartilham o mesmo denominador
(compradores), que cancela em `ROAS = receita ÷ verba`. Trocando o denominador por transações, o
split muda. Os 72/28 não são falsos, são **dependentes da escolha da unidade** — por isso a versão
de três fatores, ancorada na identidade do achado 0, é a que vale.

Uma alavanca não compensa a outra: para o BP10 empatar o ROAS do BNO24 só com ticket, teria que
vender a **R$ 3.141**.

**O que esse enquadramento invalida:** falar em "CAC do vitalício" como custo de aquisição.
Ninguém comprou mídia de vitalício. O achado 7 (rateio por produto) continua no relatório, mas como
leitura de **P&L e de resultado da oferta** — onde o faturamento caiu e quanto do custo cada família
carrega —, não como custo de adquirir cada produto.

---

### 0. O CAC subiu por mix de canal, não por preço de mídia — e isso é uma identidade aritmética

`CAC = (verba ÷ compradores) = (verba ÷ compradores de mídia) × (compradores de mídia ÷ total)`

Comparando as duas campanhas que vendem a mesma coisa (vitalício para a base) — e são mesmo
comparáveis: o vitalício é **93,4% da receita do BNO24 e 76,5% da do BP10** (achado 7):

| | BNO24 (nov/2024) | BP10 (jun–set/2026) |
|---|---|---|
| CAC do canal mídia | R$ 979 | **R$ 849 (−13%)** |
| Fatia de compradores vinda de mídia | 19,1% | **50,2% (2,6×)** |
| **CAC médio** | **R$ 186** | **R$ 426 (+129%)** |
| CPM | R$ 35,07 | **R$ 18,39 (−48%)** |
| CPC | R$ 1,73 | **R$ 0,35 (−80%)** |
| **Conversão clique → compra** | **0,176%** | **0,041% (−77%)** |

⚠️ **O contrapeso, que a versão anterior omitiu (revisão de 17/09):** `CAC do canal = CPC ÷ conversão`
(1,73 ÷ 0,00176 = 983 ≈ 979 ✓). Os −13% do CAC de canal são o **líquido** de um clique 80% mais
barato contra uma conversão 77% pior. Publicar CPM e CPC sem a conversão faz a mídia parecer bem
melhor do que o próprio dado diz. O CTR implícito triplicou (2,03% → 6,23%) — assinatura de
deslocamento para inventário de atenção barata, não de ganho de eficiência.

⚠️ **E o CPM não é comparável entre as duas:** o BNO24 é Meta puro (o warehouse só tem Google/PMax
desde jan/2025) e o BP10 tem R$ 1,02 mi de PMax a CPM 12,24 puxando a média para baixo. Meta contra
Meta o CPM cai **−43,4%**, não −48%. O CPC sobrevive à correção (−81,5% Meta contra Meta).

Adquirir um comprador *pela mídia* ficou um pouco mais barato. O CAC médio subiu porque a mídia
deixou de ser o complemento e virou o motor — o denominador "de graça" (Comercial + CRM) encolheu.

⚠️ **ROAS é a métrica comparável, não CAC.** Campanhas com ticket diferente não têm CAC comparável:
o BNO25 tem o melhor CAC da série (R$ 104) e é a pior campanha de vitalício, porque vendeu assinatura
de R$ 345 em vez de vitalício de R$ 1.374. ROAS por campanha: TRA 9,20× · BNO24 7,37× · CDL 6,89× ·
ODI 3,68× · BNO25 3,33× · TRA2 2,64× · BP10 2,35× · BIT 2,03× · DBI 1,31×.

### 1. A dependência de anúncios é real — mas o degrau foi em 2024, não uma deriva de três anos

Participação da **mídia paga** na receita da campanha:

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| Mídia paga | 5,2% | 10,7% | 13,5% | 6,3% | 24,9% | 23,5% | 33,5% | **53,3%** | 26,9% |
| Comercial | 68,2% | 73,4% | 51,6% | 76,1% | 59,7% | 41,6% | 48,0% | **26,5%** | 46,6% |
| CRM | 21,6% | 10,1% | 26,5% | 9,6% | 5,6% | 20,9% | 14,2% | 14,1% | 22,1% |

O high-ticket começou como produto de **Comercial** (68–76% da receita) e o BP10 já é um produto
de **mídia** (53,3%).

#### Os dois testes de robustez (revisão de 17/09) — um sustenta, o outro limita

**Teste 1 — o salto é artefato da regra de universo? Não.** Cada campanha existe em dois universos
na `tb_ht_compradores`. Medindo com a **mesma** regra dos dois lados:

| share de mídia (compradores) | BNO24 | BNO25 | CDL | BP10 | ODI |
|---|---|---|---|---|---|
| regra `janela` | 19,1% | 47,8% | 49,6% | **49,2%** | 49,4% |
| regra `rastro` | 18,8% | 57,1% | 34,3% | **50,2%** | 29,9% |

Sob `janela` (idêntica nos dois extremos) o share vai de 19,1% para 49,2%. **O salto não vem da
escolha de regra.** Este teste faltava e sustenta a tese.

**Teste 2 — o BNO24 é linha de base ou outlier? É outlier, e isso muda a moldura.**
Mix de canal de **toda** venda nova da casa, mês a mês, mesma regra de canal:

| | abr/23 | mai/23 | ago/24 | set/24 | out/24 | **nov/24** | dez/24 | nov/25 | ago/26 | set/26 |
|---|---|---|---|---|---|---|---|---|---|---|
| % mídia | 27,7 | 22,7 | 47,8 | **64,3** | 48,0 | **19,8** | 71,0 | 48,4 | 54,2 | 45,8 |
| % comercial | 46,8 | 55,1 | 13,3 | 9,3 | 12,0 | **41,3** | 9,5 | 26,3 | 22,5 | 27,8 |

**Nov/2024 é o mês de MENOR participação de mídia de todo 2024.** A casa deu um **degrau** para
mídia em meados de 2024 (ago–set/2024 saltam para 48–64%) e opera em ~45–55% desde então.

⚠️ **Isso corrige a moldura da versão anterior.** Não houve "troca de motor ao longo de três anos":
a casa já era mídia-first desde meados de 2024, e o **BNO24 foi uma mobilização excepcional do
Comercial** contra esse patamar. A frase "o BP10 já é um produto de mídia (53,3%)" descreve a casa
inteira em 2026, não algo específico do BP10.

**A pergunta acionável muda junto.** Não é "por que a mídia cresceu" — é **"por que o Comercial não
foi mobilizado de novo como em nov/2024"**: mesmo time (51 vendedores com venda no BP10 contra 37 no
BNO24), **46% menos abordagens por dia** (5.228 → 2.805), com o mesmo tipo de oferta (vitalício).
É a única das três hipóteses do pedido que tem dono e alavanca.

⚠️ Um efeito menor na mesma direção da tese: a cobertura de rastreio melhorou (`sem_rastro` caiu de
6–14% em 2023–24 para 3–5% em 2025–26), o que empurra share para canais nomeados. Poucos pp.

### 2. O BNO25 não foi saturação — foi outra oferta

A queda do Black November (**R$ 56,4 mi em 2023 → R$ 40,3 mi em 2024 → R$ 18,7 mi em 2025**, tudo
venda nova) não é o mesmo produto vendendo menos:

⚠️ **Correção (revisão de 17/09):** a versão anterior citava R$ 66,6 mi em 2023. Aquele número é o
total **com renovação** (R$ 10,2 mi de renovação + R$ 56,4 mi de venda nova) e vinha da wiki, onde
está na régua errada para comparar com BNO24/BNO25, que são `bl_is_renovation = FALSE`. Na mesma
régua a queda 2023→2024 é **−28,6%**, não −39,5%.

| | BNO24 | BNO25 |
|---|---|---|
| Receita | R$ 40,28 mi | R$ 18,72 mi |
| Ticket médio | R$ 1.374 | R$ 345 |
| Vitalícios vendidos | **18.553** (R$ 37,6 mi, 93,4% da receita) | **1.939** (R$ 6,76 mi, 36,1%) |
| Oferta (planilha do tráfego) | "Vitalício. Começo do Black" | "Originais por R$ 7,90 e 70% off no premium" |

O BF de 2025 **não vendeu vitalício** — vendeu entrada barata. Comparar o CAC das duas como se
fossem a mesma campanha é comparar produtos diferentes. Em 2026 o motor de vitalício voltou, mas
no aniversário (BP10: R$ 14,3 mi dos R$ 18,7 mi são vitalícios).

⚠️ **O "melhor CAC da série" do BNO25 (R$ 104) é artefato de mix.** Ele vendeu 50.997 assinaturas
de R$ 206 e só 1.939 vitalícios. Separando o produto (achado 7), o CAC de vitalício dele é
**R$ 1.046 — o pior da série** sob rateio por receita. Não usar o R$ 104 como benchmark.

### 3. O Comercial responde menos — mas a queda não é monotônica

Taxa de resposta às abordagens do Zenvia (grupo Comercial, janela da campanha):

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| Abordagens/dia | 2.559 | 1.172 | 5.228 | 3.862 | **9.726** | 5.688 | 3.344 | 2.805 | 3.066 |
| % com resposta | **73,8%** | 44,6% | 43,8% | 51,1% | 31,9% | **25,5%** | 42,1% | 36,6% | 31,4% |

⚠️ **Correção (revisão de 17/09):** a versão anterior chamava essa queda de "monotônica" e a própria
tabela desmente — há três subidas (BNO24→BIT +7,3pp, BNO25→BP10 +4,7pp, DBI→CDL +16,6pp). O que se
sustenta é: **caiu ~40pp entre as pontas**, de forma irregular. O par limpo (mesmo mês do ano, mesma
promoção) é BNO24 43,8% → BNO25 31,9%.

Em 2023 três de cada quatro abordagens viravam conversa; em 2026 é uma em três. O canal que
sustentava o high-ticket ficou mais caro **em trabalho**, não em mídia.

### 4. A base já não é virgem, mas o estoque não acabou

| | TRA (abr/23) | BNO24 (nov/24) | BNO25 (nov/25) | BP10 (jun/26) | ODI (jul/26) |
|---|---|---|---|---|---|
| Base ativa pagante | 558.624 | 464.794 | 726.562 | 607.138 | 610.639 |
| % da base que já tem high-ticket | **1,5%** | 7,8% | 8,9% | 11,9% | **12,3%** |
| Compradores em 1ª compra high-ticket | 81,3% | 89,0% | 97,0% | 92,8% | 42,6% |
| Penetração do estoque na campanha | 0,59% | **2,37%** | 0,85% | 0,43% | 0,13% |

**O sinal de esgotamento está na reincidência, não no estoque.** % dos compradores que já haviam
comprado numa campanha high-ticket anterior desta série: TRA 0% · BNO24 2,9% · BNO25 3,1% ·
DBI 4,9% · BP10 6,6% · TRA2 7,8% · BIT 11,0% · **CDL 16,7% · ODI 50,7%**. Na Odisseia, a maior
origem única é o **Clube do Livro, com 40,8%** dos compradores — os lançamentos de livro de 2026
estão girando o mesmo público.

⚠️ **Duas correções (revisão de 17/09):** (1) a versão anterior dizia "a Odisseia vendeu mais da
metade para a carteira do CDL" — os 50,7% são a união de **todas** as campanhas anteriores; o CDL
sozinho é 40,8%. (2) o cálculo usava a ordem das campanhas (`ord`) em vez da data: como BP10
(11/06–15/09) e ODI (17/07–16/09) se sobrepõem, 115 compradores que compraram o BP10 **depois** do
ODI contavam como anteriores. Corrigido para data — ODI caiu de 54,1% para 50,7% e BP10 subiu para 6,6%.

A penetração de high-ticket na base saiu de 1,5% para 12,3% em três anos — mas ainda sobram
~535 mil membros sem high-ticket. O estoque **não** está esgotado em volume; o que mudou é que
a camada mais fácil já foi convertida (o BNO24 sozinho converteu 2,37% do estoque disponível).

---

### 5. CRM: duas medidas que não se contradizem, mas respondem coisas diferentes

⚠️ **Correção da versão anterior deste memo.** A primeira leitura usou a receita de CRM da *janela
inteira* dividida por *todos* os disparos do período, e concluiu que "o CRM não perdeu eficiência".
Com o corte por **tag da campanha** (só as peças daquele lançamento), o quadro é mais fino:

| Medida | O que mede | Leitura |
|---|---|---|
| Casa inteira, série mensal | todos os disparos ÷ toda a receita CRM | 2026 é o **melhor** período: R$ 25–68 por mil vs R$ 5–21 em 2024–25 |
| Só peças com a tag da campanha | disparos e receita daquele lançamento | **BNO24 R$ 107/mil é o pico da série** e nada chegou perto |

As duas são verdadeiras. O CRM da casa melhorou; o **CRM de campanha de vitalício** não voltou ao
nível de 2024.

Receita por mil disparos com a tag: TRA2 16 · **BNO24 107** · BIT 4 · **BNO25 5,7** · DBI 8 ·
**CDL 56** · BP10 17 · **ODI 49**. O BNO25 disparou **1,9× mais** que o BNO24 (185 mi contra 100 mi)
e rendeu **95% menos por disparo** — é a mesma história da troca de oferta (achado 2), vista pelo CRM.

⚠️ **O push está no denominador e não deveria (revisão de 17/09).** O relatório diz que push é cego
e manda tratá-lo como alcance — e mesmo assim as 55,5 mi de entregas de push (35% do volume do BP10)
entram na conta. Só com e-mail + WhatsApp: **BNO24 107 · CDL 75 · ODI 58 · BP10 26 · BNO25 6,3**.
A conclusão sobrevive (o BNO24 segue o pico), mas a distância BNO24/BP10 cai de **6,5× para 4,2×** —
como o push é zero no BNO24 e um terço no BP10, a métrica com push exagera a deterioração.

⚠️ **Denominador restrito à tag, numerador não.** A cobertura da tag vai de **11,2% (ODI)** a
**89,5% (BNO24)** dos disparos da janela, e os Black November usam universo `janela` (numerador
máximo) enquanto os outros usam `rastro`. Os R$ 107 do BNO24 e os R$ 49 do ODI não são a mesma conta.

**Composição do disparo mudou:** o push saiu de zero (BNO24) para 55 milhões de entregas no BP10
(35% do volume da campanha) — e push **não tem telemetria** de abertura nem clique (140M+ entregues
na casa com ~19 opens). A receita atribuída a ele vem do fallback do modelo. Tratar como alcance,
não como engajamento. Taxa de clique da casa: 0,54% (2024) → 0,14–0,36% (2025–26).

O canal que de fato perdeu eficiência é o **Comercial** (achado 3).

### 6. Economia por canal — o que cada um custa (premissa de comissão de 9%)

Custos por natureza: mídia = verba de anúncio com a sigla; Comercial = **comissão de 9% sobre a
venda** (premissa do André); CRM = disparos com a tag × preço por canal (WhatsApp R$ 0,323 —
fonte canônica `zenvia-custos.md`; e-mail R$ 0,0008; push/in-app zero).

| Campanha | CAC mídia | **ROAS mídia** | CAC Comercial | CAC CRM | ROAS CRM |
|---|---|---|---|---|---|
| BNO24 | R$ 979 | **0,99×** | R$ 153 | R$ 145 | 10,14× |
| BNO25 | R$ 217 | **0,83×** | R$ 69 | R$ 42 | 5,76× |
| CDL | R$ 578 | **2,31×** | R$ 127 | R$ 122 | 11,22× |
| BP10 | R$ 849 | **1,25×** | R$ 98 | R$ 113 | 7,48× |
| ODI | R$ 1.133 | **0,99×** | R$ 121 | R$ 102 | 12,75× |

⚠️ **A coluna de ROAS da mídia estava calculada e não tinha sido publicada (revisão de 17/09).**
Série completa: TRA 0,48 · TRA2 0,28 · BNO24 0,99 · BIT 0,13 · BNO25 0,83 · DBI 0,31 · **CDL 2,31** ·
BP10 1,25 · ODI 0,99. **Em 6 das 8 campanhas mensuráveis a mídia não se paga no last-click.**
Mostrar ROAS só para o CRM (5,76–12,75×) e omiti-lo justamente onde ele é devastador era seleção de
coluna. A ressalva 3 abaixo explica *por que* o número é pessimista — isso é razão para publicá-lo
com a ressalva, não para suprimi-lo. **Com a margem digital de 0,75 (`midia-paga/MARGEM.md`) o piso
de ROAS é 1,33× — só o CDL passa.**

Três ressalvas que precisam andar junto com esses números:

1. **O ROAS do Comercial é 11,11× em todas as campanhas — é aritmética, não achado.** Com custo
   proporcional à receita (9%), o retorno é 1 ÷ 0,09 por construção. Só o CAC dele informa algo.
2. **A comissão é piso.** Não inclui folha dos ~50 vendedores, Zenvia nem estrutura. O custo real
   por comprador do Comercial é bem maior — e é exatamente a parte que não existe no warehouse.
   A comparação mídia × Comercial é, por construção, desfavorável à mídia.
3. **Assimetria de escopo.** A verba de mídia é do lançamento inteiro (inclusive o aquecimento que
   alimentou as vendas dos outros canais); comissão e disparo são custos por venda realizada.
   Onde a mídia faz captação e o Comercial fecha (TRA, TRA2, BIT), o CAC de mídia por último clique
   chega a milhares de reais — ali a leitura correta é o ROAS da campanha inteira.

**Dimensionando o item 2 (sensibilidade no BP10):** foram **51 vendedores com venda** em 3,19 meses
e R$ 445,9 mil de comissão. ⚠️ A definição importa: 51 é `COUNT(DISTINCT nm_salesman)` entre as
vendas comerciais da janela; contando quem **abordou** no Zenvia são **71**. Para custo de folha o
denominador certo é provavelmente 71 (gente trabalhando, com ou sem fechamento), e aí o limiar cai
de R$ 2,7 mil para R$ 1,97 mil por vendedor-mês e o CAC de +R$ 8 mil vai de R$ 385 para **R$ 498** —
ainda abaixo da mídia (R$ 849), com a distância caindo de 2,2× para 1,7×. Bastam **R$ 2,7 mil por vendedor-mês** de custo adicional para o custo do
canal dobrar. Com uma folha total plausível:

| Folha + encargos por vendedor-mês | Custo do canal | CAC do Comercial |
|---|---|---|
| só comissão (o que está no relatório) | R$ 445,9 mil | R$ 98 |
| + R$ 4 mil | R$ 1,10 mi | R$ 242 |
| + R$ 6 mil | R$ 1,42 mi | R$ 313 |
| + R$ 8 mil | R$ 1,75 mi | R$ 385 |

Mesmo no cenário mais caro o Comercial (R$ 385) sai **abaixo da mídia (R$ 849)** no BP10 — mas a
distância cai de 8,7× para 2,2×. **É a conta que falta pedir ao Financeiro**, e ela muda a ordem de
grandeza da conclusão, não o sinal.

---

### 7. O que a oferta entregou — composição de produto e rateio de custo (P&L)

**Levantado a pedido do André (17/09):** o CAC blendado divide a verba por todos os compradores da
janela, e as promoções vendem várias coisas ao mesmo tempo. No BNO24, **10.684 dos 29.313
compradores levaram assinatura de R$ 205**, não vitalício.

⚠️ **Leia esta seção como P&L, não como aquisição.** Pelo enquadramento acima, a mídia não é comprada por
produto — então "CAC do vitalício R$ 690" significa *quanto do custo da campanha o vitalício carrega
no rateio*, não *quanto custou trazer um comprador de vitalício*. O que a composição de produto de
fato mede é o **resultado da oferta**: qual escada o comprador subiu depois de chegar.

Composição da receita (% da campanha):

| | Vitalício | Livro/físico | Certificação | Assinatura | Mecenas/outros |
|---|---|---|---|---|---|
| TRA | — | — | **99,4%** | 0,5% | 0,1% |
| BNO24 | **93,4%** | — | — | 5,5% | 1,2% |
| BNO25 | 36,1% | — | 0,3% | **56,1%** | 7,5% |
| CDL | 6,2% | **90,7%** | — | 3,0% | 0,1% |
| BP10 | **76,5%** | 4,4% | — | 17,6% | 1,6% |
| ODI | 14,9% | **77,0%** | — | 6,2% | 1,9% |

**Convenção adotada: rateio por RECEITA** (decisão do André, 17/09). As outras entram como
sensibilidade, para checar se a conclusão depende da escolha — não depende.

**⚠️ Qualquer rateio de verba por produto é escolha, não dado.** A mídia não separa produto — os
anúncios do BNO24 se chamam `[BNO24] [VENDA] [MEMBROS] ABO Monster`. Não existe "verba do
vitalício". Por isso reporto as convenções possíveis, e **cada uma cega uma métrica por construção**:

| Rateio | Custo da família | Consequência |
|---|---|---|
| por **receita** | verba × (receita da família ÷ total) | ROAS fica **igual** para toda família (= ROAS da campanha); só o CAC separa |
| por **comprador** | verba ÷ total de compradores | CAC fica **igual** para toda família (= CAC blendado); só o ROAS separa |

**CAC do vitalício, BNO24 → BP10** (as duas campanhas em que ele era a oferta central):

| Convenção | BNO24 | BP10 | Variação |
|---|---|---|---|
| **rateio por receita (adotado)** | **R$ 275** | **R$ 690** | **+151%** |
| rateio por comprador (sensibilidade) | R$ 186 | R$ 426 | +129% |
| rateio por transação (sensibilidade) | R$ 185 | R$ 410 | +122% |

O rateio por transação fica colado no por comprador porque quase todo comprador faz uma transação
só: 1,015 tx/comprador no BNO24 e 1,064 no BP10 (a exceção é o CDL, 1,293, por causa dos order bumps).

**As três convenções cercam a alta do CAC do vitalício entre +122% e +151%** — e a de baixo já é
maior que os +129% do número blendado da campanha. **Separar o produto aumenta a alta, não a
suaviza**, e a conclusão central não depende do rateio escolhido, que é o teste que importa.

**O BNO25 é onde a escolha da convenção mais pesa** e por isso ele não entra na comparação acima:
pela convenção adotada (receita) ele tem o **pior CAC de vitalício da série, R$ 1.046** — gastou
R$ 5,6 mi e vendeu 1.939 vitalícios. Pela alternativa (por comprador) o vitalício dele viraria o
**melhor ROAS da série (33,6×)**, porque cada comprador custou R$ 104 e pagou ticket de R$ 3.484.
Registro a leitura contrária porque é a que alguém pode trazer: ela dá crédito à oferta barata que
trouxe 51 mil compradores, enquanto a adotada cobra dele o vitalício que não priorizou.
Em nenhuma das duas o R$ 104 do CAC blendado é benchmark válido.

⚠️ **Mecenas dentro do universo das campanhas (revisão de 17/09).** O BIT tem R$ 284,6 mil de
Mecenas (10,9% da receita da campanha), sendo **uma única transação de R$ 149,9 mil** (5,8% da
campanha inteira); o BNO25 tem R$ 1,26 mi (6,7%). São doações de patrocínio entrando no ROAS de uma
certificação. O rastro é legítimo (`lan_ven-bit`) e o memo justifica Mecenas para a Travessia, mas
não para as outras. Sem os Mecenas o ROAS do BIT cai de 2,03 para ~1,81. Fica como está — mas quem
citar o ROAS do BIT precisa saber que ele tem uma doação de R$ 150 mil dentro.

**Sugestão anterior descartada.** Eu havia proposto pôr o produto no nome da campanha de anúncio
para acabar com o rateio. **Não faz sentido** (apontado pelo André): o anúncio não é do produto, a
campanha vende tudo. Não existe verba de vitalício para separar, e forçar isso criaria um rótulo
falso.

**O que substitui:** medir **ticket por criativo**, não produto por criativo. Cada anúncio traz um
público, e públicos diferentes compram tickets diferentes — essa é a versão respondível da pergunta
("qual anúncio traz gente que compra caro", não "qual anúncio vende vitalício"). É factível hoje:
`nm_pptc_utm_content` carrega o criativo na transação e a Marketing API dá spend por anúncio
(refazer `extrai_meta_api.py` com `level=ad` só nas 9 janelas). Resultado: CAC e ticket por criativo,
que é exatamente a decomposição do enquadramento descida ao nível de decisão de mídia.

---

### 8. Fechando a lista do pedido: anúncios, status do comprador e conversão do Comercial

Auditando o relatório contra a lista de métricas do pedido original, três itens não estavam
entregues. Foram fechados em 18/09.

**Qtd. de anúncios** — anúncios distintos com verba na conta Meta, dentro da janela:

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| Anúncios | — | — | — | — | 690 | 284 | **897** | **1.182** | 506 |
| Campanhas de anúncio (Meta) | — | 8 | 109 | 43 | 81 | 40 | 34 | 52 | 20 |
| Verba por anúncio | — | — | — | — | R$ 6.479 | R$ 536 | R$ 5.393 | R$ 5.840 | R$ 3.166 |

O volume de criativos cresceu junto com a dependência de mídia (284 → 1.182), e a **verba por
anúncio ficou estável** (R$ 5,4–6,5 mil nas campanhas grandes): escalou-se em número de criativos,
não em verba por criativo.

⚠️ **Só 5 das 9, e a razão é externa.** O nome do anúncio só existe no warehouse desde ago/2025.
Para TRA, TRA2, BNO24 e BIT a contagem exige a Marketing API em `level=ad` — o script está pronto
(`scripts/extrai_meta_ads.py`, com janelas e retry), mas **o token da Meta foi invalidado em
18/09/2026** (erro 190 / subcode 460: sessão encerrada por troca de senha ou decisão do Facebook).
Renovado o token, o script fecha as quatro. Google e PMax ficam fora de propósito: PMax não tem
nível de anúncio e o Google do warehouse traz id, não nome comparável.

**Distribuição membro / ex-membro / não-membro** — estava no `data.json` mas só o "% não-membro"
aparecia na página:

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| Membro ativo | **84,8** | 63,3 | 43,9 | 63,3 | 12,8 | 28,1 | 54,7 | 16,9 | 58,0 |
| Ex-membro | 6,7 | 26,4 | 24,1 | 12,8 | 25,2 | 22,3 | 17,8 | **28,3** | 16,4 |
| Nunca foi membro | 8,5 | 10,2 | 32,0 | 23,9 | **61,9** | 49,6 | 27,5 | **54,8** | 25,6 |

A Travessia vendeu para dentro de casa (84,8% membros) e o BP10 vendeu para fora (54,8% nunca foram
membros) — é a história do canal vista pelo outro lado. O BNO25 tem 61,9% de não-membros porque a
oferta era assinatura de R$ 7,90: captação barata, não high-ticket.

**Funil do Comercial completo** — o relatório tinha abordagens e conversas, faltava a conversão:

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| % resposta (abordagem → conversa) | **73,8** | 44,6 | 43,8 | 51,1 | 31,9 | 25,5 | 42,1 | 36,6 | 31,5 |
| **% conversa → venda** | 10,6 | 9,5 | **14,5** | 8,2 | 10,5 | 8,5 | 12,6 | 12,3 | 12,8 |
| % abordagem → venda | **7,81** | 4,22 | 6,34 | 4,17 | 3,36 | 2,18 | 5,29 | 4,51 | 4,03 |

**O funil do Comercial não quebrou no fechamento — quebrou no topo.** A conversão de conversa em
venda ficou estável e até melhorou (10,6% → 12,3%, com o BNO24 no pico de 14,5%): quem conversa
continua fechando na mesma proporção. O que despencou foi **abrir a conversa** (73,8% → 36,6%) e,
junto com o teste 2 do achado 1, o **volume de abordagem** (metade do BNO24). O líquido é a taxa
abordagem → venda caindo de 7,81% para 4,51%.

Isso reforça o diagnóstico do achado 1: o problema do Comercial é de **alcance e mobilização**, não
de capacidade de venda. Método idêntico ao de `relatorios/comercial-abordagens` (venda comercial da
mesma pessoa em 14d, por telefone ou e-mail) — ⚠️ é atribuição por proximidade temporal, mede
"conversou e comprou", não "comprou por causa da conversa".

---

## Revisão independente (17/09/2026)

A análise passou por revisão crítica de um agente de analytics com acesso ao warehouse, que rodou
~20 queries de verificação. **Tudo que ele apontou foi conferido por mim antes de aceitar.**

**Erros corrigidos** (todos estavam publicados):
1. R$ 66,6 mi do BF2023 misturava renovação — o número na régua certa é **R$ 56,4 mi** (achado 2)
2. Vitalícios do BNO25: **1.939**, não 1.607 (número obsoleto de uma query parcial)
3. "Queda monotônica" do Comercial — a própria tabela tem 3 subidas (achado 3)
4. `vl_cac_canal_midia` da TRA vinha do percentual arredondado → **R$ 3.397,72**, não R$ 3.379,66
   (bug no `refresh.py`, corrigido; o `data.json` publicava dois valores divergentes)
5. Reincidência da ODI: os 54,1% eram união de todas as campanhas, não do CDL (**CDL = 40,8%**),
   e usavam ordinal em vez de data (**50,7%** por data)
6. Seis células truncadas em vez de arredondadas na tabela do achado 3

**O que mudou de conclusão:**
- **A moldura "troca de motor em três anos" não se sustenta.** A série da casa mostra degrau em
  meados de 2024 e o BNO24 como outlier de mobilização do Comercial (achado 1, teste 2).
- **A validação da whitelist estava errada** — quem reproduz o oficial é a contagem sem filtro
  (§Decisões de abordagem).
- **A penetração do estoque não sustenta "camada fácil esgotada"** (achado 4).

**O que sobreviveu à verificação:** a identidade `ROAS = ticket ÷ CAC` (9/9), a identidade
`CAC = CAC_canal × share` (9/9), as três convenções de rateio, receita e compradores por campanha,
CAC/ROAS/CPM/CPC, mix de canal, taxa de resposta do Comercial, CRM por 1k, os regex de universo
(procurou falso positivo e não achou nada material) e a ausência de duplo cômputo de verba entre
BP10/ODI/CDL.

---

## Pendências / próximos passos

- [ ] **Piso de ROAS — a recomendação mais acionável do dataset, e ela já é respondível.** Com
      margem digital 0,75 (`midia-paga/MARGEM.md`) o piso é **1,33×**. O ROAS do canal mídia por
      campanha (achado 6) fica entre 0,13× e 2,31×: **só o CDL passa**. Levar essa tabela para a
      decisão de desligar/manter mídia por campanha.
- [ ] **Por que o Comercial não foi mobilizado como em nov/2024** — é a pergunta que o teste 2 do
      achado 1 abre e a única com dono e alavanca clara. Cruzar com `dtm_seller_conversion_rate`
      (Pipedrive), que não entrou nesta análise.
- [ ] **Intervalo de confiança**: campanhas pequenas (TRA2 n=371, DBI n=1.167, BIT n=1.549) aparecem
      nas mesmas tabelas que o BNO25 (n=54.211) sem sinalização de precisão. O CAC de mídia da TRA2
      (R$ 4.254) sai de **42 compradores**.
- [ ] **Ticket do próprio vitalício caiu 20%** (BNO24 R$ 2.027 → BP10 R$ 1.625) — parte do "ticket
      caiu de 1.374 para 1.003" é preço do mesmo produto, não mix. Alavanca de oferta, com dono.
- [ ] **Gasto prévio médio do comprador** já está calculado (`vl_gasto_previo_medio`, query 03) e não
      foi usado: ODI R$ 4.305 e CDL R$ 2.322 contra BNO25 R$ 373 e BP10 R$ 634. É o teste direto de
      "girar a mesma carteira".
- [ ] **Incrementalidade**: nada aqui separa venda que a mídia causou da que ela só registrou.
      O caminho é holdout geográfico (o MMM já tem o instrumento — ver `relatorios/midia-paga`).
- [ ] **Piso de ROAS acordado com o negócio**: a lição do DOM/ELS (`aquecimento-vendas`) se repete —
      sem piso, cada campanha decide desligar mídia no feeling. Com ROAS 2,35× no BP10 e margem
      digital m=0,75 (`midia-paga/MARGEM.md`), vale checar se o BP10 ainda estava acima do piso.
- [ ] **Custo real do Comercial**: pedir folha + ferramenta ao Financeiro para trocar a comissão de
      9% (piso) por custo total do canal. Sem isso, toda comparação mídia × Comercial é enviesada.
- [ ] 🔑 **Renovar o token da Meta** (`~/meu_projeto/BigQuery/meta_api/.env`) — invalidado em
      18/09/2026 (erro 190/460). Destrava: (a) a contagem de anúncios das 4 campanhas antigas
      (`scripts/extrai_meta_ads.py`, pronto) e (b) o CAC e ticket por criativo. Sem ele a extração
      de nível de campanha que já está no BQ continua válida — nada do relatório depende do token.
- [ ] **CAC e ticket por criativo**: com o token renovado, `level=ad` nas 9 janelas cruzado com
      `nm_pptc_utm_content` das transações. É a decomposição do enquadramento no nível em que a
      mídia decide — e a versão respondível de "qual anúncio traz gente que compra caro".
- [ ] **Reincidência como alerta operacional**: ODI vendeu 54% para quem já havia comprado no CDL.
      Vale medir canibalização entre lançamentos de livro antes do próximo.

## Queries

| Arquivo | O quê |
|---|---|
| [queries/01_universo_compradores.sql](queries/01_universo_compradores.sql) | `tb_ht_compradores`: comprador × campanha × universo, com status, canal e histórico high-ticket |
| [queries/02_esforco_crm_comercial.sql](queries/02_esforco_crm_comercial.sql) | Disparos de CRM e abordagens/conversas do Comercial por janela |
| [queries/03_saturacao_base.sql](queries/03_saturacao_base.sql) | Base elegível, penetração de high-ticket e maturidade do comprador |
| [queries/04_midia_google_pmax.sql](queries/04_midia_google_pmax.sql) | Spend Google e PMax por campanha (warehouse, jan/2025+) |
| [queries/05_cac_por_campanha.sql](queries/05_cac_por_campanha.sql) | CAC (tag e blended), ROAS, CPM, CPC e conversão de clique |
| [queries/06_consolidado.sql](queries/06_consolidado.sql) | Uma linha por campanha — alimenta o `data.json` |
| [queries/07_economia_por_canal.sql](queries/07_economia_por_canal.sql) | Custo, CAC e ROAS por campanha × canal + detalhe de disparos de CRM |
| [queries/08_cac_por_produto.sql](queries/08_cac_por_produto.sql) | O que foi vendido em cada campanha + CAC por família nos dois rateios |
| [queries/09_testes_atribuicao.sql](queries/09_testes_atribuicao.sql) | Os 2 testes de robustez: universo rastro×janela e série mensal de canal da casa |
| [queries/10_conversao_comercial.sql](queries/10_conversao_comercial.sql) | Funil do Comercial: abordagem → conversa → venda em 14d |
| [queries/11_qtd_anuncios.sql](queries/11_qtd_anuncios.sql) | Qtd. de anúncios, conjuntos e campanhas de anúncio por campanha |
| [scripts/extrai_meta_ads.py](scripts/extrai_meta_ads.py) | Extração em `level=ad` nas 9 janelas (⚠️ requer token Meta válido) |
| [scripts/extrai_meta_api.py](scripts/extrai_meta_api.py) | Spend Meta por campanha × dia via Marketing API (ago/2023+) |
| [scripts/carrega_meta_bq.py](scripts/carrega_meta_bq.py) | Carrega o CSV em `bp-staging.dbt_abe.tb_ht_meta_spend` |
| [refresh.py](refresh.py) | Roda tudo e gera `data.json` |

## Wiki atualizada

- `wiki-bp/pages/meta-insider-ads.md` — como recuperar spend Meta anterior a ago/2025 pela Marketing API
- `wiki-bp/pages/metricas-referencia.md` — CAC/ROAS das 9 campanhas high-ticket + decomposição do CAC
- `wiki-brasil-paralelo/pages/campanhas-contexto.md` — oferta e resultado de BNO24 vs BNO25

## Checklist de revisão

- [x] `nm_status='approved'`, `bl_is_renovation=FALSE` em todas as queries
- [x] Universo validado contra 5 referências independentes (planilha, aquecimento-vendas, wiki, cbo_daily_members)
- [x] Whitelist de membership aplicada (sem ela, comprador de livro vira "membro")
- [x] Fonte de mídia validada: API × warehouse com 0,0% de diferença em 13 meses
- [x] Canal separado (Comercial vs Digital vs CRM) em todas as tabelas
- [x] Métrica principal correta para o contexto (ROAS, não CAC, entre tickets diferentes)
- [x] Paleta dos gráficos validada com `validate_palette.js`
