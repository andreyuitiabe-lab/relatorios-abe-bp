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

Comparando as duas campanhas que vendem a mesma coisa (vitalício para a base):

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

### 5. A eficiência do CRM NÃO caiu — isso refuta parte da premissa

A percepção de "alta eficiência de CRM no começo" não se sustenta nos dados disponíveis.
Receita por 1.000 mensagens entregues, por mês (Insider começa em jan/2024, então 2023 é cego):
2024 varia entre R$ 5 e 16 (com o pico do BNO24 em R$ 47); **2025 cai para R$ 6–21; 2026 é o melhor
período da série, R$ 25–68**. O que caiu foi a **taxa de clique** (0,54% em 2024 → 0,14–0,36% em
2025–26) e o volume de disparo triplicou. O CRM entrega mais receita por mensagem hoje do que entregava.

O canal que de fato perdeu eficiência é o **Comercial** (achado 3).

---

## Pendências / próximos passos

- [ ] **Incrementalidade**: nada aqui separa venda que a mídia causou da que ela só registrou.
      O caminho é holdout geográfico (o MMM já tem o instrumento — ver `relatorios/midia-paga`).
- [ ] **Piso de ROAS acordado com o negócio**: a lição do DOM/ELS (`aquecimento-vendas`) se repete —
      sem piso, cada campanha decide desligar mídia no feeling. Com ROAS 2,35× no BP10 e margem
      digital m=0,75 (`midia-paga/MARGEM.md`), vale checar se o BP10 ainda estava acima do piso.
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
