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

## Pendências / próximos passos

- **Braço otimizado por IQL depende da ponte CAPI** (decidido: priorizar). Sequência: MR do A1
  (dataset dedicado) → token no Business Manager → ponte em dry-run → teste → ligar. O braço entra
  no relatório sozinho quando a campanha começar a gastar.
- **Levar as perguntas de qualificação para o form nativo** (a Meta suporta perguntas customizadas):
  hoje o form nativo ganha em custo mas é cego em qualidade — com pesquisa, seria o melhor braço em
  todas as leituras. É a maior alavanca imediata da JOM.
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
