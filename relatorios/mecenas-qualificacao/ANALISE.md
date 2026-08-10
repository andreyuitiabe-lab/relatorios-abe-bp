# Qualificação de potenciais Mecenas

**Data:** 2026-08-07 · **Analista:** André Abe
**Relatório:** [index.html](index.html) — publicado no portal (Base & Produtos)

## Pergunta original

Campanha de Mecenas em curso, captando fundos para financiar bolsas da **Licenciatura em História**. O time precisa saber:

1. Como qualificar potenciais mecenas?
2. O que quem é/foi mecenas tem de diferente da base?
3. Quem está comprando agora (ago/2026) tem padrão diferente?
4. Ser sócio de empresa ajuda?
5. Como identificar os públicos a abordar?

Importa porque a abordagem de Mecenas é feita pelo Comercial, um a um, com custo alto por contato — errar o alvo é caro, e a régua atual não é baseada em evidência.

## Decisões de abordagem

| Decisão | Por quê |
|---|---|
| **Doador de bolsa = compra Mecenas ≥ R$ 1.000** | O produto nasceu como patrocínio de bolsa: 1 bolsa custa R$ 1.188 ou R$ 1.668. Abaixo de R$ 1.000 não existe bolsa inteira. Decisão de negócio (ago/2026) |
| **Mecenas Solidário analisado à parte** | Campanha atual (jul/2026+), de ~R$ 30/mês sem teto. É outra população — misturar produz um perfil médio que não existe. Identificado por **produto**, nunca por valor: a oferta de R$ 1.078,80 passa de R$ 1.000 e cairia em "bolsa" |
| Chave = **`id_person`** (identity graph), não e-mail | **20,6% dos doadores têm mais de uma conta.** Agregar por e-mail infla a contagem e subestima a doação por pessoa. Resolução por e-mail, telefone ou CPF via `dim_person_identity`; apoio em `tb_mecenas_person_map` |
| Universo = **1,54M compradores** (≥1 tx aprovada), não só membros ativos | É o universo abordável real. Membro ativo (618,5k) é o grupo de controle |
| Grupo de controle **explícito** em toda comparação | "40% dos doadores são decil 9+" não diz nada sem o 17,7% da base. Tudo é reportado como **lift** |
| Segmentar o doador de bolsa em **3 faixas** por maior doação | Bolsa única, múltiplas bolsas e alto (>R$10 mil) têm perfis diferentes; a média deles não descreve ninguém |
| Validação **out-of-time** (treino ≤ jun/2026, teste jul–ago/2026), excluindo quem já era doador | Sem isso o lift é vazamento: o modelo "acerta" quem já converteu |
| CNPJ: vários thresholds, controle estratificado **e** logística completa | Sócio correlaciona com riqueza *e* com antiguidade — só o controle completo revela o que sobra |

### ⚠️ As três populações (a decisão que mais mexe nos números)

O rótulo "Mecenas" cobre três coisas que não têm relação entre si. Separá-las é a decisão estruturante desta análise:

| População | O que é | Como identificar | Pessoas |
|---|---|---|---|
| **Bolsa** | Patrocínio de bolsa, o produto original (2021→hoje). 1 bolsa = R$ 1.188 ou R$ 1.668; pacotes vão a 500 bolsas | Mecenas, não Solidário, não order bump, **≥ R$ 1.000** | **8.995** |
| **Solidário** | Campanha atual (jul/2026+). Recorrente de ~R$ 30/mês, sem teto | Produto/oferta contendo "solid", ou plano `mecenas_mecenas-solidario-premium` | **203** |
| **Order bump** | R$ 180 (R$ 15/mês) marcado no checkout de outro produto | Oferta **ou produto** contendo "order bump" **e** Mecenas | 6.961 |

⚠️ O corte de R$ 1.000 deixa fora o **pagamento fracionado** de 1 bolsa (ex.: 2× R$ 594). Perda pequena, aceita para não contaminar o perfil.

### ⚠️ E os order bumps

Existem **dois** order bumps de Mecenas, e só um se identifica pelo nome:

| Order bump | Como identificar | Volume |
|---|---|---|
| `BP Essencial - 20%Off Order Bump Mecenas` | tem "order bump" na **oferta** (`nm_gateway_plan = 'good'`) | ~336 tx/mês |
| **`Brasil Paralelo / Comercial - Mecenas Order Bump`** (R$ 180 = R$ 15/mês) | ⚠️ **Não tem "order bump" na oferta** ("Adicione + R$ 15/mês…", "Upsell pós compra…") — só se pega testando o **produto** | 6.961 pessoas |

O segundo é um checkbox no checkout de assinatura barata. Em **mar/2026** ele produziu 2.535 "vendas Mecenas" com ticket de R$ 421 (94% do mês), vindas de tráfego pago de aquisição de plano Básico — 28% eram clientes novos comprando no mesmo dia. **Não é população de doador.**

⚠️ O filtro de order bump é restrito a Mecenas de propósito: order bump de Clube do Livro ou BP Clube é compra legítima e continua contando no histórico (`vl_total_outras`). Sem essa restrição o gasto prévio de todo mundo afunda.

**Definição canônica:** ver o bloco de flags em [00_base_qualificacao.sql](queries/00_base_qualificacao.sql) — as três populações são calculadas lá, com comentário explicando cada corte.

## Números de referência

- **8.995 doadores de bolsa** (pessoas reais) / **R$ 52,44M** histórico
- Universo: 1.541.244 compradores → **taxa base 0,584%**
- Controle: 620.563 membros ativos que nunca doaram
- **Mecenas Solidário: 203 pessoas / R$ 112 mil** (campanha atual, seção 13)
- Multi-conta: 1,24 contas por doador (1,08 na base geral) — quem compra muito espalha mais

## Achados principais

### 1. O topo é minúsculo e concentra tudo

| Tier | Critério (maior doação) | Pessoas | Receita | R$/pessoa | % receita |
|---|---|---|---|---|---|
| Bolsa única | R$ 1–2 mil | 4.111 | R$ 8,36M | 2.033 | 15,9% |
| Múltiplas bolsas | R$ 2–10 mil | 4.578 | R$ 29,14M | 6.366 | 55,6% |
| **Alto** | > R$ 10 mil | **306** | **R$ 14,94M** | 48.833 | **28,5%** |

**306 pessoas (3,4% dos doadores) respondem por 28,5% da receita.** Qualificar para o topo é um problema de algumas centenas de pessoas, não de segmentação de massa.

### 2. Perfil: doador vs. membro padrão

| Atributo | **Membro ativo (620,6k)** | Doador de bolsa (8.688) | **Doador alto (306)** | Lift alto |
|---|---|---|---|---|
| Renda decil 9-10 | 17,6% | 39,0% | 50,7% | 2,9× |
| Cartão black/amex | 28,1% | 60,0% | 81,0% | 2,9× |
| Sócio de empresa | 24,5% | 38,8% | 59,8% | 2,4× |
| **Empresa capital 1M+** | **3,3%** | 11,1% | **47,7%** | **14,5×** |
| Já tem vitalício | 10,3% | 43,7% | 52,9% | 5,1× |
| Já tem certificação | 0,8% | 12,9% | 22,9% | 28,6× |
| Já tem Clube do Livro | 3,7% | 16,9% | 33,0% | 8,9× |
| Gasto prévio (fora doação) | R$ 855 | R$ 3.649 | **R$ 10.819** | 12,7× |
| Mulheres | 37,8% | 40,0% | 29,4% | 0,8× |
| Idade média | 51,3 | 54,0 | 56,2 | — |
| Tempo de casa | 2,3 anos | 5,2 anos | 4,9 anos | 2,1× |

**O doador de alto valor é: sócio de empresa grande, cartão black/amex, já comprou vitalício + certificação, gastou ~R$ 10,8 mil na BP antes de doar, ~4,9 anos de casa, homem de ~56 anos.**

### 3. Lift univariado — o que mais discrimina

| Feature | Conversão | Lift |
|---|---|---|
| Gasto prévio R$ 5k+ | 14,51% | **24,9×** |
| Já comprou certificação | 9,05% | **15,5×** |
| Já tem vitalício | 5,65% | **9,7×** |
| 7+ anos de casa | 4,48% | **7,7×** |
| Gasto prévio R$ 2–5k | 4,06% | 7,0× |
| Black (produto) | 3,12% | 5,4× |
| Sócio com capital 1M+ | 3,02% | 5,2× |
| Sócio com 4+ empresas | 2,73% | 4,7× |
| Já tem Clube do Livro | 2,30% | 4,0× |
| Cartão black/amex | 1,87% | 3,2× |
| Decil de renda 9-10 | 1,46% | 2,5× |
| Sócio de empresa (@0,95) | 0,97% | 1,7× |
| Gênero feminino | 0,64% | 1,1× |
| **Sem cartão mapeado** | 0,09% | **0,15×** |
| **1–2 anos de casa** | 0,05% | **0,08×** |
| **< 1 ano de casa** | 0,01% | **0,02×** |

**Comportamento de compra domina demografia.** Quanto a pessoa já gastou vale ~10× mais como sinal do que o decil de renda dela. Gênero é ruído (1,1×). E **não ter nível de cartão mapeado é sinal negativo forte** (0,2×) — é informação, não ausência dela.

### 4. Sócio de empresa: o que importa é o CAPITAL, não ser sócio

Resposta à pergunta do time, em quatro camadas — porque ela muda conforme o controle:

- **Lift bruto 1,66×** (@ similaridade ≥ 0,95). Modesto sozinho.
- **Sobrevive ao controle por renda e cartão:** dentro de cada um dos 16 estratos renda × cartão o lift fica entre **~1,3× e 2,1×**, sem cair em nenhum. Não é proxy de riqueza.
- ⚠️ **Mas MORRE no controle completo.** Na logística multivariada `socio_95` perde significância (coef 0,009, **p = 0,49**). O que o mata não é renda/cartão — é **tempo de casa + já ter comprado pelo Comercial + maior ticket já pago**. O sócio doa mais porque é antigo de casa e já pagou caro; não porque é sócio. **A flag de CNPJ não é critério de qualificação — é redundante com histórico transacional.**
- ✅ **O capital social sobrevive a tudo:** `log_capital` (0,148) e `capital_1M` (0,071) seguem significativos (p < 0,0001) no modelo completo.

| Recorte | Lift | Doação média |
|---|---|---|
| Capital acima de R$ 1 mi | **5,18×** | R$ 13.123 |
| Capital R$ 100 mil–1 mi | 1,84× | R$ 6.088 |
| Capital R$ 10–100 mil | 1,41× | R$ 5.242 |
| Capital abaixo de R$ 10 mil | 1,03× | R$ 4.536 |
| 4+ empresas | **4,67×** | R$ 15.284 |
| 1 empresa | 1,17× | R$ 5.199 |

**Setores (CNAE):** financeiro/seguros **3,62×** (doação média R$ 10.978), imobiliário 3,52× (R$ 9.654), saúde 3,43× (R$ 5.497). **Comércio fica abaixo da base** — não vale abordar. Educação, apesar de ser o tema do produto, é só 1,34×.

**Uso prático:** filtrar por `vl_share_capital_total >= 1.000.000`, nunca pela flag de sócio. **Exceção:** para público **sem histórico transacional**, o CNPJ volta a ajudar (no modelo estrutural `socio_95` reaparece com coef 0,068).

Convergente com a análise de profissão de 05/08: saúde sobre-indexada pelos dois métodos (profissão declarada 1,93× · CNAE 3,32×).

### 5. Quem compra agora (ago/2026)

| | 2025 | 2026 H1 | jul/2026 | **ago/2026** |
|---|---|---|---|---|
| Doadores | 2.410 | 692 | 161 | 170 |
| Ticket médio | R$ 4.721 | R$ 4.671 | R$ 4.817 | **R$ 1.974** |
| % via Comercial | 100% | 97% | 81% | **36%** |
| % renda topo | 40,0% | 41,2% | 47,2% | 41,2% |
| % cartão topo | 66,8% | 67,6% | 73,3% | 62,4% |
| % vitalício | 51,7% | 53,2% | 60,9% | 46,5% |

**Mudou o canal e o ticket, não o perfil socioeconômico.** A renda no topo praticamente não se moveu (47,2% → 41,2%). Causa: o **Mecenas Solidário** (self-checkout, R$ 358,80 / 718,80 / 1.078,80 — "1/2/3 reais por dia"), que entrou em jul/2026 e em agosto passou o Comercial em volume.

### 6. O Solidário traz gente nova — não canibaliza (mas tem risco)

Coortes jul–ago/2026:

| | Solidário (153) | Bolsas Comercial (157) |
|---|---|---|
| Ticket médio | R$ 541 | R$ 4.606 |
| Já era doador antes | **6,5%** | 70,7% |
| **Nunca comprou high-ticket** | **62,7%** | 6,4% |
| Já tem Black ou vitalício | 33,3% | 65,0% |

- **Canibalização real são 10 pessoas** (~R$ 25k de exposição máxima) contra ~R$ 68k de receita nova dos 96 compradores virgens de high-ticket. Saldo positivo mesmo no cenário pessimista.
- **O risco não é o passado, é o teto:** 33,3% dos compradores de Solidário já têm Black/vitalício e 41,8% já compraram pelo Comercial. São ~51 pessoas com capacidade comprovada pagando R$ 359 porque ninguém as subiu de escada. **É lista de upgrade, não de aquisição.**
- 98% são membros ativos com ~3,7 anos de casa: **monetização de base fiel de baixo ticket** — o segmento que o Comercial não trabalha por falta de valor unitário.

### 7. Logística multivariada: o que sobra quando tudo compete

AUC out-of-time: **0,884** no modelo completo, **0,848** no estrutural. ⚠️ O 0,884 é otimista — a tabela tem features *all-time*, então para os positivos de jul–ago o gasto inclui compras posteriores à conversão. **O número honesto é 0,848.**

| Variável | Uni | Multi | Retenção |
|---|---|---|---|
| **Já comprou pelo Comercial** | 1,18 | **1,02** | 87% |
| **Maior ticket já pago** | 0,79 | **0,79** | 99% |
| Anos de casa | 0,62 | 0,67 | 109% |
| Membro ativo | 0,66 | 0,58 | 89% |
| Nível de cartão | 0,80 | 0,41 | 51% |
| Decil de renda | 0,57 | 0,26 | 45% |
| log(capital social) | 0,35 | 0,15 | 42% |
| Vitalício / Black / CDL | 0,56 / 0,36 / 0,32 | 0,14 / 0,10 / 0,08 | **25% / 28% / 24%** |
| Sócio (@0,95) | 0,27 | 0,009 | **morre (p=0,49)** |

- **O canal Comercial é a variável mais forte** (OR 2,78 por desvio-padrão) e não aparece em análise univariada de demografia. Mecenas de bolsa é venda consultiva.
- **Vitalício, Black e CDL são quase inteiramente proxy** (perdem 72–76%). Servem de filtro, não são causa — **podem sair das regras sem perda relevante.**
- ⚠️ **`vl_total_outras` inverte de sinal no multivariado — colinearidade (r = 0,92 com o maior ticket), não achado. Não interpretar.** Usar `vl_maior_tx_outras`. Mediana do maior ticket: R$ 708 (doador) vs. R$ 180 (base).

### 8. O score de ML em produção não discrimina — está pior que a base

`ml_models.dtm_lead_score_predictions_upsell_current` (`upsell_mecenas_in_30_days`), teste out-of-time limpo:

| Abordagem | Elegíveis | Converteram | Por 10k | Lift OOT |
|---|---|---|---|---|
| **S1 capital1M+ & black/amex & vitalício** | 3.102 | 11 | **35,5** | **28,6×** |
| **S3 black/amex & vitalício & gasto 2k+** | 19.776 | 46 | **23,3** | **18,7×** |
| S5 black/amex & gasto 2k+ | 13.076 | 10 | 7,7 | 6,2× |
| ML p50-80 | 179.539 | 72 | 4,0 | 3,2× |
| ML p90-95 | 29.526 | 9 | 3,1 | 2,5× |
| **ML p95+** | 33.256 | 9 | **2,7** | **2,2×** |
| ML p80-90 | 59.515 | 16 | 2,7 | 2,2× |
| ML p<50 | 296.906 | 70 | 2,4 | 1,9× |

**O p95+ do modelo converte menos que o p50-80 e quase igual ao p80-90** — o ranking continua invertido no topo, e o lift histórico aparente é vazamento. **Regras simples batem o modelo em ~13×.** Não usar o score para priorizar Mecenas até retreino com validação temporal.

**A logística própria empata com as regras, não supera:** top 1% = lift 18,2× contra 18,9–24,2× de S1/S3. O que ela agrega é a curva de trade-off (top 2% = 13,7% capturando 27%; top 10% = 6,7× capturando 67%).

### 9. Os públicos a abordar

Bolsões de quem **ainda não doou**:

| Segmento | Bolsão | Membros ativos | Já doaram | Lift | Doação esperada |
|---|---|---|---|---|---|
| **S1 Patrono** — capital 1M+ & black/amex & vitalício | **3.138** | 3.044 | 11,8% | **20,2×** | R$ 14.939 |
| **S3 Fiel rico** — black/amex & vitalício & gasto 2k+ | **19.861** | 18.686 | 9,5% | **16,2×** | R$ 6.434 |
| S6 Certificação & premium | 225 | 93 | 8,2% | 14,0× | R$ 5.250 |
| S5 Alto gasto premium | 11.442 | 8.727 | 5,0% | 8,6× | R$ 5.742 |
| S2 Empresário premium — capital 1M+ & black/amex | 16.206 | 9.140 | 2,7% | 4,7× | R$ 12.161 |
| S4 Sócio qualificado — sócio & black/amex & decil 9+ | 19.748 | 11.505 | 1,9% | 3,3× | R$ 5.894 |

**Ordem de ataque: S1 → S3 → S2.** S1+S3 = 23,0k pessoas com lift 16–20×.

### 10. Direcionamento de mídia (para o time de marketing)

**a) Maturidade da base é o filtro nº 1 — e é gigante.** Quem tem menos de 2 anos de casa praticamente não doa: 682.403 pessoas (44% do universo) produziram 303 doadores. `<1 ano` = lift **0,04×** · `1–2 anos` = **0,09×** · `4–7 anos` = 2,35× · `7+ anos` = 7,59×. **Excluir quem tem menos de 2 anos de qualquer campanha de Mecenas** — é quase metade do alcance pago indo para audiência que não converte. Mecenas é produto de base madura, não de aquisição.

**b) Novembro e dezembro são mortos.** Nov (3,1%) + dez (0,9%) = **4% do ano**, contra 8,3% esperado por mês. Black Friday e Natal canibalizam — a base está comprando produto para si. Pico em março (12,0%). ⚠️ Contraintuitivo (dezembro é o mês de filantropia no hemisfério norte). Mas o **ticket sobe** (R$ 6.660 em nov, o maior do ano): nov/dez servem para abordagem individual do Comercial ao tier alto, não para campanha de volume.

**c) Geografia — Brasília destoa.** DF lift **1,69×** (maior do país, provável concentração de servidores de alto escalão). SP 1,23× e **maior doação média, R$ 6.811** — principal mercado em receita. RS 1,15×. MG abaixo da média (0,84×). Nordeste inteiro entre 0,41× e 0,65×.

**d) A janela não é pós-compra imediata.** Só **13,5%** doam em até 30 dias da compra anterior; **40,5% doam 6–12 meses depois**, alinhado ao ciclo anual da assinatura. Retargeting pós-compra imediato não é o caminho — a campanha deve mirar quem comprou algo **há 6–12 meses**.

**e) Como levar ao Meta.** Os atributos que discriminam (cartão black, capital social, decil de renda) **não existem como segmentação na plataforma**. O caminho é **custom audience a partir de S1/S3 → lookalike**, nunca targeting por interesse. Os bolsões (3,1k e 19,7k) estão acima do mínimo para semente.

**f) Copy.** O eixo é "quem já provou que compra caro aqui", não "quem é rico". E o setor de maior propensão e maior doação é o **financeiro** (3,71×, R$ 13.214) — junto de imobiliário e saúde. Convergente com a análise de profissão de 05/08 (saúde 1,93×, médicos = maior profissão individual).

### 11. ⚠️ Gatilho de conteúdo — inconclusivo

Duas execuções independentes discordam. **Robusto:** El Salvador **não** é gatilho (lift 0,93–0,98 apesar de liderar o ranking absoluto) e "Pedagogia do Abandono" tem sinal (1,97–2,10×, único conteúdo de educação). **Não robusto:** "A Vida dos Santos" (0,75 vs 2,38), "Temas em alta" (0,77 vs 1,71) e o cluster de denúncia/corrupção.

Causa diagnosticada: a execução com N=3.747 incluía os order bumps de R$ 180 (consumo prévio ~zero), que subestimam todos os lifts. A execução limpa (N=1.001) corrige, mas fica com 30–40 doadores por playlist — ruidosa demais para conclusão por playlist individual. **Seção deixada fora do relatório.**

**Duas regras metodológicas que ficam validadas:** (1) ranking absoluto de playlist não serve para segmentar — sempre usar controle com data-âncora pareada; (2) excluir o order bump de R$ 180 de qualquer análise de doador.

### 12. Os cinco ICPs (k-means)

Clusterização dos 8.995 doadores de bolsa. **O valor da doação não entra no modelo** — não é conhecido antes de a pessoa doar, e incluí-lo produziria perfis impossíveis de localizar na base. O mesmo modelo é aplicado aos 618,5k membros ativos para dimensionar o alvo de mídia de cada perfil.

Com o Solidário fora do label (analisado à parte, §13), os doadores de bolsa se separam por dois eixos limpos: **tem empresa** × **tem histórico de produto high-ticket**. K=4; um dos clusters é resíduo de 10 pessoas e foi descartado.

| ICP | Doadores | % receita | Doa | Marca registrada | Alvo na base | Lift |
|---|---|---|---|---|---|---|
| **A · Empresário** | 3.546 | **52,6%** | R$ 7.780 | 91% sócio · 31% capital 1M+ · 70% homem | **36.656** | 6,2× |
| **B · Vitalício fiel** | 2.673 | 27,4% | R$ 5.378 | 89% vitalício · 22% certificação · só 4,7% sócio · 47% mulher | 29.930 | 5,7× |
| **C · Assinante comum** | 2.766 | 19,9% | R$ 3.779 | 0% vitalício · 0% certificação · gastou só R$ 1.221 | **106.299** | 1,8× |

- **A e B são o ponto ótimo de mídia** e valem quase o mesmo: propensão 6,2× e 5,7×, somando 66,6k pessoas. ⚠️ **Pedem mensagens opostas**: A é patrocínio/legado (financia como quem patrocina obra), B é pertencimento (continuação de anos acompanhando a BP) — e B é o único em que o conteúdo da formação é argumento, porque ele é aluno. Rodar uma campanha só desperdiça um dos dois: é a decisão de criativo mais concreta desta análise.
- **B tem o maior gasto prévio** (R$ 5.832) — mais que o empresário. O dinheiro dele vem de salário ou patrimônio, não de CNPJ.
- **C → volume.** Maior bolsão (106,3k), propensão 1,8×. Notável: gastou R$ 1.221 e doa R$ 3.779 — **doa mais do que já gastou na vida**. Capacidade de doar não se lê pelo consumo passado.

**Fora dos clusters:** 411 doadores (4,6%, 5,8% da receita) gastaram < R$ 100 antes de doar — para **98% deles a doação foi a primeira compra na BP**, com R$ 7.341 médios. Vieram pela causa, sem funil de produto. Candidato a teste de aquisição falando só da causa.


### 13. Mecenas Solidário — a campanha atual

Produto lançado em jul/2026: contribuição recorrente a partir de ~R$ 30/mês, sem teto. **203 pessoas, R$ 112 mil.** Faixa escolhida:

| Faixa | Pessoas | % | Receita |
|---|---|---|---|
| R$ 1/dia (R$ 358,80) | 118 | 58,1% | R$ 42.697 |
| R$ 2/dia (R$ 718,80) | 63 | 31,0% | **R$ 46.003** |
| R$ 3/dia (R$ 1.078,80) | 17 | 8,4% | R$ 18.340 |
| Mensal (R$ 27 a 97) | 3 | 1,5% | R$ 151 |
| Pacote do Comercial (R$ 2 mil+) | 2 | 1,0% | R$ 5.250 |

⚠️ **A faixa de R$ 2/dia arrecada mais que a de R$ 1/dia** (R$ 46,0k vs R$ 42,7k) com metade das pessoas. Há espaço para posicionar o degrau do meio como padrão.

#### O achado: mesmo dinheiro, pessoa diferente

| Atributo | **Solidário (180)** | Doador de bolsa (8.972) | Membro ativo | Significância |
|---|---|---|---|---|
| Contribuição típica | R$ 359 | R$ 2.148 | — | — |
| **Mulheres** | **51,4%** | 40,7% | 37,8% | **p=0,005** ✓ |
| **Idade mediana** | **62 anos** | 53 anos | 51 | **p=0,0003** ✓ |
| Renda no topo (decil 9-10) | 43,6% | 40,0% | 17,6% | p=0,36 ✗ |
| Cartão black/amex | 60,7% | 62,8% | 28,1% | p=0,58 ✗ |
| Já tem vitalício | 35,0% | 44,0% | 10,3% | p=0,019 ✓ |
| **Gasto prévio (mediana)** | **R$ 1.230** | R$ 2.494 | R$ 360 | **p<0,001** ✓ |
| Já comprou pelo Comercial | 46,1% | 99,9% | 27,9% | — |

**O ticket baixo não é limitação de renda.** Renda e cartão são estatisticamente **iguais** aos do doador de bolsa — e o fato de não serem distinguíveis é o achado, não falta de dado. Quem compra Solidário tem o mesmo poder aquisitivo de quem patrocina uma bolsa de R$ 1.668; contribui menos porque essa é a porta que passou a existir para ele.

**O que muda é quem ele é:** mais velho (62 vs 53), mais feminino (51% vs 41%) e com metade do histórico de compra na BP. **É a persona que o Mecenas clássico não alcançava** — e a mensagem de "patrocine uma bolsa" não é a que a converte.

**Metade não passa pelo Comercial** (46% vs 99,9% do doador de bolsa): é o primeiro produto Mecenas que converte sem venda consultiva.

**Canibalização:** 23 pessoas que já eram doadoras de bolsa também compraram Solidário — e são as de maior gasto prévio do grupo (mediana R$ 4.322), 100% via Comercial, 57% vitalício. Vale checar se estão trocando bolsa por contribuição mensal.

⚠️ Ressalva: a idade só existe para uma fração da base (n=58 no Solidário), então a mediana de idade é a menos firme das quatro diferenças significativas.


## Pendências / próximos passos

- [ ] Gerar a **lista nominal** de S1 e S3 para o Comercial, aplicando as exclusões obrigatórias de `listas-comercial.md` (Zenvia 30d, Pipedrive, blacklist, triple-check e-mail+telefone+CPF). ⚠️ Lista nominal não entra no repo (é público).
- [ ] **Refinar as regras dos segmentos** conforme §7: trocar `vl_total_outras` por `vl_maior_tx_outras`, adicionar `bl_ja_comprou_comercial`, retirar vitalício/Black/CDL. Revalidar out-of-time depois.
- [ ] **Decisão de produto:** os ~51 compradores de Solidário com Black/vitalício devem receber oferta de upgrade? Definir régua antes que o teto de R$ 359 se institucionalize.
- [ ] Reportar ao time de ML o problema do `upsell_mecenas_in_30_days` (p95+ abaixo da base out-of-time).
- [ ] **Reconstruir a base com features as-of** (não all-time) se for treinar modelo de produção — hoje há vazamento nos positivos recentes.
- [ ] Concluir o gatilho de conteúdo agrupando playlists por tema e ampliando a janela para 2025+2026 (elevar N).

## Queries

| Arquivo | O que faz |
|---|---|
| [00_base_qualificacao.sql](queries/00_base_qualificacao.sql) | Materializa `bp-staging.dbt_abe.tb_mecenas_qualificacao_base` — 1 linha por e-mail, label + features |
| [00a_sanity_volume_mensal.sql](queries/00a_sanity_volume_mensal.sql) | Volume/receita por mês |
| [00b_sanity_pessoas_por_tier.sql](queries/00b_sanity_pessoas_por_tier.sql) | Dimensionamento por tier |
| [00c_ofertas_mecenas.sql](queries/00c_ofertas_mecenas.sql) | Catálogo de ofertas e tickets |
| [01a_geografia_resumo.sql](queries/01a_geografia_resumo.sql) | Distribuição geográfica |
| [02_lift_univariado.sql](queries/02_lift_univariado.sql) | Lift por feature vs. taxa base |
| [03_cnpj_controle_confusao.sql](queries/03_cnpj_controle_confusao.sql) | Sócio controlando renda × cartão |
| [04_perfil_por_tier_vs_base.sql](queries/04_perfil_por_tier_vs_base.sql) | Ficha de perfil por tier vs. controle |
| [05_validacao_out_of_time.sql](queries/05_validacao_out_of_time.sql) | Modelo ML vs. segmentos, teste temporal |
| [06_segmentos_bolsoes.sql](queries/06_segmentos_bolsoes.sql) | Segmentos e tamanho dos bolsões |
| [07_perfil_por_safra.sql](queries/07_perfil_por_safra.sql) | Perfil do comprador por safra |
| [08_lift_playlist_pre_compra.sql](queries/08_lift_playlist_pre_compra.sql) | Lift de playlist com data-âncora pareada (inconclusivo — ver §10) |
| [00b_person_map.sql](queries/00b_person_map.sql) | Mapa conta do gateway → pessoa real (id_person) |
| [09_cnpj_capital_setor.sql](queries/09_cnpj_capital_setor.sql) | Propensão por capital, nº de empresas e CNAE |
| [10_direcionamento_midia.sql](queries/10_direcionamento_midia.sql) | Sazonalidade, geografia por UF e janela pós-compra |
| [11_perfil_solidario.sql](queries/11_perfil_solidario.sql) | Perfil do Mecenas Solidário vs doador de bolsa vs controle |
| [12_lista_abordagem_fundador_black.sql](queries/12_lista_abordagem_fundador_black.sql) | Lista de abordagem: Membros Fundadores + Black, com exclusões |

**Modelos:** [modelo/icp_clusters.py](modelo/icp_clusters.py) — k-means dos 5 ICPs + dimensionamento do alvo. [modelo/logistica_multivariada.py](modelo/logistica_multivariada.py) — logística com validação out-of-time e blocos de controle para o CNPJ. Saídas em `modelo/saida/`.

**Relatório:** `index.html` + `data.json` + `refresh.py` (padrão do portal). Atualizar com `python refresh.py --push`.

Tabela materializada: `bp-staging.dbt_abe.tb_mecenas_qualificacao_base` (1,61M linhas).

## Wiki atualizada

- `wiki-brasil-paralelo/pages/mecenas-perfil.md` — **criada**: perfil do doador, lifts, segmentos, CNPJ, Solidário, gatilho inconclusivo
- `wiki-bp/pages/mecenas.md` — gotcha do 2º order bump (não tem "order bump" no nome) + tabela materializada
- `wiki-bp/pages/bq-schema-extra.md` — `dim_entrepreneurs`: usar capital, não a flag; e o alerta sobre o score de ML
- `wiki-bp/pages/metricas-referencia.md` — taxa base, tabela de lift, concentração, reconciliação com a análise de profissão
