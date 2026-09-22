# Análise: testes de campanha na JOM (CPL × qualidade × retorno)

**Data:** 21/ago/2026 · **última leitura: 08/set** (aba "Semana") · **Relatório:** [index.html](index.html) (preview: artifact `eb46dd5e`)
**Wiki:** `wiki-brasil-paralelo/campanhas-calendario.md` (JOM) · `wiki-bp/pages/iql.md` · [PROJECAO-RPL.md](../qualificacao-leads/PROJECAO-RPL.md)

---

## Pergunta original

O time vai testar várias estratégias de campanha na JOM e precisa saber **qual vale mais a pena** —
não só qual traz lead mais barato. Inclui comparar campanhas otimizadas pelo IQL/RPL projetado
contra a campanha normal.

Hipótese testável: *dentro da mesma tag e no mesmo período, existe braço com retorno esperado
(RPL esperado ÷ CPL) ≥ 1,5× e significativamente melhor que os demais.*

## Decisões de abordagem

- **Braço de teste = campanha Meta**, não ad set nem criativo. O relatório lê as campanhas da tag
  automaticamente — teste novo aparece sozinho, sem mexer no código.
- **Atribuição lead→braço**: `utm_content` → `id_advertising` → campanha (regex `(\d{10,})$`,
  90,7% de cobertura na JOM). **Exceção**: o form nativo não traz id numérico no `utm_content` —
  ali o braço é a própria tag (`JOM-BR-FORMS`/`JOM-USA-FORMS`).
- **Métrica primária = retorno esperado** (D52), não CPL nem CPLq. Lead barato de mix fraco pode se
  pagar; o retorno decide.
- **Retorno como faixa, não ponto** (decisão metodológica, achados 1 e 1b): *observado* (piso) e
  *teto* (se todos valessem como respondentes). Comparar braços de mesma cobertura pelo piso; entre
  coberturas diferentes, comparar a faixa e preferir quem ganha nos dois extremos.
- Série diária **exclui os braços de form nativo**: a ingestão é em lote e `dt_registered_at_br` é a
  hora do import, não do cadastro — a série seria fictícia.
- Janela de teste começa em **25/07** (a tag JOM é reusada desde out/2025; survey in-funnel só
  desde 28/07).

## Achados principais

**1. A comparação ingênua de qualidade entre braços está errada — e inverte o ranking.**
O IQL usa a pesquisa; braço que pergunta menos tem lead classificado em faixa baixa *por ausência
de sinal*. O form nativo tem 16,2% de cobertura de pesquisa vs 54–58% dos demais:

| Braço (leitura de 23/08 23:55) | CPL | Cob. pesquisa | % A+/A obs. | % A+/A comp. | Retorno obs. | **Retorno comp.** | Receita obs. | Vendas |
|---|---|---|---|---|---|---|---|---|
| Form nativo Meta | **R$ 1,74** | 16,2% | 14,3% | 46,6% | 4,13× | **5,93×** | R$ 239 | 1 |
| [ADVANTAGE] Junho (encerrada) | R$ 2,89 | 54,4% | 31,4% | 45,1% | 3,10× | 3,63× | R$ 4.541 | 22 |
| [ADVANTAGE] Agosto | R$ 3,72 | 58,3% | 27,6% | 40,6% | 2,20× | 2,58× | R$ 4.866 | 30 |
| [ADVANTAGE] Agosto \| ROAS 3 ⚠️ 2 dias | R$ 3,43 | 61,9% | 15,2% | 23,1% | 1,78× | 1,95× | R$ 0 | 0 |
| [ADVANTAGE] Agosto \| Exclusão ⚠️ 2 dias | R$ 4,65 | 53,7% | 17,9% | 27,8% | 1,38× | 1,49× | R$ 0 | 0 |

Entre respondentes, os braços ficam em **41–47% de A+/A** — mesma ordem de grandeza, com o form
nativo no topo (46,6%) sobre uma base pequena (~208 respondentes). O que os separa é o CPL. Na
leitura observada o form nativo é 3º; na comparável, é 1º com folga.

⚠️ **O ranking do form nativo é projeção, não resultado.** Ele tem **1 venda e R$ 239 de receita
observada contra R$ 2.237 de gasto** (ROAS realizado 0,11×) em 7 dias. Junho e Agosto carregam 22 e
30 vendas. O retorno esperado é a métrica de decisão *antes* da receita madura chegar — mas quem
compara os braços precisa ver que só um deles ainda não produziu venda material.

> **Fonte canônica das colunas de qualidade é o `data.json`.** Uma revisão de 24/08 encontrou esta
> tabela e a prosa defasadas em relação ao dado gerado (diziam 14,2% de cobertura, "42–45%" de A+/A
> e percentuais obs. mais altos). Corrigido pelo `data.json` de 23/08 23:55. Ao atualizar, rodar o
> `refresh.py` e reler estes números aqui.

**1b. A taxa de resposta é sinal REAL — mas "recusou" ≠ "não foi perguntado" (medido 24/ago).**
Em receita observada (não circular; não-membros, EVG/BP10 maduras, D+30): **quem responde vale
2,3–2,8× mais** (EVG R$ 3,88 vs 1,41; BP10 R$ 1,81 vs 0,78) e converte 3,5–5,5× mais. Ou seja,
zerar o efeito da pesquisa (minha 1ª versão da métrica "comparável") é **otimista demais**.

Porém o modelo tem 3 níveis (`sim` / `nao` / `pesquisa_indisponivel`) e no form nativo **952 dos
1.079 não-respondentes estão marcados como `nao`** — como se tivessem recusado, quando a campanha
simplesmente não pergunta. Logo:

- **Retorno observado = piso** (trata não-perguntado como recusa → subestima o form nativo)
- **Retorno teto** (todos valeriam como respondentes → superestima)
- **O valor real fica entre os dois.** Form nativo hoje: entre **4,13× e 5,93×**.

Evidência sobre onde no intervalo: comparando só atributos que **não** dependem da pesquisa, o
público do form nativo é levemente pior — base conhecida 9,9% vs 13,5%, recadastro quente 12,8% vs
19,7%. Menos atrito no cadastro = menos filtro de intencionalidade. Então o valor real está no meio
do intervalo, não colado no teto — mas **mesmo no piso o form nativo lidera** (4,13× vs 2,58× do
Advantage Agosto). A decisão de mídia não muda; a precisão do número, sim.

**2. O form nativo é o melhor braço, e melhorou ao escalar** — de 544 para 1.287 leads em 2 dias,
com o **CPL caindo de R$ 2,29 para R$ 1,74** e o retorno comparável subindo de 4,27× para **5,93×**.
Escalar barateou em vez de encarecer: o oposto da saturação. ⚠️ 7 dias — ainda em aprendizado
(regra: só ler como definitivo a partir do 15º dia).

**3. O Advantage Agosto continua abaixo do Junho** (2,58× vs 3,63×) e estável com +750 leads —
não é ruído. Junho encerrou (0 leads novos desde 21/08), então a comparação vira histórica.

**3b. Dois braços novos entraram em 21/08** (`| ROAS 3` e `| Exclusão`), com 2 dias e ~100 leads
cada — ambos **abaixo** do Advantage Agosto puro (1,95× e 1,49×). Leitura ainda sem valor: estão
no primeiro terço da janela de aprendizado, onde o CPL infla por construção. A Exclusão em
particular tem CPL 25% maior, esperado (público menor). Reler em 04/09.

**4. Leads sem atribuição de mídia (1.328, orgânico/CRM) são os melhores da tag**: score +11,5
entre respondentes vs −3,3 do melhor braço pago. Consistente com o histórico (canal próprio ganha
de mídia em qualidade) — e é volume que não custa CPL.

**5. Todos os braços seguem acima da meta de 1,5×** (o pior, Exclusão, está em 1,49× no 2º dia) —
a captação da JOM se paga em qualquer estratégia. A decisão é de otimização, não de continuidade.

**6. Visão LP × Form nativo por mercado — o sinal de receita observada contradiz o de qualidade
esperada.** Agora é a **2ª aba do relatório principal** ([index.html](index.html), artifact
`78e9d296`), no template do briefing (BR e EUA). A página standalone
[lp-vs-form.html](lp-vs-form.html) (preview `78d08587`) segue como legado — mesma fonte
(`lp-vs-form.json`), mesmo render.

**Janela comparável (revisão 25/ago):** o form nativo só começou em **20/08** (verificado nos leads;
antes eu havia anotado "17/08" — errado). Comparar a janela cheia (12–23) enviesava a favor da LP,
cujos leads tinham até 8 dias a mais para abrir e-mail e converter. A query agora **recorta LP e
form ao mesmo período por mercado** (do 1º lead do form até 23/08 = **20–23/08**), inclusive a mídia
BR (BigQuery) e a mídia EUA (CSV, recortado pela mesma `dt_corte`).

| Métrica (BR, 20–23/08) | LP | Form nativo | Leitura |
|---|---|---|---|
| CPL | R$ 2,73 | **R$ 1,44** | form −47% |
| CPM | R$ 35,89 | **R$ 29,21** | form −19% |
| Leads | 2.761 | 1.425 | |
| Abertura de e-mail | **10,1%** | 8,4% | LP engaja mais (gap ↓) |
| Clique no e-mail | **1,1%** | 0,6% | LP ~2× |
| Vendas na janela | **15** | 1 | |
| **Retorno por lead** | **R$ 0,82** | R$ 0,17 | **LP ~5×** |

Casada a janela, o gap de abertura de e-mail encolhe (era 9,4 vs 7,2 na janela cheia; agora 10,1 vs
8,4) — **parte da diferença era idade de coorte, como suspeitávamos** — mas a LP segue à frente em
engajamento e converte muito mais na janela. O form nativo entrega lead mais barato e (entre
respondentes) com nota equivalente, porém **converte bem menos** e engaja menos no e-mail.
**Hipótese consistente com o achado 1b:** menos atrito no cadastro = menos filtro de
intencionalidade. O IQL não captura isso porque a maior parte desses leads não responde a pesquisa.

**EUA (mídia da planilha do time, em dólar, 20–23/08):** LP **CPL US$ 0,60** (155 leads), form
**CPL US$ 0,51** (184 leads) — form ~15% mais barato. **Zero vendas nos dois** — sem base para
conclusão de receita. E-mail nos EUA: LP abre 9,4% / clica 0,7% vs form 9,6% / 0,6% — praticamente
empatados na janela casada.

⚠️ **CTR não é comparável entre os formatos** (BR: LP 8,24% vs form 0,27%): no form nativo o usuário
não sai do Instagram/Facebook, então "outbound click" mede coisas diferentes.

---

## Leitura semanal 01–07/set/2026 (apurada 08/09 às 17h19)

Pedido: gasto, CPL, taxa de resposta, mix de faixas A/B/C/D, RPL e abertura de e-mail por braço.
Virou a **aba "Semana"** do [index.html](index.html) — a janela rola sozinha (últimos 7 dias
completos). Queries: [resumo_semanal.sql](queries/resumo_semanal.sql) e
[ritmo_maturacao.sql](queries/ritmo_maturacao.sql).

🚨 **Correção sobre a 1ª apuração deste mesmo dia (16h16).** O mart de spend do Meta ainda estava
sendo reconstruído: a mesma query devolveu R$ 23.338 de manhã e **R$ 31.238 à tarde (+34%)**. Os
números abaixo são os da tarde, conferidos contra o Gerenciador de Anúncios (`Agosto`: R$ 10.538,25
no Gerenciador × R$ 10.538,76 na query). **O ranking mudou por causa disso** — ver achado 1.

**Formato:** o pedido era comparar *configurações* de campanha em 6 métricas, então o bloco
principal é uma **matriz de comparação** — métricas nas linhas, campanhas nas colunas, melhor e
pior destacados por linha (mesmo padrão da aba LP × Form, já validado com o time). A leitura útil
é horizontal: "quem ganha nesta métrica". Duas regras que a matriz respeita e uma tabela ingênua
quebraria: (1) **volume não tem vencedor** — mais leads não é melhor quando o gasto difere, então
`Valor gasto` e `Leads` não recebem verde/vermelho; (2) **braço sem pesquisa não compete nas
linhas de faixa** — sai como `n/c`, porque 0,0% em D no form nativo é score cego, não mix bom, e
marcá-lo como "melhor" inverteria a conclusão.

⚠️ **A JOM não é só Meta.** Google Ads `[KW]` e PMax `[PMAX]` captam para a mesma tag: R$ 3,7k de
verba e 941 leads/semana que antes caíam no balde "sem atribuição" e eram lidos como orgânico.

| Braço | Gasto | Leads | CPL | Não membros | Tx. resp. | A+/A | RPL obs. | RPL esp. | Retorno esp. | Ritmo | Abertura |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Google PMax [PMAX]** | R$ 1.858 | 810 | R$ 2,29 | 83,7% | 52,7% | 30,7% | R$ 3,60 | R$ 8,71 | **3,80×** | **5,35×** | 7,5% |
| Setembro \| Lead Qualificado Event | R$ 3.340 | 1.137 | **R$ 2,94** | 83,4% | 59,1% | **30,2%** | R$ 1,26 | R$ 8,63 | 2,94× | 2,02× | **8,6%** |
| Form nativo (Meta) ⚠️ | R$ 3.531 | 1.470 | R$ 2,40 | 91,6% | **0,0%** | 8,3% | R$ 0,45 | R$ 6,08 | 2,53× (piso) | 0,88× | 6,0% |
| Agosto (base) | **R$ 10.539** | 2.827 | R$ 3,73 | 87,0% | 60,5% | 27,5% | R$ 0,50 | R$ 8,23 | 2,21× | **0,72×** | 7,9% |
| Agosto \| ROAS 3 | R$ 3.105 | 874 | R$ 3,55 | 89,9% | 57,9% | 24,4% | R$ 1,01 | R$ 7,75 | 2,18× | 1,47× | 7,0% |
| Agosto \| Em breve | R$ 3.532 | 952 | R$ 3,71 | 87,5% | 58,7% | 24,7% | R$ 1,05 | R$ 7,80 | 2,10× | 1,90× | 7,1% |
| Agosto \| Exclusão Insider | R$ 3.510 | 927 | R$ 3,79 | **97,4%** | 60,7% | 9,9% | R$ 0,28 | R$ 5,57 | **1,47×** | **0,58×** | 6,9% |
| Google Ads [KW] | R$ 1.823 | 131 | R$ 13,92 | **71,0%** | **70,2%** | 42,7% | **R$ 37,64** | R$ 10,50 | 0,75× | **45,12×** | **16,2%** |
| Sem atribuição (orgânico/CRM) | — | 366 | — | 71,0% | 73,2% | **56,3%** | R$ 8,13 | R$ 12,45 | — | 9,52× | 15,8% |

Total pago: **R$ 31.238** · 9.128 leads de mídia · CPL blendado **R$ 3,42** · 9.494 leads na tag (BR).

⚠️ O CPL aqui é sistematicamente **maior** que o do Gerenciador (Meta reporta 3.358 leads em `Agosto`,
o warehouse atribui 2.827): o Meta conta o evento dele, aqui conta-se o lead com atribuição por
`utm_content`. Comparar CPL-daqui com CPL-daqui.

### Ritmo de maturação — a métrica que faltava

O erro de leitura mais fácil desta análise é comparar o **RPL esperado (que vale para D+240)** com a
**receita já atribuída (leads de 1 a 7 dias)**: o realizado sai ~12× menor por construção e todo
braço parece um desastre. A 1ª versão do relatório fazia exatamente isso.

O denominador honesto é o esperado **para a idade que o lead tem hoje**. Curva medida na mediana de
24 campanhas maduras (≥15k leads, 240d de vida): D+0 2,5% · D+3 7,6% · **D+7 12,2%** · D+14 19,4% ·
D+30 28,8% da receita de D+240. Com idade média de 3,8 dias, os leads da semana só deveriam ter
entregue **8,1%** do RPL esperado.

**Índice de ritmo = RPL observado ÷ RPL esperado para a idade.** No agregado da mídia paga: **2,40×**
— ou seja, a captação está **acima** do ritmo histórico, não abaixo.
⚠️ A JOM ainda não abriu venda e a curva mediana inclui campanhas que já vendiam desde o dia 0 —
o índice serve para **comparar braços entre si**, não para julgar o nível absoluto.

**Achados**

1. **O PMax é o melhor braço da semana — e estava invisível até hoje.** Melhor retorno esperado
   (3,80×), 2º melhor CPL (R$ 2,29), melhor mix entre respondentes (50,1% A+/A) e ritmo 5,35×.
   ⚠️ Na apuração incompleta da manhã quem liderava era o `Setembro | Lead Qualificado` (com CPL
   R$ 2,02, que era irreal); com o spend completo ele cai para 2,94×. **Foi a correção de spend
   que mudou o ranking** — motivo de sobra para conferir contra o Gerenciador antes de publicar.

2. **O `Setembro | Lead Qualificado Event` continua sendo o melhor braço DE META**, e por margem
   real: CPL R$ 2,94 contra R$ 3,55–3,79 dos outros braços de LP (−17 a −22%), melhor mix
   (30,2% A+/A observado, 40,2% entre respondentes), melhor abertura de e-mail (8,6%) e o melhor
   ritmo entre os braços de Meta (2,02×). ⚠️ 7 dias — janela de aprendizado; reler a partir de ~15/09.

3. 🚨 **O braço que leva mais verba é o que está mais atrasado.** `Agosto` concentra R$ 10.539
   (34% do investimento) e está em **0,72× do ritmo** — abaixo do esperado para a idade dos leads,
   e o pior de todos os braços de Meta depois da Exclusão. Não é imaturidade (o índice já desconta
   isso): é o braço rendendo menos que os irmãos no mesmo período e com a mesma oferta. Vale
   investigar antes de renovar a verba dele.

4. 🚨 **O form nativo parou de coletar pesquisa em 28/08 — quando a campanha virou `Agosto v2`**
   (resposta cai de 22–77/dia para 0 e não volta em 11 dias). 91,6% dos leads em faixa C, **zero em
   B e zero em D** — assinatura de score sem pesquisa, não de público ruim. Sem leitura comparável
   possível (0 respondentes): o retorno de 2,53× é piso. Verificar o formulário do v2 no Gerenciador.

5. **O braço de busca inverte a ordem e o IQL não o enxerga.** Retorno esperado 0,75× (o pior de
   todos) e **ritmo 45×**: R$ 4.930 de receita sobre R$ 1.823 em 7 dias, 18 vendas em 131 leads
   (13,7% de conversão contra 0,3–0,9% do Meta). O scorecard não tem atributo de intenção de busca.
   ⚠️ 11 das 18 vendas vêm do canal "Pesquisas de marca" — é keyword de marca, então parte dessa
   receita aconteceria sem o anúncio; incrementalidade só com holdout geográfico. E uma venda de
   Vitalício de R$ 1.668 é 34% da receita.

6. **`Exclusão Insider` é o pior braço em tudo** — pior CPL (R$ 3,79), pior mix (9,9% A+/A, 31,7%
   em D), pior retorno (1,47×, abaixo da meta de 1,5×) e pior ritmo (0,58×). Coerente com o
   histórico: excluir a base conhecida tira justamente quem converte.

7. **A taxa de não membros ordena o RPL quase perfeitamente — e explica os extremos.** Quanto
   menos base conhecida o braço traz, menos ele rende: `Exclusão Insider` tem **97,4% de não
   membros** (é o desenho dela) e o pior RPL (R$ 0,28); no outro extremo, Google [KW] e o orgânico
   têm **71,0%** e RPL de R$ 37,64 e R$ 8,13. A base conhecida vale ~11× por lead (D28), então
   **o % de não membros funciona como leitura rápida de quanto do retorno vem de recompra e
   quanto vem de aquisição real** — e é o que sustenta a regra de que excluir a base é a pior
   estratégia. ⚠️ O contrário também vale: braço com pouco não membro entrega receita fácil que o
   CRM traria de graça — por isso o CAPI só manda não membro para a Meta.

8. **Taxa de resposta homogênea entre os braços de Meta (57,9–60,7%)** — nenhum desenho moveu esse
   ponteiro. Quem foge é Google KW para cima (70,2%) e PMax para baixo (52,7%).

**Fora do recorte (e por quê)**

| Item | Volume | Por que ficou fora |
|---|---|---|
| Mercado EUA (`JOM-USA`, `JOM-USA-FORMS`) | 798 leads | A conta `[BIG]` não está no warehouse — sem spend, não há CPL |
| `[BNO25] [JOM] [VENDA] Promoção \| ADV` | 2 vendas / R$ 419 | Campanha de **venda**, não de captação; spend zerado na janela |
| `[JOM-FORM] Agosto` (v1) | R$ 0 | Encerrada em 27/08, substituída pelo v2 |


## Pendências / próximos passos

- **Braço otimizado por IQL depende da ponte CAPI** (decidido: priorizar). Sequência: MR do A1
  (dataset dedicado) → token no Business Manager → ponte em dry-run → teste → ligar. O braço entra
  no relatório sozinho quando a campanha começar a gastar.
- **Levar as perguntas de qualificação para o form nativo** (a Meta suporta perguntas customizadas):
  resolveria o intervalo piso–teto E testaria a hipótese da intencionalidade — se com pesquisa o
  form nativo mantiver a nota alta mas seguir convertendo 10× menos, o problema é o público, não a
  medição. Maior alavanca imediata da JOM.
- **Mídia dos EUA fora do warehouse** (conta `[BIG]`, 0 linhas no BQ). Solução atual: `midia_eua.csv`
  na pasta do relatório, exportado da planilha **"[NOVO] Meta Ads - Big Picture"** (Drive) — o
  `refresh.py` lê e mescla. **Atualizar o CSV quando a planilha mudar** (as métricas de BQ atualizam
  sozinhas, essa não). Solução definitiva: trazer a conta dos EUA para o pipeline do Meta, na mesma
  esteira da conta BR — aí o CSV pode ser aposentado.
- **Taxa de conversão da etapa** (LP visita→lead / form abertura→envio) não existe no BQ: LP exige
  GA4 (domínios distintos por mercado), form exige métricas de formulário do Meta.
- Reler quando o form nativo passar de 14 dias (~31/08) e quando houver vendas nele.
- ✅ Braços ROAS 3 e Exclusão relidos em 08/09 (ver leitura semanal): ROAS 3 empata com o base, Exclusão é o pior.
- 🚨 **Form nativo sem pesquisa desde 28/08** (troca para `Agosto v2`) — checar o formulário no Gerenciador antes de qualquer leitura de qualidade desse braço.
- Reler o braço `Setembro | Lead Qualificado Event` a partir de ~15/09 (sai do aprendizado).
- ✅ **Google Ads [KW] e PMax entraram como braços do relatório** (08/09): `resumo_bracos.sql`, `mix_faixas.sql`, `serie_diaria.sql` e `resumo_semanal.sql` agora unem as três tabelas de funil e atribuem por `utm_source`. Regra documentada em `queries/_atribuicao.md`.
- **Mercado EUA continua fora do relatório principal** — a conta `[BIG]` não está no warehouse, então `JOM-USA`/`JOM-USA-FORMS` (798 leads na semana) ficariam com CPL vazio. Só entra por CSV manual, como já é feito na aba LP × Form.
- **Investigar o braço `Agosto`**: 34% da verba e 0,72× do ritmo, o pior de Meta depois da Exclusão. Descobrir se é criativo, público ou saturação antes de renovar verba.
- **Carimbar a hora da apuração** em toda leitura de spend, e conferir o total contra o Gerenciador — o mart do Meta subiu 34% entre 16h e 17h do mesmo dia (ver correção acima).
- **Incrementalidade do braço de busca de marca** não está medida (11 das 18 vendas vêm de "Pesquisas de marca") — exige holdout geográfico antes de escalar por causa do ROAS observado.
- Se o time criar braços com nomenclatura fora do padrão `[LAN] [JOM] [LEAD] …`, o rótulo do braço
  sai feio — vale manter a convenção.

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/resumo_bracos.sql](queries/resumo_bracos.sql) | Resumo por braço: leads, spend, CPL, qualidade obs./comp., retorno obs./comp., receita |
| [queries/serie_diaria.sql](queries/serie_diaria.sql) | Série diária por braço (exclui form nativo — ingestão em lote) |
| [queries/mix_faixas.sql](queries/mix_faixas.sql) | Mix de faixas IQL por braço |
| [queries/resumo_semanal.sql](queries/resumo_semanal.sql) | **Resumo por braço em janela parametrizada** (gasto, CPL, taxa de resposta, mix A/B/C/D, RPL obs./esp., abertura e clique de e-mail) — alimenta a aba "Semana"; o `refresh.py` reescreve os `DECLARE` de data para os últimos 7 dias completos |
| [queries/ritmo_maturacao.sql](queries/ritmo_maturacao.sql) | **Índice de ritmo**: mede a curva de maturação nas campanhas maduras e compara o realizado de cada braço com o esperado PARA A IDADE do lead |
| [queries/_atribuicao.md](queries/_atribuicao.md) | **Como o lead é ligado ao braço** nas três contas de mídia (Meta por id de anúncio, Google e PMax por `utm_source`) |
| [queries/lp_vs_form_mercado.sql](queries/lp_vs_form_mercado.sql) | Matriz LP × form × mercado (mídia, leads, e-mail, receita) — alimenta o `lp-vs-form.html` |

Atualizar o relatório: `python3 refresh.py` — usa o **`bqq`** (`~/meu_projeto/BigQuery/bqq`), o
cliente padrão do projeto: ADC renova sozinha, enquanto a credencial do `bq` CLI expira quase todo
dia e não reautentica em sessão não-interativa (ver `wiki-bp/pages/bq-acesso.md`).

## Wiki atualizada

- `campanhas-calendario.md` (JOM): números do teste form nativo vs padrão já registrados em 21/08;
  esta análise confirma com a leitura comparável.
- `iql.md`: o viés de cobertura de pesquisa na comparação entre braços (achado 1) vale para
  qualquer comparação de qualidade — registrado como regra.

## Para retomar

**Próximo passo:** ponte CAPI (A1 → token → dry-run) para destravar o braço IQL; em paralelo,
propor as perguntas de qualificação dentro do form nativo.
**Wiki a carregar:** `iql.md` → `campanhas-calendario.md` (JOM) → esta análise.
**Estado das queries:** ✅ as três rodam e alimentam o `data.json`.
