# Coleção Brasil: A Última Cruzada — perfil do comprador e abordagem do Comercial

**Data da análise:** 04/09/2026 · **Janela:** 01–04/09/2026 (4 dias de venda; lançamento 01/09)

> Os números abaixo são o fechamento de 04/09 16h. **A versão viva é o relatório HTML** — `python refresh.py`
> regera `data.json` e a página inteira a partir das queries de `queries/`.

## Pergunta original

Quem está comprando a Coleção Brasil: A Última Cruzada — membros ou não? Qual o perfil
(renda, cartão, consumo, engajamento, tempo de casa)? E como o Comercial está abordando?

## Decisões de abordagem

- **Universo**: `nm_gateway_plan LIKE 'colecao-brasil%'` **OU** produto contendo "Coleção Brasil".
  A wiki documentava só 2 planos; existem **4** (`-fisico`, `-completo`, `-completo-cursos`,
  `-digital`) + bundles em `nm_gateway_plan = 'black'` (`Última Cruzada + Black Vitalício/Anual`).
  Filtrar só pelos 2 documentados perderia 30% das vendas.
- **Chave de pessoa**: e-mail normalizado (cobre multi-conta). 364 compradores aprovados no fechamento.
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
- Benchmark de renda/cartão calculado sobre os 603k membros ativos, para não ler nível de cartão
  em absoluto (gotcha de `bq-acesso.md`: Black+ sozinho não é sinal de elite).

## Achados principais

### Resultado em 4 dias
- **364 compradores / R$ 352.403**. Ramp: 3 (01/09) → 85 → 176 → 100 (04/09, dia parcial).
- **Comercial = 243 compradores (66,8%) / R$ 227k**; Digital = 121 / R$ 125k.
- Mix: Físico 249 (ticket R$ 873), Completo 109 (R$ 1.142), Digital 4 (R$ 358), Bundle Black 2 (R$ 4.415).
- **Recusa/abandono relevante**: 92 pessoas com transação `canceled/abandoned` (139 tentativas) — ~25% do volume aprovado. Erros: limite insuficiente, cartão vencido/bloqueado, transação não permitida.

### É venda para a base — e para a nata dela
- **96,4% já eram clientes.** Só **13 compradores** fizeram a 1ª compra na BP.
- **76,4% são membros ativos hoje**; **70,3% são vitalícios**; **21,4% são/foram Mecenas**.
- **55,8% já compraram o Clube do Livro**; 20,6% compraram a Odisseia; 14,8% têm certificação.
- **LTV anterior mediano R$ 5.508** (média R$ 8,2k). 66,1% já gastaram R$ 4 mil+ antes da coleção.
- **Tempo de casa: 50% tem 4+ anos**; mediana ~4 anos. Só 14% entrou há menos de 1 ano.
- **Penetração ainda baixa: 0,82% dos 24,9k compradores do CDL** compraram a coleção → o público
  natural está longe de saturado.

### Perfil socioeconômico (acima da base, com folga)
| Indicador | Compradores UC | Base membros ativos | Lift |
|---|---:|---:|---:|
| Cartão premium (Black/Amex/Platinum) | 84,9% | 57,2% | **1,5×** |
| Cartão nível Black | 63,0% | 30,5% | **2,1×** |
| Renda (decil 8–10 do CEP) | 61,0% | 31,7% | **1,9×** |

- Gênero inferido: 73% masculino.
- Idade (dado em 238 de 364): **64% tem 45 anos ou mais**.
- Geografia: SP 30%, RJ 12%, RS 10%, PR 7%, MG 7%, DF 6%.
- Pagamento: 86% cartão (12x é o padrão de todas as ofertas), 12% Pix.

### Engajamento: compra sem consumo
- **43,1% dos compradores não teve nenhuma sessão na plataforma nos últimos 90 dias.**
  Só 15% são usuários de alto engajamento (11+ dias ativos em 90d).
- O produto físico vende para quem **tem vínculo mas não consome** — colecionador, não espectador.
- O Comercial converte melhor exatamente na faixa engajada leve/média (73–74% das vendas dessas
  faixas são comerciais) e pior nos totalmente inativos (57%).

### Abordagem do Comercial: o disparo frio não abre conversa
**11.651 prospects abordados** desde o lançamento. Os três grupos são mutuamente exclusivos.

| Tipo de abordagem | Prospects | Respondeu | Comprou | Conversão | Receita | Abertura scriptada |
|---|---:|---:|---:|---:|---:|---:|
| Disparo em massa (só a peça) | 5.433 | **0,18%** | 3 | **0,055%** | R$ 3.105 | 98% |
| Disparo + atendimento de vendedor | 384 | 77,6% | 19 | 4,948% | R$ 15.632 | 98% |
| Abordagem do vendedor (sem disparo) | 5.834 | **21,73%** | 194 | **3,325%** | R$ 185.333 | 76% |

- **A peça de disparo, sozinha, é quase inerte**: 5.433 prospects, 0,18% de
  resposta, 3 vendas, R$ 3.105. Dos 10 que responderam só ao disparo,
  **nenhum comprou**. Quem foi atendido por vendedor converte 60× mais.
- ⚠️ **O disparo não aquece — ele seleciona.** Controlando pela etapa `carteiraMecenas`
  (8.056 dos 11.651 prospects):
  disparo puro 0,06% · disparo + atendimento 5,49% · vendedor sem disparo **5,69%**.
  Quem recebeu a peça antes de falar com o vendedor converteu **menos** que quem nunca recebeu — a
  leitura de "aquecimento" (que estava na 1ª versão desta análise) não se sustenta.
- ⚠️ **O mecanismo da diferença não foi testado.** 76% das "abordagens de vendedor"
  abrem com um texto repetido em 20+ conversas — **os dois lados são disparo scriptado**. A diferença
  de 0,18% para 21,73% na resposta é real e grande, mas não é
  personalização. Candidatos não separados por estes dados: remetente (número do vendedor × blast),
  formato da peça (texto curto × peça longa com imagem) e qualidade da lista.
- A etapa `carteiraMecenas` concentra a operação: 8.056 prospects, 197 vendas
  (2,45%). `linkEnviado` converte 15,31%; `tentativa1/2` e `contatoNegociacao` ficam
  abaixo de 0,2%.
- Vendas pulverizadas entre **28 vendedores** (líder com 18) — operação de carteira.

### Dentro das conversas: o que o cliente escreve
Base: **1.661 prospects que responderam algo** (5.359 mensagens), dos quais
12,8% compraram.

- **45,2% nunca escreveram nada** — só clicaram no botão do WhatsApp ou
  mandaram "sim/ok" (750 pessoas, 7,7% de conversão).
  Cliques em botão + respostas mínimas são 25,7% de todos os turnos do cliente.
- **Conversão escala com a profundidade**: só clique 7,7% → 1 fala 10,1%
  → 2–3 falas 14,9% → **4+ falas 35,9%**.
  ⚠️ Parte é causalidade reversa: frete/endereço (40,2%) e
  "paguei" (81,2%) são temas **pós-decisão** — logística de fechamento, não persuasão.

**Temas (base = quem escreveu ao menos uma fala, 17,0% de conversão):**

| Tema | Prospects | Conversão | |
|---|---:|---:|---|
| Preço / quanto custa | 386 | **14,2%** | abaixo da média |
| Membro / minha assinatura | 218 | 22,9% | |
| Não quer / não agora | 217 | 9,7% | |
| O que é / conteúdo | 180 | 27,2% | pergunta qualificada |
| Parcelamento | 130 | 33,8% | |
| Frete / entrega | 87 | 40,2% | pós-decisão |
| Já tem CDL / Odisseia | 45 | 42,2% | |

- ⚠️ **"Quanto custa" é o tema mais comum e converte ABAIXO da média.** A peça de disparo não traz
  preço, então boa parte da conversa nasce e morre nisso. Pergunta sobre o produto em si converte
  quase o dobro.

**O achado acionável — pedir desconto não é objeção, é sinal de compra:**

| Sinal na fala | Prospects | Conversão |
|---|---:|---:|
| ✅ Pediu desconto ou condição melhor | 59 | **32,2%** |
| ✅ Citou ser cliente fiel (vitalício / CDL / Odisseia) | 45 | **42,2%** |
| ❌ Declarou restrição financeira | 51 | 7,8% |
| ❌ Achou caro (juízo de valor) | 28 | 10,7% |
| ❌ Clicou por engano / só curiosidade | 19 | 5,3% |
| ❌ Ainda pagando o vitalício | 9 | 0,0% |

Contra 12,8% da base. **São dois clientes diferentes na mesma frase sobre dinheiro** —
quem negocia e quem não tem — e o roteiro não os separa.

**Fricções operacionais expostas pelas conversas** (volumes pequenos, todos evitáveis):

| Fricção | Prospects | Conversão |
|---|---:|---:|
| Pediu condição citando fidelidade | 75 | 18,7% |
| Travou no campo de cupom do checkout | 14 | 57,1% |
| Esperando entrega de CDL / Odisseia | 14 | 35,7% |
| Confundiu com a série de 2018 ou com o CDL | 3 | 0,0% |
| Não sabe onde acessar o que comprou | 3 | 66,7% |

- **Campo de cupom sem código**: o checkout exibe campo de cupom, o cliente para e pergunta qual é.
  Fricção no último passo — dos 14 que travaram, 8 compraram.
- **14 pessoas em abordagem estão esperando um produto físico anterior** (CDL ou Odisseia
  não entregue). Vender outro físico a quem espera o primeiro é risco reputacional evitável com um
  cruzamento de lista.
- **Como o vendedor responde ao pedido de desconto** (57 conversas):
  vai verificar / consegue 12 · passa um cupom 5 · nega — preço fechado 5 · cita a fidelidade do cliente 5. **Não há política visível** —
  cada vendedor decide na hora, exatamente no momento em que o cliente mais fiel pede reconhecimento.
- O nome reaproveita a **série "A Última Cruzada" de 2018–2019** (~13k transações na `fct_transactions`),
  e aparecem clientes perguntando se é o mesmo material ou como difere do Clube do Livro.

⚠️ **Privacidade**: as transcrições contêm nome e às vezes telefone. **Nenhuma citação literal foi
publicada** — o repo é público e são conversas privadas. A query fica versionada, o texto não;
o `data.json` recebe apenas contagens.

### Atribuição: o Comercial trabalha a nata, o digital alcança o resto
⚠️ "Abordado" aqui exige abordagem **antes** da compra. **14 compradores foram
abordados só depois de já ter comprado** — o Comercial correndo atrás da lista, não aquecendo. Sem
essa guarda o grupo "abordado → digital" dobra de tamanho e a tese de crédito ambíguo fica inflada.

| Origem | n | Ticket | Membro | Vitalício | LTV mediana |
|---|---:|---:|---:|---:|---:|
| Abordado → venda Comercial | 202 | R$ 934 | 84% | 82% | R$ 6.409 |
| Abordado → venda Digital | 14 | R$ 1.098 | 71% | 71% | R$ 6.543 |
| Comercial sem abordagem prévia | 41 | R$ 936 | 88% | 80% | R$ 6.164 |
| **Digital sem abordagem prévia** | **107** | R$ 1.027 | **58%** | **45%** | **R$ 3.576** |

- **59% dos compradores foram abordados antes de comprar.**
- Crédito ambíguo existe, mas é pequeno: **14 vendas (R$ 15.375)**
  fecharam no digital com abordagem prévia.
- O grupo grande é outro: **107 pessoas (29,4%) compraram no digital sem
  nenhuma abordagem**, com perfil bem mais fraco (45% de vitalícios contra
  82%, LTV mediano
  44% menor).
  O digital alcança quem a carteira não cobre.

### Preço: o Comercial vende mais barato que o site
Mesma coleção, ofertas diferentes por canal:
- **Físico**: Comercial ticket médio **R$ 848** vs Digital
  **R$ 976**. A oferta de R$ 719 (12×59,90) é quase exclusiva do
  Comercial: 100 compradores contra 7 no digital.
- **Completo**: Comercial R$ 1.099 vs Digital R$ 1.217.
- Há **5 faixas de preço simultâneas** na versão física (R$ 719 / R$ 948 / R$ 959 / R$ 1.068 / R$ 1.199) — teste de preço ou
  desconto discricionário do vendedor. Vale confirmar com o time se é intencional.

## Pendências / próximos passos

- [ ] Confirmar com o Comercial se a política de preço múltipla (R$ 719 vs R$ 1.199) é teste
      controlado ou desconto livre do vendedor.
- [ ] Pedir criação de **etiqueta/etapa própria do CBR no Zenvia** — hoje a medição depende de
      regex no texto da conversa, o que não escala e não entra em dashboard.
- [ ] Revisitar em ~15 dias: a janela de 4 dias não permite medir maturação, churn de parcelamento
      nem o efeito do disparo em massa com defasagem.
- [ ] Trocar o **formato** da peça de disparo, não o volume: 0,18% de resposta em
      5.433 disparos rendeu R$ 3.105. Testar mensagem curta com pergunta, saindo do
      número do vendedor.
- [ ] **Testar o mecanismo** (o dado atual não separa): rodar A/B de remetente (blast × número do
      vendedor) e de formato (peça longa com imagem × texto curto) na mesma lista. Sem isso, não se
      sabe por que a resposta salta de 0,18% para 21,73%.
- [ ] **Higiene da lista de abordagem**: 14 pessoas foram abordadas depois de
      já ter comprado. É o mesmo problema de higiene já documentado na base da Lambda
      (`fluxo-comercial.md`).
- [ ] Lista de reabordagem: 92 pessoas com transação recusada (limite/cartão) não parecem estar
      em fluxo de recuperação — perfil idêntico ao de quem comprou.

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

## Wiki atualizada

- `wiki-bp/pages/bq-planos.md` — seção da Coleção reescrita: 4 planos + bundles Black, sigla `CBR`,
  checkouts, faixas de preço por canal, assinatura-fantasma.
- `wiki-brasil-paralelo/pages/ultima-cruzada.md` — nova página com os achados de negócio.
- `wiki-bp/pages/metricas-referencia.md` — números de referência do lançamento.
