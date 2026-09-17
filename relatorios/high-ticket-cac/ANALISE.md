# High-ticket: por que o CAC subiu — Travessia (2023) → BP10 (2026)

**Data:** 2026-09-17 | **Status:** concluída (relatório vivo)
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
| Base ativa em 01/04/2023 | 558.624 | 558.769 | `cbo_daily_members` (pagantes ativos) |

**Status do comprador** (membro / ex-membro / não-membro) avaliado na data da primeira compra da
campanha, com **whitelist de membership** — sem ela todo comprador de livro viraria "membro",
porque `dim_subscriptions` grava produto avulso (CDL, Odisseia, Travessia, certificações) como
assinatura ativa. Legados `patriota` (304k) e `bp-select` entram como membership; os clubes de
conteúdo de 2021 não.

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

⚠️ A Travessia original é a única campanha sem spend granular. Para ela o custo vem da planilha
(`TRA-2023`: captação R$ 178.970, 46.000 cadastrados, CPL R$ 3,89), que não separa canal.

---

## Achados principais

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

Adquirir um comprador *pela mídia* ficou **mais barato**. O CAC médio subiu porque a mídia deixou
de ser o complemento e virou o motor — o denominador "de graça" (Comercial + CRM) encolheu.

⚠️ **ROAS é a métrica comparável, não CAC.** Campanhas com ticket diferente não têm CAC comparável:
o BNO25 tem o melhor CAC da série (R$ 104) e é a pior campanha de vitalício, porque vendeu assinatura
de R$ 345 em vez de vitalício de R$ 1.374. ROAS por campanha: TRA 9,20× · BNO24 7,37× · CDL 6,89× ·
ODI 3,68× · BNO25 3,33× · TRA2 2,64× · BP10 2,35× · BIT 2,03× · DBI 1,31×.

### 1. A dependência de anúncios é real e é grande

Participação da **mídia paga** na receita da campanha:

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| Mídia paga | 5,2% | 10,7% | 13,5% | 6,3% | 24,9% | 23,5% | 33,5% | **53,3%** | 26,9% |
| Comercial | 68,2% | 73,4% | 51,6% | 76,1% | 59,7% | 41,6% | 48,0% | **26,5%** | 46,6% |
| CRM | 21,6% | 10,1% | 26,5% | 9,6% | 5,6% | 20,9% | 14,2% | 14,1% | 22,1% |

O high-ticket começou como produto de **Comercial** (68–76% da receita) e o BP10 já é um produto
de **mídia** (53,3%). Não é impressão: é uma troca de motor.

### 2. O BNO25 não foi saturação — foi outra oferta

A queda do Black November (R$ 66,6 mi em 2023 → R$ 40,3 mi em 2024 → R$ 18,7 mi em 2025) não é
o mesmo produto vendendo menos:

| | BNO24 | BNO25 |
|---|---|---|
| Receita | R$ 40,28 mi | R$ 18,72 mi |
| Ticket médio | R$ 1.374 | R$ 345 |
| Vitalícios vendidos | **18.553** (R$ 37,6 mi, 93% da receita) | **1.607** (R$ 6,25 mi, 33%) |
| Oferta (planilha do tráfego) | "Vitalício. Começo do Black" | "Originais por R$ 7,90 e 70% off no premium" |

O BF de 2025 **não vendeu vitalício** — vendeu entrada barata. Comparar o CAC das duas como se
fossem a mesma campanha é comparar produtos diferentes. Em 2026 o motor de vitalício voltou, mas
no aniversário (BP10: R$ 14,3 mi dos R$ 18,7 mi são vitalícios).

⚠️ **O "melhor CAC da série" do BNO25 (R$ 104) é artefato de mix.** Ele vendeu 50.997 assinaturas
de R$ 206 e só 1.939 vitalícios. Separando o produto (achado 7), o CAC de vitalício dele é
**R$ 1.046 — o pior da série** sob rateio por receita. Não usar o R$ 104 como benchmark.

### 3. A eficiência do Comercial caiu de forma monotônica

Taxa de resposta às abordagens do Zenvia (grupo Comercial, janela da campanha):

| | TRA | TRA2 | BNO24 | BIT | BNO25 | DBI | CDL | BP10 | ODI |
|---|---|---|---|---|---|---|---|---|---|
| Abordagens/dia | 2.560 | 1.172 | 5.227 | 3.862 | **9.726** | 5.688 | 3.344 | 2.804 | 3.065 |
| % com resposta | **73,8%** | 44,6% | 43,8% | 51,1% | 31,9% | **25,5%** | 42,1% | 36,5% | 31,3% |

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
BP10 6,5% · BIT 11,0% · **CDL 16,7% · ODI 54,1%**. A Odisseia vendeu mais da metade para a carteira
do Clube do Livro — os lançamentos de livro de 2026 estão girando o mesmo público.

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

**Composição do disparo mudou:** o push saiu de zero (BNO24) para 55 milhões de entregas no BP10
(35% do volume da campanha) — e push **não tem telemetria** de abertura nem clique (140M+ entregues
na casa com ~19 opens). A receita atribuída a ele vem do fallback do modelo. Tratar como alcance,
não como engajamento. Taxa de clique da casa: 0,54% (2024) → 0,14–0,36% (2025–26).

O canal que de fato perdeu eficiência é o **Comercial** (achado 3).

### 6. Economia por canal — o que cada um custa (premissa de comissão de 9%)

Custos por natureza: mídia = verba de anúncio com a sigla; Comercial = **comissão de 9% sobre a
venda** (premissa do André); CRM = disparos com a tag × preço por canal (WhatsApp R$ 0,323 —
fonte canônica `zenvia-custos.md`; e-mail R$ 0,0008; push/in-app zero).

| Campanha | CAC mídia | CAC Comercial | CAC CRM | ROAS CRM |
|---|---|---|---|---|
| BNO24 | R$ 979 | R$ 153 | R$ 145 | 10,14× |
| BNO25 | R$ 217 | R$ 69 | R$ 42 | 5,76× |
| CDL | R$ 578 | R$ 127 | R$ 122 | 11,22× |
| BP10 | R$ 849 | R$ 98 | R$ 113 | 7,48× |
| ODI | R$ 1.133 | R$ 121 | R$ 102 | 12,75× |

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

**Dimensionando o item 2 (sensibilidade no BP10):** foram 51 vendedores ativos em 3,19 meses e
R$ 445,9 mil de comissão. Bastam **R$ 2,7 mil por vendedor-mês** de custo adicional para o custo do
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

### 7. O que foi vendido em cada campanha — e o CAC justo por produto

**Levantado a pedido do André (17/09):** o CAC blendado divide a verba por todos os compradores da
janela, e as promoções vendem várias coisas ao mesmo tempo. No BNO24, **10.684 dos 29.313
compradores levaram assinatura de R$ 205**, não vitalício.

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

**O que resolveria de vez:** verba separada por produto na mídia — hoje impossível porque o nome da
campanha de anúncio não carrega produto. É uma mudança de nomenclatura no gerenciador, barata,
e destravaria CAC por produto sem rateio.

---

## Pendências / próximos passos

- [ ] **Incrementalidade**: nada aqui separa venda que a mídia causou da que ela só registrou.
      O caminho é holdout geográfico (o MMM já tem o instrumento — ver `relatorios/midia-paga`).
- [ ] **Piso de ROAS acordado com o negócio**: a lição do DOM/ELS (`aquecimento-vendas`) se repete —
      sem piso, cada campanha decide desligar mídia no feeling. Com ROAS 2,35× no BP10 e margem
      digital m=0,75 (`midia-paga/MARGEM.md`), vale checar se o BP10 ainda estava acima do piso.
- [ ] **Custo real do Comercial**: pedir folha + ferramenta ao Financeiro para trocar a comissão de
      9% (piso) por custo total do canal. Sem isso, toda comparação mídia × Comercial é enviesada.
- [ ] **Qtd. de anúncios (nível de criativo)**: a extração é de campanha, não de anúncio.
      Para contagem de criativos por campanha, repetir a extração com `level=ad` só nas 9 janelas.
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
