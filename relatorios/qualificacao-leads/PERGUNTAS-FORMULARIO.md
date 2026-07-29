# Banco de perguntas — formulário de qualificação de leads

Backlog vivo de perguntas candidatas para os formulários de cadastro (survey in-funnel do IQL).
Adicionar candidatas aqui conforme surgirem; promover a "em coleta" quando entrarem num formulário.

**Regras do jogo** (referências: Drive Research, SurveyMonkey WTP, literatura de lead scoring; metodologia IQL D39):

- **Máx. 2 perguntas novas por campanha** — cada pergunta custa conversão do formulário.
- **Sempre fechadas** e com wording neutro (nunca "caro", nunca opção que induza).
- Ciclo de vida: `candidata → em coleta → ativa (IV comprova) → aposentada (IV não comprova)`.
- Operacional: pergunta nova = linhas novas no `seed_iql_de_para`; entra rodando no prior
  (D39) e **o IV decide se fica** — zero mudança de código.
- Governança D20: pesos e IV das respostas **não circulam** para quem opera campanha.

## Já no formulário (não duplicar)

renda · streaming / qtd_streaming / assina_streaming · relacao_bp · tempo_conhece_bp ·
religiao · fonte_confianca · midia_tradicional

## IV medido em não-membro (jul/2026) — a régua real

| Pergunta | IV | Situação |
|---|---|---|
| tempo_conhece_bp | **0,388** | ativa |
| midia_tradicional | **0,328** | **ativa desde a D48** (era coleta, valia zero) |
| relacao_bp | 0,221 | aposentada na D13 — justificativa caiu com a D41 (identity graph removido) |
| renda | 0,164 | ativa; binning viola o piso de 5% (15k+ tem 19 conversões) |
| fonte_confianca | 0,099 | aposentada na D14 alegando IV <0,02 — **não bate com a medição** |
| assina_streaming | 0,098 | ativa; β 0,19 (redundante, não ruim) |
| qtd_streaming | 0,069 | aposentada na D14 |
| religiao | **0,015** | **no formulário sem poder preditivo — candidata a aposentar** |

⚠️ **Cobertura é o gargalo, não o wording:** só EVG (69%), BP10 (71%) e ELB26 (50%) têm pesquisa.
DOM (233k), ELS (218k), BMA (190k), ABC (93k) e as LPs sempre-ativas têm **zero**. ~78% do volume
de 2026 nunca foi perguntado nada — levar a pesquisa atual para lá vale mais que qualquer
pergunta nova.

## Candidatas

### P1 — Intenção (timing) 🥇

> **Você pensa em assinar algum serviço de conteúdo nos próximos meses?**
> 1. Sim, ainda este mês
> 2. Sim, nos próximos 3 meses
> 3. Talvez, mais para frente
> 4. Não penso em assinar

- **Hipótese:** timing é o preditor nº 1 na literatura de lead scoring; o form atual mede afinidade e capacidade, não mede prontidão.
- **Atributo:** `intencao_assinar` (novo). **Status:** candidata — não entrou na ELB26 (form ficou com 4 perguntas); sugerida para a próxima campanha nova.

### P2 — Motivação / JTBD 🥈 — **EM COLETA desde a D48**

> **O que mais te atraiu para se cadastrar?**
> 1. A educação dos meus filhos
> 2. Fé e valores
> 3. História do Brasil
> 4. Política e atualidades
> 5. Os documentários / entretenimento
> 6. O material gratuito

- **Hipótese:** além de IV, vira briefing de criativo por persona. Opção 6 é a "armadilha honesta" — autodeclaração de Curioso Frio.
- **Atributo:** `motivacao`. **Status:** **em coleta** (D48) — 10 linhas no de-para, textos por
  campanha mapeando para níveis canônicos compartilhados (`estudo_profundo` · `atualidade` ·
  `militancia` · `familia_educacao` · `entretenimento` · `lead_frio`).
- **Wording final (copy, 29/jul):** o eixo mudou de "temas que eu gosto" para "o que vou fazer com
  isso" — lista de temas convida resposta identitária (todos gostam de história E política E
  valores) e mata a variância; lista de usos força escolha real. "Fé e valores" foi **cortada** por
  esse motivo (seria a nova `religiao`, IV 0,015). A armadilha honesta virou "Só me interessei por
  esse assunto" — sem a palavra "grátis", que dá vergonha e faz o lead frio mentir. Prova de que
  o mecanismo funciona: na `midia_tradicional`, 7,8% marcaram "Acho que está tudo certo"
  (essencialmente *"não sou seu público"*) e convertem 0,1%.

### P3 — Hábito de consumo

> **Com que frequência você assiste documentários ou conteúdo educativo?**
> 1. Quase todos os dias
> 2. Algumas vezes por semana
> 3. Algumas vezes por mês
> 4. Raramente

- **Hipótese:** proxy declarado de RFV (modelo FT: hábito prediz assinatura). Ponte até termos engajamento pré-cadastro medido (1º refit).
- **Atributo:** `habito_consumo` (novo). **Status:** candidata.

### P4 — Momento de vida (filhos)

> **Você tem filhos em idade escolar?**
> 1. Sim, em escola
> 2. Sim, em educação domiciliar
> 3. Não

- **Hipótese:** ativa a persona Pai/Educador e o cross-sell BP Kids; educação domiciliar é sinal forte de fit com a marca.
- **Atributo:** `filhos_escola` (novo). **Status:** candidata.

### P5 — Atribuição declarada

> **Como você conheceu a Brasil Paralelo?**
> 1. YouTube
> 2. Instagram ou Facebook
> 3. Indicação de amigo ou família
> 4. Influenciador ou podcast
> 5. TV ou rádio
> 6. Não lembro

- **Hipótese:** fecha o gap de atribuição de influenciadores com link genérico (ver `wiki-brasil-paralelo/influenciadores.md`); "indicação" é proxy de advocacy.
- **Atributo:** `origem_declarada` (novo). Nota: útil também fora do IQL (atribuição), mesmo que o IV não comprove.
- **Status:** candidata.

### P6 — Expectativa de preço (WTP)

> **Quanto você esperaria pagar por mês por um serviço como a BP?**
> 1. Até R$ 20
> 2. Entre R$ 20 e R$ 40
> 3. Entre R$ 40 e R$ 60
> 4. Mais de R$ 60
> 5. Não pagaria

- **Hipótese:** WTP declarado complementa renda (capacidade ≠ disposição). Wording de expectativa, não de disposição (menos viés de desejabilidade social).
- **Atributo:** `expectativa_preco` (novo). **Status:** candidata.

## Aposentadas

_(nenhuma ainda — mover para cá quando o IV não comprovar)_

---

Referências completas e racional: `ANALISE.md` (pesquisa de 27/jul/2026) ·
metodologia e registro de decisões: `METODOLOGIA-IQL.md`.
