# High-ticket: por que o CAC subiu — Travessia (2023) → BP10 (2026)

**Data:** 2026-09-17 | **Status:** concluída (relatório vivo) · **revisado por agente independente
em 17/09** — 6 erros corrigidos e 2 testes de robustez incorporados (ver §Revisão independente)
**Relatório:** [index.html](index.html) — reescrito em 18/09 para leitura de negócio: resultado na
frente, método no fim, sem jargão. **Este memo é o documento técnico**: todo o detalhe de método,
as ressalvas, a revisão independente e o histórico de correções ficam aqui, não na página.
**Pedido (André):** nos últimos anos lançamos produtos de alto ticket. No começo vendíamos bem
com CAC baixo e alta eficiência de CRM; ultimamente dependemos mais de anúncios e o CAC subiu.
Entender se **(1)** fizemos algo diferente, **(2)** o perfil do público está saturando, ou
**(3)** tínhamos demanda reprimida que está se esgotando.

Campanhas: Travessia, Travessia relançamento, BNO24, Bitcoin 1, Bitcoin 2, BNO25, CDL, ODI, BP10.

---

## Decisões de abordagem

**Escopo: 8 campanhas, não 9 — o BNO25 saiu em 21/09/2026.** Decisão do André a pedido da Bárbara:
*"só tiraria o bp25, realmente foi foco em entrada mesmo"*. O relatório passou de R$ 130,1 mi para
**R$ 111,4 mi de receita** e de R$ 28,3 mi para **R$ 22,7 mi de mídia**.

Antes de executar, levantei a objeção com número: o BNO25 é o **5º maior em receita de alto ticket
da série** (R$ 9,6 mi, 3.277 compradores acima de R$ 1.000 — mais que a Travessia, R$ 8,0 mi). O
"foco em entrada" descreve a *composição* dele (51,2% da receita), não o tamanho do alto ticket.
O André manteve a remoção; registro aqui para quem retomar saber que não foi descuido.

Três consequências que precisaram de tratamento:
1. **O BNO25 continua em `tb_ht_compradores`** (query 01), de propósito. Ele é a origem principal
   de reincidência do DBI — tirá-lo do universo faria a reincidência do DBI cair por artefato de
   escopo, não por fato. As demais queries já não o listam, e a query de reincidência do
   `refresh.py` o exclui **só da linha de saída**, mantendo-o como origem possível.
2. **A evidência de "mudamos a oferta" trocou de dono.** Era o BF 2025 ter parado de vender
   vitalício; passou a ser a reprecificação do vitalício entre BNO24 e BP10 (achado 2b) — que é
   comparação de vitalício contra vitalício e, por isso, mais limpa do que a anterior.
3. **O caso pedagógico do CAC blendado enfraqueceu.** O BNO25 era o exemplo extremo (8,5× entre o
   CAC de todos e o de alto ticket). O que sobra com amostra grande é o BP10 (1,6×) e o BNO24
   (1,5×); o DBI tem 13,8×, mas com **31 compradores** de alto ticket — publicado como alerta, não
   como conclusão (decisão do André na mesma conversa: manter o DBI marcado como amostra
   insuficiente).

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

### 2. O BNO25 não foi saturação — foi outra oferta  ⚠️ FORA DO ESCOPO DESDE 21/09/2026

> Mantido como registro: foi este achado que refutou a hipótese de saturação no Black November, e
> o raciocínio segue válido. Ele **não aparece mais no relatório publicado** — a campanha saiu do
> escopo (ver "Decisões de abordagem"). Quem for reusar estes números precisa dizer de onde vêm.

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

### 2b. A oferta de vitalício foi reprecificada — e é isso que o relatório publica agora

⚠️ **CORRIGIDO em 21/09/2026 — erro meu, pego pelo André** (*"bp10 só teve isso de vendas de black
mesmo?"*). A primeira versão desta seção comparava o universo **principal** de cada campanha:
BNO24 em `janela` e BP10 em `rastro`. São réguas diferentes, e a diferença é grande — o Black
Vitalício do BP10 é **368 em rastro e 1.644 em janela**. A tabela publicada dava −87% de volume no
Black; com régua consistente é **−43% (janela) ou −77% (rastro)**. O total também estava errado:
eu publiquei "18.553 → 8.798" (−53%), que é janela contra rastro.

**Por que não dá para escolher só uma régua.** Cada uma enviesa para um lado:
- `rastro × rastro` — o BNO24 fica subcontado (era promoção de catálogo, nem toda venda levava
  tag: 11.788 de 18.553 vitalícios). **Exagera a queda.**
- `janela × janela` — o BP10 ganha 97 dias de janela contra 30 do BNO24. **Suaviza a queda.**

A leitura honesta é o intervalo. O relatório publica os dois com um toggle e escreve os números em
faixa.

| Degrau | Preço BF24 → BP10 | Volume `rastro` | Volume `janela` |
|---|---|---|---|
| Básico  | R$ 1.292 → 1.289 (igual) | 7.739 → 2.443 (**−68%**) | 11.313 → 3.307 (**−71%**) |
| Premium | R$ 2.468 → 1.622 (**−34%**) / R$ 2.470 → 1.672 (**−32%**) | 2.334 → 5.987 (**+157%**) | 4.065 → 7.191 (**+77%**) |
| Black   | R$ 4.338 → 3.918 (−10%) / R$ 4.296 → 4.255 (−1%) | 1.569 → 368 (**−77%**) | 2.887 → 1.644 (**−43%**) |
| Intermediário | R$ 1.987 → não existe | 146 → 0 | 288 → 0 |
| **Total** | | **11.788 → 8.798 (−25%)** | **18.553 → 12.142 (−35%)** |

**O que sobrevive à troca de régua** (é o que a seção afirma):
- **Preço do Premium caiu ~1/3** (−32% a −34%). Preço é robusto ao universo — preço é preço.
- **Volume do Premium subiu muito** (+77% a +157%), com receita quase estável. Reprecificação que
  funcionou: troca deliberada de margem por volume. O CAC piorar por isso é **mecânico, não erro
  de mídia** — ticket menor com a mesma verba.
- **Volume caiu onde o preço NÃO mudou**: Básico −68/−71% e Black −43/−77%. Não é elasticidade; é
  volume que não apareceu, no mesmo período da queda de abordagens do Comercial (achado 3).
- **Total de vitalício caiu 25–35%.**

**Lição de método para as próximas comparações:** o universo principal é escolhido por campanha,
por boas razões (o BNO24 é promoção de catálogo, o BP10 é lançamento). Isso é correto para medir
*cada campanha*, e errado para *comparar duas*. Toda comparação campanha × campanha neste relatório
precisa fixar a régua antes — conferir se a afirmação sobrevive nas duas.

⚠️ `nm_plano_principal` é o plano principal do comprador e `vl_receita` inclui order bump, então a
soma por degrau excede a receita estrita de vitalício. Vale para preço e volume, que é o uso aqui;
para receita de vitalício usar `vl_receita_vitalicio` do consolidado. Query: `Q_VITALICIO` em
[refresh.py](refresh.py).

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

### 4b. Quem é "membro" mudou de natureza: o vitalício virou o comprador principal (21/09)

Pedido do André ao ver o gráfico de perfil: quebrar "membro ativo" entre **vitalício** e
**assinante corrente**. A coluna já existia (`bl_vitalicio_previo` na query 01, assinatura vitalícia
iniciada antes da primeira compra da campanha); só faltava expor. Adicionada na
[queries/06_consolidado.sql](queries/06_consolidado.sql) como `qt_membro_vitalicio` /
`qt_membro_assinante`.

| Campanha | Membros | Já eram vitalícios | % dos membros |
|---|---:|---:|---:|
| TRA   |  4.118 |     0 | **0,0%** |
| TRA2  |    235 |    47 | 20,0% |
| BNO24 | 12.855 | 1.777 | 13,8% |
| BIT   |    981 |   236 | 24,1% |
| DBI   |    328 |    54 | 16,5% |
| CDL   | 14.000 | 6.180 | **44,1%** |
| BP10  |  3.146 |   619 | 19,7% |
| ODI   |  2.893 | 1.654 | **57,2%** |

**Por que importa:** vender para vitalício é outra venda. Não há mensalidade a converter, ele já
pagou alto ticket antes, e o que se oferece é produto novo — não upgrade de plano. Nos dois
lançamentos de livro de 2026 (CDL e ODI) essa é a maioria ou quase, contra 14% no BNO24.

✅ **O zero da Travessia foi validado, não é falha de dado:** a primeira assinatura vitalícia da
base é de **01/11/2023** (`MIN(dt_started_at)` em `dim_subscriptions` com
`nm_subscription_recurrence = 'vitalício'`, 85.612 no total). A Travessia é de abr–mai/2023,
anterior ao produto existir.

🔗 **Fecha com o achado 4 (reincidência).** A Odisseia tem 50,7% de compradores vindos de campanha
anterior *e* 57,2% dos seus membros são vitalícios. Os lançamentos de livro de 2026 estão girando a
carteira de vitalícios — receita boa e barata, mas a mesma carteira. É aqui que se olha se a
pergunta for esgotamento, e não na penetração da base (que segue em 88% sem high-ticket).

⚠️ Paleta do gráfico revalidada com `validate_palette.js` ao virar 4 séries
(`#4a3aa7,#2a78d6,#eb6834,#1baf7a`): todos PASS, pior par adjacente ΔE 9,2 em deutan e 16,3 em
visão normal. O WARN de contraste do verde é o mesmo de antes e está coberto por legenda + rótulos.

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

### 7a. CAC por faixa de valor da venda — o corte que o André pediu duas vezes

⚠️ **Falha minha, registrada:** o André pediu isso em 17/09 ("no BNO24 tinham outros produtos
sendo vendidos, atribuir todo o custo ao CAC do vitalício é injusto") e de novo em 18/09. Eu
calculei por família de produto (achado 7) mas, ao reescrever a página para legibilidade, **removi
a seção** — ela ficou só neste memo. Refeito em 18/09 por faixa de valor, que é o corte mais direto.

Faixas pelo maior ticket do comprador: alto > R$ 1.000 (46% dos compradores, 88% da receita) ·
médio R$ 200–1.000 (25% / 8%) · entrada < R$ 200 (29% / 4%). Rateio por receita (convenção oficial).

| | CAC blendado | **CAC alto ticket** | diferença | ticket alto |
|---|---|---|---|---|
| TRA | R$ 179 | **R$ 182** | 1,0× | R$ 1.679 |
| TRA2 | R$ 482 | **R$ 631** | 1,3× | R$ 1.666 |
| BNO24 | R$ 186 | **R$ 277** | 1,5× | R$ 2.045 |
| BIT | R$ 828 | **R$ 1.413** | 1,7× | R$ 2.872 |
| **BNO25** | **R$ 104** | **R$ 878** | **8,5×** | R$ 2.923 |
| **DBI** | **R$ 146** | **R$ 2.008** | **13,8×** | R$ 2.638 |
| CDL | R$ 198 | **R$ 214** | 1,1× | R$ 1.475 |
| BP10 | R$ 426 | **R$ 674** | 1,6× | R$ 1.587 |
| ODI | R$ 339 | **R$ 404** | 1,2× | R$ 1.484 |

**O que muda na conclusão:**
1. **A alta do CAC do produto caro é maior que a do blendado:** BNO24 → BP10 vai de R$ 277 para
   R$ 674 (**+143%**), contra +129% no blendado.
2. **O BNO25 e o DBI eram ilusão de mistura.** Tinham os melhores CACs da série (R$ 104 e R$ 146)
   porque 94% e 97% dos compradores levaram produto de entrada. No alto ticket são o 2º e o 1º
   **piores** do estudo. A diferença de 8,5× e 13,8× é o tamanho do engano.
3. **O CDL segue sendo a melhor campanha da série por qualquer corte** — R$ 214 de CAC de alto
   ticket, praticamente igual ao blendado, porque 96% da receita dele já era alto ticket.

⚠️ O rateio por receita torna o **retorno idêntico em todas as faixas por construção** — entre
faixas de preço, só o CAC diferencia. Não citar "retorno da faixa X".

---

### 7b. Universo: o relatório conta TODOS os compradores, não só os de alto ticket

**Pergunta do André (18/09):** os gráficos contam só as vendas high-ticket ou o geral da campanha?

**Resposta: o geral.** O "high-ticket" do título se refere ao tipo de *lançamento*, não a um filtro
de transação. O universo é consistente em todo o relatório — todo comprador da campanha — e é a
mesma convenção da planilha do time de tráfego (BNO24 = toda venda nova de novembro).

Quanto da campanha é de fato alto ticket (transação acima de R$ 1.000):

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| % da receita | 99,5 | 92,2 | 94,7 | 95,9 | **51,2** | **36,6** | 96,4 | 88,0 | 93,7 |
| % dos compradores | 97,7 | 70,4 | 63,7 | 56,2 | **6,0** | **2,7** | 89,2 | 55,6 | 78,7 |

Em sete das nove, alto ticket é 88%+ da receita e a distinção não muda nada. **Nas duas em que
muda, ela inverte o perfil do comprador:**

| | Todos os compradores | Só alto ticket |
|---|---|---|
| **BNO25** | 12,8% membro · 61,9% nunca-membro | **69,2% membro · 17,0% nunca-membro** |
| **DBI** | 28,1% · 49,6% | **67,7% · 22,6%** |
| BP10 (controle) | 16,9% · 54,8% | 20,9% · 52,0% |

Faz sentido: BNO25 e DBI venderam sobretudo produto de entrada barato (R$ 7,90 e R$ 48), e quem
compra entrada barata é gente de fora. **Quem levou o produto caro nessas duas era membro da base.**

⚠️ **Consequência para leitura:** a frase "o BNO25 vendeu para fora" vale para a promoção inteira,
não para o alto ticket. A página agora traz a coluna "% alto ticket" na tabela mestra e essa
comparação na nota do gráfico de perfil. As demais métricas (CAC, receita, mix de canal) seguem no
universo completo de propósito — mudar o universo de um gráfico só criaria inconsistência.

---

### 8. Fechando a lista do pedido: anúncios, status do comprador e conversão do Comercial

Auditando o relatório contra a lista de métricas do pedido original, três itens não estavam
entregues. Foram fechados em 18/09.

**Qtd. de anúncios — 9 de 9** (fechada em 18/09 com a planilha histórica do time de tráfego):

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| **Anúncios** | **128** | **40** | **371** | **91** | 690 | 284 | **897** | **1.182** | 506 |
| só fase de venda (planilha) | 128 | 40 | 371 | 91 | 753 | 78 | — | — | — |
| todas as fases (warehouse) | — | — | — | — | 690 | 284 | 897 | 1.182 | 506 |

O volume de criativos cresceu junto com a dependência de mídia — **128 na Travessia contra 1.182 no
BP10** — e a **verba por anúncio ficou estável**: escalou-se em número de criativos, não em verba
por criativo.

⚠️ **São duas fontes com definições diferentes, e elas não são intercambiáveis:**

| Fonte | Cobertura | Limite |
|---|---|---|
| Planilha do tráfego (`tb_ht_sheet_meta_ads`) | nível de anúncio, 01/06/2022 → 16/04/2026 | **só fase de venda** |
| Warehouse (`dtm_analytics_facebook_ads_funnel`) | todas as fases | nome de anúncio só confiável desde **mar/2025** |

**O DBI mostra por que a distinção importa:** 78 anúncios / R$ 19 k na planilha contra
**284 / R$ 152 k no warehouse** — quase toda a verba dele foi captação, que a aba de venda não vê.
Em campanha majoritariamente de venda as duas convergem (BNO25: 753 vs 690 anúncios, spend batendo
em 0,6%). **Comparar dentro de cada grupo, nunca entre eles.**

⚠️ A planilha é um **XLSX baixado em 16/04/2026**, não a planilha viva — não atualiza sozinha e não
alcança CDL, BP10 nem ODI. Para dado novo: rebaixar e rodar `scripts/carrega_planilha_ads.py`.

**Validação:** o spend mensal da planilha bate com a Marketing API em **0,0% em 22 de 31 meses**
(máximo 3,8%) — é o mesmo dado, recortado diferente. A planilha também alcança abr–mai/2023 e
mostra que a conta gastou **R$ 2,09 mi** em mídia de venda na janela da Travessia; os R$ 869.816
que o time de tráfego atribui à campanha são **41,5% disso** — proporção plausível, o que dá
sustentação ao CAC de R$ 179 e ao ROAS de 9,20× que abrem a série.

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

### 9. Quanto sobra depois do custo de aquisição (pedido do André em 18/09)

⚠️ **Nomenclatura.** Eu chamei isto de "margem" numa versão anterior e estava errado — o André
pegou (*"a gente trabalhou com uma margem tão alta assim?"*). Não é. É **receita menos os três
custos de aquisição** (mídia + comissão de 9% do Comercial + disparo de CRM) e nada mais. Ficam de
fora impostos e gateway (12–18%), reembolso (6,5%), custo de produto físico (15–25%), folha do
Comercial e do time de mídia, produção de conteúdo. A margem de verdade da casa está em
`relatorios/midia-paga/MARGEM.md` (0,75 digital / 0,55 físico). Aplicando aqueles descontos, a
Travessia sai de 83% para ~61%, o CDL de 80% para ~38% e o DBI fica **negativo (−12%)**.
Depois da correção, o André fechou o escopo: *"eu preciso só dos custos de aquisição mesmo"* — é o
que está publicado, com o rótulo certo.

| Campanha | Receita | Custo de aquisição | Sobra | % que sobra | Por comprador | Mídia no custo |
|---|---:|---:|---:|---:|---:|---:|
| TRA*  | R$ 8,0 mi  | R$ 1,4 mi | R$ 6,6 mi  | 83,0% | R$ 1.368 | 63,9% |
| TRA2  | R$ 471 mil | R$ 231 mil| R$ 240 mil | 51,0% | R$ 647   | 77,3% |
| BNO24 | R$ 40,3 mi | R$ 8,4 mi | R$ 31,9 mi | 79,2% | R$ 1.088 | 65,1% |
| BIT   | R$ 2,6 mi  | R$ 1,5 mi | R$ 1,1 mi  | 41,9% | R$ 704   | 84,7% |
| BNO25 | R$ 18,7 mi | R$ 6,8 mi | R$ 11,9 mi | 63,6% | R$ 220   | 82,5% |
| DBI   | R$ 223 mil | R$ 203 mil| R$ 21 mil  |  9,2% | R$ 18    | 83,9% |
| CDL   | R$ 34,9 mi | R$ 7,0 mi | R$ 27,9 mi | 79,9% | R$ 1.091 | 72,2% |
| BP10  | R$ 18,7 mi | R$ 8,7 mi | R$ 9,9 mi  | 53,2% | R$ 534   | 90,9% |
| ODI   | R$ 6,2 mi  | R$ 2,1 mi | R$ 4,2 mi  | 66,9% | R$ 833   | 82,1% |

\* **Travessia é teto.** O Insider só tem dado a partir de 30/01/2024, então o custo de CRM da
Travessia entra como zero — não porque foi zero, mas porque não é medível. Nas campanhas em que dá
para medir, o CRM custa de 2,7% (BNO24) a 4,5% (TRA2) da receita; nessa faixa a Travessia iria de
83% para 79–80%. Não muda a leitura; muda o número.

**O mecanismo é o mix, não a eficiência.** A coluna "mídia no custo" sobe de 63,9% (TRA) para 90,9%
(BP10) em paralelo com a queda do % que sobra — são a mesma coisa vista de dois ângulos, porque o
custo por real de receita é 9% no Comercial, 9–13% no CRM e 43% a 100% na mídia (achado 6). Trocar
o motor de canal piora a conta mesmo com a eficiência unitária de cada canal intacta.

**O contrafactual, que é o número acionável.** Se o BP10 tivesse o mix de canal do BNO24 — mantendo
as próprias eficiências de custo que o BP10 teve em cada canal, sem supor nenhuma melhora — a sobra
iria de 53,2% para **81,1%**: R$ 15,2 mi no lugar de R$ 9,9 mi. Diferença de **R$ 5,2 milhões**.
O número é estável nos cenários de imposto de 12/15/18% porque depende só do mix, não do nível de
custo — é aritmética de composição, não projeção.

⚠️ **O contrafactual não é promessa.** Ele supõe que o Comercial e o CRM conseguiriam entregar o
volume do BNO24 na mesma eficiência unitária. O achado 3 mostra que a resposta à abordagem caiu de
73,8% para 31% — então parte do volume do BNO24 pode simplesmente não estar mais disponível. Leia
como *teto do que se perdeu*, não como receita a recuperar.

**A comissão de 9% é piso** — não inclui folha do time. Isso deixa a comparação entre canais
conservadora a favor do Comercial. Dobrando o custo dele, nenhuma conclusão muda de sinal.

### Toggle campanha × alto ticket (21/09/2026)

Pedido do André: *"nos gráficos, você consegue adicionar um toggle para ver dados da campanha e dos
produtos de alto ticket"*. Formaliza uma dúvida que ele já tinha levantado em 18/09 ao ver o
gráfico de perfil. Implementado em
[queries/17_recortes_campanha_alto_ticket.sql](queries/17_recortes_campanha_alto_ticket.sql).

**Onde tem toggle:** tabela mestra, origem dos compradores, perfil dos compradores. São as três
peças em que o recorte existe no dado — basta filtrar `vl_maior_tx > 1000` e recontar.

**Onde NÃO tem, de propósito:**
- *Esforço de CRM e funil do Comercial.* Uma mensagem enviada não tem ticket — quem recebeu ainda
  não comprou. O recorte não existe no dado, e fabricá-lo por rateio seria inventar.
- *CAC por faixa de valor.* Já É a quebra; um toggle ali seria redundante.
- *Série mensal da casa, vitalício por degrau.* Não são recortes de campanha.
- *Verba de mídia e número de anúncios,* mesmo dentro da tabela com toggle: não existe "verba do
  alto ticket", a campanha comprou mídia uma vez só. Ficam iguais nos dois estados e o subtítulo
  da tabela diz isso.

**Defaults diferentes, de propósito.** A tabela mestra abre em **alto ticket**; os dois gráficos
descritivos abrem em **campanha inteira**. Razão: da tabela se tira número para decidir mídia, e o
CAC blendado é exatamente o que o relatório mostra ser enganoso — abrir nele contradiria o próprio
argumento. Já os gráficos descrevem quem comprou, e o universo completo é a descrição honesta;
além disso o texto ao lado deles se refere a esse universo.

**O que o recorte revelou** (não era o objetivo, mas é o achado mais forte desta rodada):

| | Mídia % dos compradores — campanha | — só alto ticket |
|---|---|---|
| Bitcoin 1 | 22,7% | **7,0%** |
| Bitcoin 2 | 56,7% | **3,2%** |
| BF 2024   | 19,1% | 14,3% |
| Clube do Livro | 34,3% | 33,6% |
| **BP10** | 50,2% | **59,7%** |

Em quase toda campanha a mídia encolhe no recorte de alto ticket — ela trouxe o produto de entrada
e o **Comercial** fechou o caro (no Bitcoin 1 o Comercial vai de 53,1% para 72,8%). **O BP10 é a
única em que a mídia sobe**, e é também a campanha com pior eficiência de aquisição da série
(53,2% de sobra). Vale como hipótese a testar, não como conclusão: é leitura de último clique.

⚠️ O CAC do recorte de alto ticket usa rateio da verba **por receita** — é o mesmo número da faixa
'alto' em `15_cac_por_faixa_valor.sql`. Por construção o ROAS fica igual nos dois recortes; quem
compara recorte tem que olhar o CAC, não o retorno.

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
      18/09/2026 (erro 190/460). Já **não bloqueia a contagem de anúncios** (resolvida pela planilha),
      mas ainda destrava o CAC e ticket por criativo. Migrar para System User, que não morre com
      troca de senha.
- [ ] **Escopo de Drive na ADC** para ler as planilhas de mídia direto do BigQuery (external table,
      mesmo padrão dos marts Adveronix) em vez de depender de XLSX baixado. DDL pronto em
      `queries/13_external_tables_planilhas.sql`; a autenticação de 18/09 não pegou os escopos.
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
| [queries/11_qtd_anuncios.sql](queries/11_qtd_anuncios.sql) | (superada pela 14) Qtd. de anúncios só pelo warehouse |
| [queries/13_external_tables_planilhas.sql](queries/13_external_tables_planilhas.sql) | DDL das external tables sobre as planilhas — ⚠️ requer escopo de Drive na ADC |
| [queries/14_qtd_anuncios_v2.sql](queries/14_qtd_anuncios_v2.sql) | Qtd. de anúncios pelas duas fontes, com a definição de cada uma |
| [queries/15_cac_por_faixa_valor.sql](queries/15_cac_por_faixa_valor.sql) | CAC separado por faixa de valor da venda (alto / médio / entrada) |
| [queries/16_receita_liquida_aquisicao.sql](queries/16_receita_liquida_aquisicao.sql) | Receita menos os três custos de aquisição — ⚠️ **não é margem**, ver cabeçalho do arquivo |
| [queries/17_recortes_campanha_alto_ticket.sql](queries/17_recortes_campanha_alto_ticket.sql) | As mesmas métricas nos dois recortes (campanha inteira × alto ticket) — alimenta o toggle |
| [scripts/carrega_planilha_ads.py](scripts/carrega_planilha_ads.py) | Carrega a aba de anúncios do XLSX do time de tráfego no BQ (595 mil linhas, 2022→2026) |
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
