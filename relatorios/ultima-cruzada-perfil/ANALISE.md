# Coleção Brasil: A Última Cruzada — perfil do comprador e abordagem do Comercial

**Data da análise:** 04/09/2026 · **Atualizado:** 22/09/2026 · **Janela:** 01–22/09/2026 (lançamento 01/09)

> Números do fechamento de **22/09/2026 14h15**. **A versão viva é o relatório HTML** — `python refresh.py`
> regera `data.json` e a página inteira a partir das queries de `queries/`.
>
> ⚠️ **O mix de canal se estabilizou.** Na primeira semana o Comercial fazia 66% do volume,
> caiu para 40,4% em 08/09 e voltou a 47,3% com a operação comercial rodando em ritmo pleno —
> os dois canais hoje vendem quase o mesmo (1.621 × 1.804 compradores, receita praticamente
> empatada). Como vendem para públicos diferentes, todo agregado depende do mix.
> **O comprador de cada canal não mudou.** Ver §"Comercial e digital vendem para pessoas diferentes".
>
> ⚠️ **A leitura do disparo em massa mudou entre 08 e 22/09** — ver §"Abordagem do Comercial".

## Pergunta original

Quem está comprando a Coleção Brasil: A Última Cruzada — membros ou não? Qual o perfil
(renda, cartão, consumo, engajamento, tempo de casa)? E como o Comercial está abordando?

## Decisões de abordagem

- **Universo**: `nm_gateway_plan LIKE 'colecao-brasil%'` **OU** produto contendo "Coleção Brasil".
  A wiki documentava só 2 planos; existem **4** (`-fisico`, `-completo`, `-completo-cursos`,
  `-digital`) + bundles em `nm_gateway_plan = 'black'` (`Última Cruzada + Black Vitalício/Anual`).
  Filtrar só pelos 2 documentados perderia ~30% das vendas.
- **Chave de pessoa**: e-mail normalizado (cobre multi-conta). 3.425 compradores aprovados no fechamento de 22/09.
- **Membership**: whitelist de tiers de `bq-regras.md`, **excluindo os planos do próprio livro**
  (produto físico gera assinatura-fantasma — sem isso, 100% viraria "membro ativo").
- **Vitalício**: `bl_lifetime_offer` restrito a planos GBB/produto com "Vitalício", excluindo
  `colecao-brasil|odisseia|clube-do-livro` (esses vêm com a flag ligada sem ser vitalício).
- **Abordagem**: as conversas Zenvia do produto foram identificadas por **regex no texto da
  conversa** (`última cruzada|coleção brasil`) — o Zenvia **não tem etiqueta/etapa própria do CBR**
  (`nm_latest_lead_product_detail` segue com VITALÍCIO GBB / BLACK / MECENAS).
- **Buckets de abordagem mutuamente exclusivos** (corrigido pós-auditoria): a 1ª versão classificava
  o prospect por `MIN(template)` e jogava no bucket "broadcast" todo prospect tocado pelo disparo,
  inclusive os que também tiveram atendimento de vendedor. Os 384 prospects mistos (6,6% do bucket)
  concentravam 96,8% das respostas e 82,6% das vendas atribuídas ao disparo — a taxa de resposta
  aparecia como 5,3% em vez de **0,18%**. Agora há três grupos disjuntos.
- **Guarda de causalidade na atribuição**: "abordado" exige abordagem anterior à compra. Sem ela,
  metade das vendas "abordado → digital" era de gente abordada depois de já ter comprado.
- **Detector de script**: a assinatura da abertura pula os 40 primeiros caracteres — quase todo
  script começa com o primeiro nome do cliente, e comparar o início faz disparo de massa parecer
  mensagem única (media 13% de script onde o real é 98%).
- Benchmark de renda/cartão calculado sobre os 604k membros ativos, para não ler nível de cartão
  em absoluto (gotcha de `bq-acesso.md`: Black+ sozinho não é sinal de elite).
- **Corte por canal em vez de por "fase" da campanha** (decisão de 08/09): a tentação era comparar
  semana 1 × semana 2, mas 05–06/09 é fim de semana e 07/09 é feriado — o Comercial não vende nesses
  dias, então a queda dele é calendário, não estratégia. O corte por canal isola o efeito real:
  o comprador de cada canal não mudou, mudou o peso de cada canal no mix.

## Achados principais

### Resultado em 22 dias
- **3.425 compradores / R$ 3.564.068** (ticket médio R$ 1.040).
- **Comercial 1.621 (47,3%) / R$ 1.785.079**;
  Digital 1.804 / R$ 1.778.989 — receita praticamente empatada entre os canais.
- Curva diária (compradores, Comercial|Digital): 01/09 0|3 · 02/09 76|8 · 03/09 107|68 · 04/09 121|75 · 05/09 23|128* · 06/09 9|155* · 07/09 54|134* · 08/09 129|86 · 09/09 103|93 · 10/09 160|59 · 11/09 109|55 · 12/09 25|58* · 13/09 23|75* · 14/09 104|60 · 15/09 76|36 · 16/09 121|84 · 17/09 117|65 · 18/09 109|116 · 19/09 12|140* · 20/09 17|160* · 21/09 91|91 · 22/09 35|55
  — `*` = fim de semana ou feriado (o Comercial não vende nesses dias; o digital não para).
  ⚠️ O último dia é parcial.
- **A venda não desacelerou na 3ª semana**: o pico do Comercial é 10/09 (160) e o do digital 20/09 (160).
  O padrão semanal é nítido — Comercial cai para 9–25 em fins de semana e feriado, o digital sobe.
  Quem lê o dia isolado lê calendário, não desempenho.
- Mix de produto: Físico 2.369 (ticket R$ 956),
  Completo 927 (R$ 1.260),
  Digital 109 (R$ 379), Bundle Black 15 (R$ 4.364).
- **Recusa/abandono**: 1.448 pessoas (1.931 tentativas) —
  42% do número de compradores, sem fluxo de recuperação aparente. O volume cresceu junto com a venda.

### Comercial e digital vendem para pessoas diferentes
O mesmo produto, dois públicos. É isso que explica a diluição do agregado.

| Indicador | Comercial | Digital | Razão |
|---|---:|---:|---:|
| Compradores | 1.621 | 1.804 | ÷1,1 |
| Ticket médio | R$ 1.101 | R$ 986 | 1,1× |
| Membro ativo | 76,8% | 59,3% | 1,3× |
| Vitalício | 62,6% | 35,8% | **1,7×** |
| Comprou o CDL | 49,6% | 37,2% | 1,3× |
| 1ª compra na BP | 6,4% | 14,4% | ÷2,3 |
| LTV anterior (mediana) | R$ 4.960 | R$ 2.472 | **2,0×** |
| Cartão premium | 82,9% | 83,4% | ~1× |
| Sem sessão em 90d | 38,5% | 61,3% | ÷1,6 |

- O Comercial vende para a base fiel; o digital para um público **muito mais frio em vínculo**
  (35,8% de vitalícios contra 62,6%, LTV 2,0× menor). A distância encolheu com o tempo, mas se mantém.
- ✅ **Mas o poder de compra é o mesmo**: cartão premium 82,9% × 83,4%
  e ticket na mesma faixa. A mídia não desceu de faixa econômica — está alcançando o mesmo tipo de
  gente com dinheiro que ainda não tem vínculo forte com a BP. Canais complementares, não substitutos.

### Vínculo com a base (agregado — ler junto com o corte por canal acima)
- **89,4% já eram clientes**; 363 pessoas fizeram a 1ª compra na BP
  (eram 13 em 04/09 e 94 em 08/09 — o crescimento é quase todo do digital).
- **67,6% membros ativos · 48,5% vitalícios ·
  13,3% Mecenas · 43,1% compraram o CDL ·
  17,8% a Odisseia.**
- **LTV anterior mediano R$ 3.402**; 45,9% já gastou R$ 4 mil+.
- **Tempo de casa mediano 3,98 anos** (média 3,79).
- **Penetração de 5,9% entre os 24,9k compradores do CDL** (1.475 pessoas; era 1,93% em 08/09) —
  o público natural da carteira ainda tem folga, mas está sendo consumido rápido.

### Perfil socioeconômico (acima da base, com folga)
| Indicador | Compradores UC | Base membros ativos | Lift |
|---|---:|---:|---:|
| Cartão premium (Black/Amex/Platinum) | 83,1% | 57,4% | **1,4×** |
| Cartão nível Black | 60,9% | 30,7% | **2,0×** |
| Renda (decil 8–10 do CEP) | 54,4% | 31,8% | **1,7×** |

- Gênero inferido: 64% masculino.
- Idade (dado em 1.823 de 3.425): **74% tem 45 anos ou mais**.
- Geografia: SP 30%, RJ 11%, MG 10%, RS 8%, PR 7%, SC 6%, DF 5%.
- Pagamento: 84% cartão (12x é o padrão de todas as ofertas), 14% Pix.

### Engajamento: compra sem consumo
- **50,5% dos compradores não teve nenhuma sessão na plataforma nos últimos 90 dias** (era 43% em 04/09 — subiu com o peso do digital, que tem 61,3%).
  Só 8% são usuários de alto engajamento (11+ dias ativos em 90d).
- O produto físico vende para quem **tem vínculo mas não consome** — colecionador, não espectador.
- O Comercial converte melhor exatamente na faixa engajada leve/média (56–68% das vendas dessas
  faixas são comerciais) e pior nos totalmente inativos (36%).

### Abordagem do Comercial: o disparo abre conversa, mas não vende
**20.201 prospects abordados** desde o lançamento. Grupos mutuamente exclusivos.

| Tipo de abordagem | Prospects | Respondeu | Comprou | Conversão | Receita | Abertura scriptada |
|---|---:|---:|---:|---:|---:|---:|
| Disparo em massa (só a peça) | 2.583 | **13,55%** | 43 | **1,67%** | R$ 49.625 | 88% |
| Disparo + atendimento de vendedor | 23 | 73,91% | 3 | 13,04% | R$ 2.854 | 87% |
| Abordagem do vendedor (sem disparo) | 17.595 | **31,44%** | 744 | **4,23%** | R$ 837.647 | 54% |

⚠️ **A leitura do disparo mudou entre 08 e 22/09.** Em 08/09 a peça de disparo parecia inerte
(0,23% de resposta, 16 vendas). Com a base completa ela responde a **13,55%** e converte a 1,67%.
O que não mudou é a comparação: **quem é atendido por vendedor sem disparo converte 2,5× mais**
(4,23% × 1,67%) e traz 17× mais receita.

- ⚠️ **O disparo não aquece — ele seleciona** (conclusão mantida, com margem menor).
  Controlando pela etapa `carteiraMecenas`: disparo puro **1,8%** · disparo + atendimento 13,6% ·
  **vendedor sem disparo 9,87%**. Quem recebeu a peça antes de falar com o vendedor
  continua convertendo bem menos que quem nunca recebeu.
- ⚠️ **O mecanismo segue não testado.** 54% das "abordagens de vendedor" abrem com
  texto repetido em 20+ conversas (era 77% em 08/09 — caiu conforme o atendimento humano
  ganhou volume). A diferença na taxa de resposta é real, mas ainda não é personalização medida.
- `carteiraMecenas` concentra a operação: 8.847 prospects,
  695 vendas (7,86%). As etapas `tentativa1`/`tentativa2`/`contatoNegociacao` somam
  10.629 prospects e apenas 54 vendas (~0,5%) — é onde o esforço se perde.
- Vendas entre **35 vendedores** (líder com 181).
- 332 pessoas compraram **antes** de serem abordadas — já descontadas da atribuição.

### Dentro das conversas: o que o cliente escreve
Base: **5.875 prospects que responderam** (24.422 mensagens), 12,3% compraram.

- **37,7% nunca escreveram nada** — só clicaram no botão do WhatsApp ou
  mandaram "sim/ok" (6,1% de conversão).
- Conversão por profundidade: só clique 6,1% → 1 fala 9,0% →
  2–3 13,7% → **4+ falas 29,9%**. ⚠️ Parte é causalidade reversa:
  frete/endereço e "paguei" são temas **pós-decisão**.
- ⚠️ **"Quanto custa" é o tema mais comum (1.197 pessoas) e converte
  17,2% — abaixo da média de 16,1% de quem escreve… e bem abaixo de
  parcelamento (31,0%) e "o que é / conteúdo" (27,9%).**
  Quem pergunta preço está comparando; quem pergunta como pagar já decidiu.

**Pedir desconto não é objeção — é sinal de compra** (conclusão mantida):

| Sinal na fala | Prospects | Conversão |
|---|---:|---:|
| ✅ Pediu desconto ou condição melhor | 287 | **29,6%** |
| ✅ Citou ser cliente fiel (vitalício / CDL / Odisseia) | 187 | **28,9%** |
| ❌ Declarou restrição financeira | 191 | 8,4% |
| ❌ Achou caro (juízo de valor) | 124 | 12,9% |
| ❌ Clicou por engano / curiosidade | 73 | 2,7% |
| ❌ Ainda pagando o vitalício | 11 | 9,1% |

Base 12,3%. Dois clientes diferentes na mesma frase sobre dinheiro — quem negocia e quem
não tem — e o roteiro não os separa.

**Fricções operacionais:**

| Fricção | Prospects | Conversão |
|---|---:|---:|
| Pediu condição citando fidelidade | 279 | 20,8% |
| Travou no campo de cupom do checkout | 51 | 60,8% |
| Esperando entrega de CDL / Odisseia | 54 | 22,2% |
| Confundiu com a série de 2018 ou com o CDL | 9 | 22,2% |
| Não sabe onde acessar o que comprou | 31 | 25,8% |
| Achava que já estava incluído no plano | 6 | 33,3% |

- **Não há política de fidelidade**: 279 pessoas pediram condição citando ser
  vitalício/CDL/Odisseia. Resposta do vendedor (83 conversas):
  vai verificar / consegue 18 · passa um cupom 6 · nega — preço fechado 6 · cita a fidelidade do cliente 7 — cada um decide na hora.
- **Campo de cupom sem código divulgado** trava a compra no último passo.
- **54 pessoas em abordagem esperam um produto físico anterior** — risco evitável
  com cruzamento de lista.
- O nome reaproveita a **série "A Última Cruzada" de 2018–2019** (~13k transações antigas na fct).

⚠️ **Privacidade**: transcrições têm nome/telefone. **Nenhuma citação literal publicada** — o repo é
público. A query fica versionada, o texto não; o `data.json` recebe apenas contagens.

### Atribuição: o Comercial trabalha a nata, o digital alcança o resto
⚠️ "Abordado" exige abordagem **antes** da compra. **27 compradores foram
abordados só depois de já ter comprado** (higiene de lista).

| Origem | n | Ticket | Membro | Vitalício | LTV mediana |
|---|---:|---:|---:|---:|---:|
| Abordado → venda Comercial | 651 | R$ 1.150 | 75% | 54% | R$ 3.751 |
| Abordado → venda Digital | 139 | R$ 1.014 | 76% | 53% | R$ 3.057 |
| Comercial sem abordagem prévia | 970 | R$ 1.067 | 78% | 69% | R$ 5.830 |
| **Digital sem abordagem prévia** | **1.665** | R$ 983 | **58%** | **34%** | **R$ 2.302** |

- **23% dos compradores foram abordados antes de comprar** (60% em 04/09, 37% em 08/09 — cai
  porque o digital cresce, não porque o Comercial abordou menos).
- Crédito ambíguo: 139 vendas (R$ 140.978) no digital com abordagem prévia.
- **O grupo majoritário é o digital sem abordagem nenhuma**: 1.665 pessoas
  (48,6% dos compradores), com 34% de vitalícios contra
  69% do Comercial espontâneo e LTV mediano 60% menor.
- ⚠️ **O Comercial espontâneo tem o melhor perfil da campanha** (LTV mediano R$ 5.830, 69%
  vitalícios): é a carteira comprando por conta própria, sem custo de abordagem.

### Preço: o Comercial vende mais barato que o site
⚠️ **Essa leitura se inverteu com a campanha madura.**
- **Físico**: ticket médio **igual nos dois canais (R$ 960)**.
- **Completo**: Comercial **R$ 1.330** vs Digital R$ 1.186 — agora o Comercial vende *mais caro*,
  puxado pelo mix (ele empurra a versão com cursos).
- **Faixas simultâneas** na versão física (compradores Comercial/Digital):
  R$ 719 (121C/7D) · R$ 901 (50C/0D) · R$ 911 (7C/121D) · R$ 948 (610C/0D) · R$ 959 (151C/984D) ·
  R$ 1.068 (7C/53D). A faixa mais barata segue quase exclusiva do Comercial, mas o grosso de cada
  canal se concentra em preços vizinhos (R$ 948 × R$ 959).
- Pendente confirmar com o time se a dispersão é teste controlado ou desconto discricionário.

## Pendências / próximos passos

- [ ] **Confirmar a política de preço**: 6 faixas simultâneas no físico, a mais barata quase
      exclusiva do Comercial. Teste controlado ou desconto livre do vendedor?
- [ ] **Definir condição de fidelidade publicada** por tier (vitalício / CDL / Odisseia). É o pedido
      mais frequente na conversa e hoje cada vendedor decide na hora.
- [ ] **Corrigir o campo de cupom do checkout** — exibe campo sem código divulgado e trava a compra
      no último passo.
- [ ] **Cruzar a lista de abordagem com entregas pendentes** de CDL/Odisseia antes de disparar.
- [ ] **Testar o mecanismo do disparo** (o dado não separa): A/B de remetente (blast × número do
      vendedor) e de formato (peça longa com imagem × texto curto) na mesma lista.
- [ ] **Higiene da lista**: compradores estão sendo abordados depois de já ter comprado.
- [ ] Pedir **etiqueta/etapa própria do CBR no Zenvia** — a medição depende de regex no texto.
- [ ] Lista de reabordagem das recusas (limite/cartão), com perfil idêntico a quem comprou.
- [ ] **CAC do digital**: com 22 dias e 1.804 compradores digitais, já dá para cruzar com o custo de
      mídia e saber se o comprador frio do digital se paga. É a pendência mais relevante hoje.
- [ ] **Churn de parcelamento** ainda não medido (12x é o padrão de todas as ofertas).

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [queries/universo_vendas.sql](queries/universo_vendas.sql) | Universo por plano/canal/status | ✅ |
| [queries/base_compradores.sql](queries/base_compradores.sql) | Cria `bp-staging.dbt_abe.tb_uc_compradores` (1 linha/comprador, todos os atributos) | ✅ |
| [queries/perfil_agregado.sql](queries/perfil_agregado.sql) | Renda, cartão, gênero, pagamento, UF | ✅ |
| [queries/benchmark_base.sql](queries/benchmark_base.sql) | Benchmark cartão/renda na base de membros ativos | ✅ |
| [queries/funil_abordagem.sql](queries/funil_abordagem.sql) | Cria `tb_uc_abordagens`; funil disparo→resposta→venda por template | ✅ |
| [queries/etapa_zenvia_compradores.sql](queries/etapa_zenvia_compradores.sql) | Etapa Zenvia dos compradores | ✅ |
| [queries/atribuicao_perfil_por_origem.sql](queries/atribuicao_perfil_por_origem.sql) | Perfil por origem (abordado × canal) | ✅ |
| [queries/amostra_transcricoes.sql](queries/amostra_transcricoes.sql) | Amostra de conversas para ler o pitch | ✅ |
| [queries/conversas_falas_cliente.sql](queries/conversas_falas_cliente.sql) | Separa turnos `seller:`/`prospect:` e devolve as falas com desfecho (⚠️ PII — uso local) | ✅ |

## Entrega

Relatório HTML no portal: `relatorios/ultima-cruzada-perfil/` (card em **Base & Produtos**).
Estrutura padrão — `index.html` (layout + gráficos, nada hardcoded) + `data.json` (gerado) +
`refresh.py` (materializa as tabelas de trabalho e regera o JSON) + `queries/` + este arquivo.
Atualizar com `python refresh.py --push`.

Paleta dos gráficos validada com o validador da skill `dataviz`
(3 slots: azul `#3b6ef5` → âmbar `#b45309` → verde `#0f8a4d`; a paleta anterior da casa falhava na
banda de luminosidade e no piso de croma). Rótulos diretos em todas as barras são o encoding
secundário exigido pelo ΔE 6,6 do par âmbar↔verde.

## Aba no dashboard vendasbp (08/09/2026)

O relatório foi portado para uma aba do dash da campanha, para acompanhar a evolução sem regerar
o HTML à mão: `vendasbp.com/dashboard-campanha/Coleção Brasil?tab=perfil-comprador`.

| Arquivo (repo `marketing-bp`) | Papel |
|---|---|
| `supabase/functions/fetch-campaign-buyer-profile/index.ts` | Resolve o universo (produto ou campanha) e roda perfil/benchmark/abordagem |
| `src/hooks/useCampaignBuyerProfile.ts` | `useCampaignBuyerProfile` (10min) + `useCampaignBuyerBenchmark` (12h) |
| `src/components/dash-campanha/CampaignBuyerProfileTab.tsx` | A aba |
| `src/pages/DashCampanha.tsx` | Trigger + content, ligados pela configuração |
| `src/lib/campaignViewPeriods.ts` | Registro da view como `optional` + `isExtraTabEnabled()` |
| `src/components/campaign-settings/ExtraTabsSection.tsx` | Configurações › "Abas extras" |
| `src/components/CampaignSettingsDialog.tsx` | A nova aba do dialog e o save |

**Abas extras são escolhidas por campanha** (evolução do pedido, 08/09): em vez de flag pelo nome
da campanha, a aba se registra em `CAMPAIGN_VIEWS_WITH_PERIOD` com `optional: true` e é ligada em
**Configurações › "Abas extras"**, persistindo em `campaign_dashboards.extra_tabs (text[])`. Ao criar
uma campanha nova, dá para escolher quais visões extras entram. Isso separa dois conceitos que
estavam misturados:

- `requires` (já existia) — automático: a aba Leads aparece se a campanha tem meta de leads;
- `optional` (novo) — decisão de quem monta o dash.

**Dois universos de compra**, escolhidos na mesma tela de configuração (evolução de 08/09):

- **produto** — quem compra os *Produtos BP* da campanha (`produto_bp_ids` → `nm_gateway_product`
  via `produto_bp_mappings`), por qualquer caminho. É o recorte para acompanhar um produto, como o livro.
- **campanha** — o que a campanha vendeu, pelas **mesmas regras de atribuição da aba Vendas**.

⚠️ **O matching de campanha NÃO foi reimplementado.** `_shared/campaignFilters.ts` é um par
espelhado **congelado** que unificou 10 implementações históricas (mudanças só pelo steward, com
autorização da Barbara). A function é um *chamador*, como as `compute-*`: usa o módulo e replica
apenas o bloco de exclusões, que por desenho fica no chamador. Eu ia replicar a regra em SQL —
teria criado a 11ª implementação, exatamente o problema que o módulo resolveu.

⚠️ **Mudança de semântica do "LTV anterior"**: agora é *tudo antes do início do período
selecionado*, não *tudo exceto este produto*. Foi preciso para a definição valer em qualquer
universo, mas muda números — "1ª compra na BP" passou de 95 para 124 pessoas no mesmo período,
porque quem comprou outra coisa dentro do período agora conta como sem histórico anterior.
O relatório HTML mantém a definição antiga; os dois não são comparáveis linha a linha.

⚠️ **O bloco de abordagem exige um "termo de conversa" configurado.** O Zenvia não tem etiqueta
por produto, então o universo de abordados só é definível por regex no texto. Sem termo, o bloco
não aparece (e a tela explica o porquê).

**Decisões de engenharia:**
- **Nada de texto de conversa sai do BigQuery.** A classificação dos temas roda dentro do SQL e a
  function devolve só contagens — as transcrições têm nome e telefone, e o browser é o pior lugar
  para isso (o repo já tem PII em 46 consumidores como problema conhecido).
- **Benchmark em bloco separado** (`block: 'benchmark'`): a query da base de membros custa ~9s e é
  quase estática; separada, trocar o período não a repaga.
- **Flags de tema por prospect, não cross join.** A primeira versão cruzava 13 regexes × 14k
  prospects e levava 22s; avaliando cada regex uma vez por prospect, caiu para 8s.
- **`dt_approach_start` sem `DATE()`** no filtro: a tabela é particionada por
  `DATETIME_TRUNC(dt_approach_start, MONTH)` e envolver a coluna em `DATE()` mata o pruning.
- **`ROLLUP` tem de agrupar pela coluna crua.** Agrupar pelo alias já com `IFNULL(...,'TOTAL')`
  faz a linha de rollup nunca vir NULL — o TOTAL não é emitido e o ticket sai somado em vez de
  médio. Peguei isso no preview, não em produção.
- **Conclusões derivadas, não fixas.** O texto sobre "o disparo aquece ou seleciona" e o de
  "pedir desconto é sinal de compra" são calculados do período selecionado. Isso importa: na
  janela de 30 dias o disparo+atendimento converteu **mais** que o vendedor sem disparo (7,9% ×
  6,4%), o inverso do fechamento de 08/09 — um texto fixo teria mentido. A aba mostra a relação
  medida e avisa que a leitura é frágil.
- **Sem animação nos gráficos** (`isAnimationActive={false}`): dashboard de dados não ganha nada
  com barras crescendo, e a animação atrasa a leitura.

⚠️ **Requer uma migration manual** — a coluna não existe ainda. No SQL Editor do Supabase:

```sql
alter table public.campaign_dashboards
  add column if not exists extra_tabs text[] default '{}'::text[],
  add column if not exists extra_tabs_config jsonb default '{}'::jsonb;
```

Enquanto ela não existir, o dialog salva todo o resto normalmente e mostra o SQL na aba
"Abas extras" (o UPDATE de `extra_tabs` é separado justamente para não derrubar o save inteiro).
O `types.ts` só é regenerado pela Lovable, então o update usa `as never` — padrão do repo.

⚠️ **Deploy da edge function é manual, via Lovable** — não sai no push (não há workflow de deploy e
as `fetch-*` não estão no `config.toml`). Enquanto a function não subir, a aba mostra erro de
carregamento. Verificar se subiu: `curl -X POST <url>/functions/v1/fetch-colecao-brasil-perfil`
→ **401 = no ar**, 404 = não deployada.

## ⚠️ A fonte do Zenvia revisou a série de abordagem para baixo (08–09/09/2026)

A `masterdata.dim_zenvia_approaches` foi recarregada em 08/09 (18:02) e os dias iniciais de
setembro voltaram com uma fração das abordagens. Reverificado em 09/09: **não se recuperou**.

| | Medido 04/09 | Medido 09/09 |
|---|---:|---:|
| Abordagens em 01–04/09 | 45.203 | **12.685** (−72%) |
| Conversas de 02/09 (total) | 21.623 | **3.998** |
| 02/09 mencionando a coleção | 6.483 | **1.341** |
| 03/09 mencionando | 4.382 | 1.235 |
| 04/09 mencionando | 2.532 | 1.436 |

**Onde está a perda — diagnóstico fechado em 09/09:** a dim está **fiel à staging**
(`int_zenvia_analytics`): para 02/09 as duas têm exatamente 3.998 abordagens distintas, e a dim não
tem `id_approach` duplicado (21.889 linhas = 21.889 distintos em 01–09/09). Ou seja, **a redução vem
da origem no Zenvia**, não da transformação dbt nem de dedup no meio do caminho. A carga segue
rodando normal para os dias novos (row_count subiu 2.917 entre 08 e 09/09).

**O que foi feito:** o relatório foi **regerado com os dados atuais** e a página ganhou um aviso
fixo na seção de abordagem. A decisão de 08/09 (esperar sem republicar) foi revista: com a perda
confirmada como persistente e originada na fonte, manter no ar um número que não se reproduz é pior
do que publicar o atual com a ressalva.

⚠️ **A perda foi SELETIVA — saíram os disparos sem resposta.** A taxa de resposta do disparo puro
saltou de 0,18% para 11,4% sem nada mudar na operação: o denominador perdeu os silenciosos.
Evidência: 31/08, outro dia de disparo em massa, preservou o padrão (12,7k conversas / 17,7% de
resposta), enquanto 02/09 ficou com 4,0k / 36,5%. Consequência: **as taxas do disparo nos dados
atuais estão infladas** — o disparo real é pior do que aparece. A conclusão de fundo (disparo frio
converte muito abaixo do atendimento humano) se mantém e fica conservadora. O grupo
*disparo + atendimento* colapsou (460 → 2 prospects), então o teste do "aquecimento" não é
calculável no período.

**Como ler os números de abordagem agora:**
- As **proporções entre os grupos se mantiveram** — o disparo puro continua com taxa de resposta e
  conversão muito mais baixas que o atendimento por vendedor. A conclusão qualitativa não mudou.
- Os **valores absolutos** de prospects e receita atribuída **não são comparáveis** com qualquer
  leitura anterior a 08/09.
- O bloco de **perfil não é afetado** — vem da `fct_transactions`, íntegra.

**Pendente (não é análise, é pipeline):** levar à equipe do Zenvia/dados a pergunta de qual carga
está correta. Se a antiga estava inflada, o relatório de 04/09 superestimava o alcance do disparo;
se a nova está incompleta, a série de setembro está subnotificada. Não é decidível com os dados
disponíveis no DW.

## Wiki atualizada

- `wiki-bp/pages/bq-planos.md` — seção da Coleção reescrita: 4 planos + bundles Black, sigla `CBR`,
  checkouts, faixas de preço por canal, assinatura-fantasma.
- `wiki-brasil-paralelo/pages/ultima-cruzada.md` — nova página com os achados de negócio.
- `wiki-bp/pages/metricas-referencia.md` — números de referência do lançamento.
