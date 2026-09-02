# Análise: testes de campanha na JOM (CPL × qualidade × retorno)

**Data:** 21/ago/2026 · **última leitura: 23/ago** · **Relatório:** [index.html](index.html) (preview: artifact `78e9d296`)
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
- Reler os braços ROAS 3 e Exclusão em ~04/09 (saem do aprendizado).
- Se o time criar braços com nomenclatura fora do padrão `[LAN] [JOM] [LEAD] …`, o rótulo do braço
  sai feio — vale manter a convenção.

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/resumo_bracos.sql](queries/resumo_bracos.sql) | Resumo por braço: leads, spend, CPL, qualidade obs./comp., retorno obs./comp., receita |
| [queries/serie_diaria.sql](queries/serie_diaria.sql) | Série diária por braço (exclui form nativo — ingestão em lote) |
| [queries/mix_faixas.sql](queries/mix_faixas.sql) | Mix de faixas IQL por braço |
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
