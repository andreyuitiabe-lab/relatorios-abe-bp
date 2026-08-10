# Formulário conversacional Mecenas ("form ref viver de ia")

**Data:** 2026-08-10 · **Analista:** André Abe
**Fonte:** planilha `[MEC] Form ref viver de ia`, aba `funil-k` (owner: barbara.olivieri) — [link](https://docs.google.com/spreadsheets/d/1IqyKryJuiGB26FmIzBNS07hTtG7pGPSAJWG7iSMlBaw/edit?gid=1859290510)
**Teste:** `mec_form_viverdeia_08ago`, variante `K`, LP `vd.brasilparalelo.com.br/seja-membro/mecenas-2026`

## Pergunta original

Um fluxo em que a pessoa conversa com um chat de IA antes de doar. Analisar as respostas e ver se sai insight — cruzando com vendas por e-mail ou telefone.

## ⚠️ Tamanho da amostra: o limite desta análise

**80 leads reais em ~25 horas** (08/08 16h43 → 09/08 17h57), com **10 conversões**. Testei todas as comparações de resposta com Fisher exato:

| Comparação | Resultado | p | Veredito |
|---|---|---|---|
| Faixa declarada baixa vs alta | 29% vs 0% | 0,079 | limítrofe |
| "Contribuir agora" vs "não tenho certeza" | 33% vs 0% | 0,135 | limítrofe |
| Tirou dúvida e resolveu vs pediu WhatsApp | 60% vs 12% | 0,217 | ruído |
| Clicou R$1–2/dia vs R$3/dia | 46% vs 0% | 0,250 | ruído |
| Já era cliente vs não era | 16% vs 4% | 0,267 | ruído |

**Nenhuma resposta do funil discrimina conversão com significância.** O que vale como achado são as **contagens diretas** (funil, checkout, match com a base), que não dependem de teste. As comparações ficam como **hipóteses a monitorar** quando o volume crescer — a direção de duas delas é forte o suficiente para valer o acompanhamento.

## Achados

### 1. O checkout perde metade de quem decide pagar — este é o achado

Das 22 tentativas de pagamento depois do formulário:

| Status | Tentativas |
|---|---|
| `approved` | **11** |
| `abandoned` | 6 |
| `canceled` | 4 |
| `waiting_payment` | 1 |

**50% de perda depois de a pessoa clicar no plano.** Todas em Mecenas Solidário (R$ 359 / 719 / 1.079). Oito pessoas passaram pelo funil inteiro, responderam tudo, escolheram o valor — e não fecharam. Isso não é problema de qualificação nem de mensagem: é atrito de pagamento, e é a maior alavanca disponível aqui.

Receita gerada no período: **R$ 5.865** (9 doações Mecenas + 1 outra compra).

### 2. O funil sangra em dois pontos específicos

| Etapa | Chegam | % do total | % da etapa anterior |
|---|---|---|---|
| Nome/contato | 80 | 100% | — |
| Cenário | 54 | 67,5% | **67,5%** ← 1ª queda |
| Formação | 54 | 67,5% | 100% |
| Faixa de valor | 47 | 58,8% | 87% |
| Continuar? | 42 | 52,5% | 89% |
| Dúvida | 19 | 23,8% | **45%** ← 2ª queda |
| Resolveu? | 13 | 16,2% | 68% |

- **A primeira pergunta derruba um terço.** Um em cada três abandona entre dar o contato e responder o cenário. Nenhuma pergunta seguinte perde tanto (87–100% de passagem). Se há um lugar para mexer, é a transição do contato para a primeira pergunta.
- **A trilha de dúvidas perde 55%.** Dos 42 que chegam ao "continuar?", 20 pediram para tirar dúvida antes — mas só 19 registraram dúvida e 13 responderam se resolveu.
- Onde as pessoas param (`etapa_atual`): `continuar` 19 · `resolveu` 13 · `email` 12 · `whatsapp` 7 · `formacao` 7 · `nome` 7.

### 3. O formulário está falando com a base, não captando público novo

- **64 dos 80 leads (80%) foram encontrados na base** por e-mail ou telefone.
- **57 (71%) já eram clientes** — tinham compra aprovada antes do formulário.
- Só **23 não eram clientes**, e desses **1 converteu**.
- Quem converteu tinha gasto prévio mediano de **R$ 1.420**, contra R$ 470 de quem não converteu.

Isso é coerente com o que a análise de perfil do Mecenas já mostrou: comportamento de compra prévio domina. O formulário é ferramenta de **monetização de base**, não de aquisição — e deve ser avaliado por essa régua.

### 4. Como as pessoas respondem (contagem, sem inferência)

**Cenário** (n=54) — a formulação vencedora é a do meio, não a extrema:
- 63,0% "Acredito que precisamos fazer alguma coisa, mas é difícil saber por onde começar"
- 20,4% "Não sei exatamente o que pensar. Só sei que é triste ver a educação nesse estado"
- 16,7% "Acho que essa é uma responsabilidade do Estado"

**Importância da formação** (n=54): 70,4% "Muito. A formação é decisiva" · 29,6% "Bastante, embora existam outros fatores". Praticamente ninguém discorda da premissa — **a pergunta não separa nada** e é candidata a sair do fluxo.

**Faixa de contribuição** (n=47): 59,6% "Até R$ 49/mês" · 21,3% "Quero conhecer formas de financiar ainda mais" · 14,9% "R$ 50–99" · 4,3% "R$ 100–500".

**Dúvidas** (n=19), em ordem: "Para onde vai exatamente o meu dinheiro?" (6) · "Quem recebe a bolsa e como é escolhida?" (4) · "Por quanto tempo fico com esse compromisso?" (4) · "Como acompanho o bolsista?" (3). **As quatro são sobre prestação de contas e compromisso, não sobre o produto.**

**Plano clicado** (n=16): R$1/dia 56% · R$2/dia 25% · R$3/dia 19%.

**Dispositivo:** 98,8% mobile. **Origem:** facebook 68% · pmax 23% · insider 5%.

### 5. Hipótese que vale monitorar: declarar valor alto não prediz pagar

| Faixa declarada | Leads | Converteram |
|---|---|---|
| Até R$ 49/mês | 28 | **8 (29%)** |
| De R$ 50 a R$ 99 | 7 | 1 (14%) |
| De R$ 100 a R$ 500 | 2 | 0 |
| "Quero conhecer formas de financiar ainda mais" | 10 | **0** |

E no plano efetivamente clicado: R$1–2/dia converteu 6 de 13; **R$3/dia converteu 0 de 3, com os 3 abandonando o checkout**.

A direção é a mesma nos dois cortes e ecoa o achado da análise de perfil (comportamento > declaração), mas **p=0,079 com n=12 no braço alto — é hipótese, não conclusão**. Se confirmar, tem consequência prática: a resposta "quero financiar ainda mais" hoje parece sinal de engajamento e pode ser sinal de fantasia. Vale marcar esses leads para o Comercial em vez de tratá-los como compra iminente.

## Recomendações

1. **Investigar os 11 pagamentos não concluídos** — é o único achado robusto e o de maior retorno. Ver se é meio de pagamento, valor, exigência de dados ou erro técnico. 8 dessas pessoas responderam o funil inteiro.
2. **Reduzir o atrito da primeira pergunta** — um terço abandona ali, mais que em qualquer outra etapa.
3. **Cortar ou reformular a pergunta de formação** — 70/30 numa premissa que ninguém contesta não gera informação.
4. **Usar as 4 dúvidas como pauta de conteúdo**: destino do dinheiro, escolha do bolsista, duração do compromisso, acompanhamento. São objeções de confiança, e o material da campanha deveria respondê-las antes de a pessoa precisar perguntar.
5. **Acompanhar a hipótese da faixa declarada** com mais volume antes de agir.
6. **Não avaliar este funil como aquisição** — 71% já eram clientes.

## Pendências

- [ ] Refazer com 2–3 semanas de dados: com ~10 conversões nada sobre as respostas é conclusivo.
- [ ] Ver se os 8 que abandonaram foram abordados pelo Comercial (cruzar com Zenvia/Pipedrive).
- [ ] Confirmar se quem pediu WhatsApp (12 leads) foi efetivamente atendido — 3 compraram.
- [ ] A planilha tem outra aba (`Página1`) que não foi analisada.

## Queries

| Arquivo | O que faz |
|---|---|
| [01_match_leads_por_email_e_telefone.sql](queries/01_match_leads_por_email_e_telefone.sql) | Casa os leads da planilha com contas do gateway por e-mail e telefone, com os filtros de telefone-lixo |

⚠️ **Nada de PII neste diretório** — a planilha tem nome, e-mail e telefone; o cruzamento foi feito localmente e a query salva usa parâmetros em vez dos literais.

## Nota de método: o telefone fake que quase estragou a análise

Um lead informou **(11) 99999-9999**, que casa com **1.234 contas** na base. Sem filtro, o match saltou de 90 para 1.324 contas e teria inflado toda a análise. A correção usa as mesmas duas regras do identity graph: descartar número com dígito repetido 6+ vezes e descartar telefone com ≥10 e-mails distintos. O match de telefone também compara **DDD + 8 últimos dígitos**, para o nono dígito não gerar falso negativo.

Ganho real do telefone: **12 contas** que o e-mail sozinho não encontraria.
