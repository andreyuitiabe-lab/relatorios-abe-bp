# Teste C — GA4 newUsers como indicador diário de relevância

**Data:** 02/09/2026 · **Contexto:** rodada 4 da análise de relevância (`ANALISE.md`) listou
`newUsers` do GA4 como "candidato imediato, ainda não testado".

## Pergunta

`newUsers` mede gente **nova** chegando, não membro voltando — a rodada 2 mostrou que boa parte
do tráfego orgânico (sobretudo direto) é membro entrando para assistir. Conceitualmente é melhor
que sessões. Passa no crivo da rodada 4? Supera os vencedores atuais (YouTube orgânico
ρ→vendas +0,265 / ρ→CAC −0,143 · busca orgânica +0,184/−0,197 · Wikipedia +0,243/−0,208)?

## Resposta curta

**Passa no crivo nos recortes orgânicos, mas não supera os vencedores — porque não é um
indicador novo: é a mesma série das sessões com outro nome.** A correlação entre `newUsers` e
`sessions` do mesmo canal é 0,95–0,99. O melhor recorte (Organic Video) empata com as sessões de
YouTube orgânico (+0,268/−0,156 vs +0,265/−0,143 — diferenças na casa do ruído), e a busca fica
até ligeiramente **pior** em newUsers. O TOTAL e o Organic Social **medem orçamento** (ρ com
spend 0,79 e 0,83), como pré-registrado. **Não há motivo para trocar sessões por newUsers no
painel diário; a Wikipedia segue com o melhor sinal de eficiência entre as fontes novas.**

O motivo conceitual da decepção importa: **"novo" no GA4 é cookie/device novo, não pessoa
nova.** No tráfego direto — o canal onde filtrar "membro voltando" mais ajudaria — 64% dos
usuários contam como "novos" (mediana nu/sessões 0,64), o que é impossível em pessoas: é membro
em outro aparelho, navegador ou janela anônima. O filtro que o newUsers promete, ele não entrega.

## Série coletada

- **Fonte:** GA4 Data API, property 378996649, mesma credencial do MCP `ga4` (o fetch está no
  script, reproduzível). Janela coletada: **01/08/2025 → 01/09/2026 (397 dias)**; crivo aplicado
  na interseção com o painel de spend: **01/08/2025 → 20/08/2026 (385 dias)** — a mesma janela
  da rodada 4.
- **Dimensão de canal:** `sessionDefaultChannelGroup` **e** `firstUserDefaultChannelGroup` —
  as duas combinam com `newUsers` na API. Para usuário novo, a primeira sessão É a sessão de
  aquisição, então os dois escopos coincidem por construção: ρ=0,9999, diferença máxima de
  38 usuários/dia. Adotei **first-user** como canônico (canal de AQUISIÇÃO do usuário, a
  semântica correta para newUsers); resultados idênticos nos dois.
- **Arquivo:** `data/teste_c_ga4_newusers.csv` (total + 5 canais × 2 escopos).

| Recorte (1st-user) | Mediana/dia | Comparação com sessões do canal |
|---|---:|---|
| newUsers TOTAL | 69.751 | — (sessões totais ~135k) |
| Organic Social | 34.804 | 66% das sessões · ρ c/ sessões 0,993 |
| Organic Search | 10.412 | 66% · ρ 0,992 |
| Direct | 5.891 | **64%** · ρ 0,993 ← "novo" = cookie novo |
| Organic Video | 338 | 47% · ρ 0,953 |
| Referral | 59 | 36% · ρ alto |

Os 5 canais orgânicos somam **85%** do newUsers total — o total é dominado pelo Organic Social
(34,8k de ~70k), que é a série já descartada como medida de orçamento.

## Crivo da rodada 4 (mesma especificação do `avaliar_fontes.py`)

Residualização `log1p(x) ~ DOW + mês + log1p(spend) + em_venda + em_aquecimento + tendência`,
Spearman nos resíduos, 385 dias. Tabela completa (11 da rodada 4 + newUsers) em
`data/teste_c_avaliacao.csv`.

| Indicador | ρ c/ spend | Indep.? | ρ→vendas | ρ→CAC | Veredito |
|---|---:|---|---:|---:|---|
| **newUsers Organic Video (1st-user)** | 0,233 | sim | **+0,268\*** | **−0,156\*** | ★ volume + eficiência |
| *YouTube orgânico (sessões, rodada 4)* | *0,162* | *sim* | *+0,265\** | *−0,143\** | *★* |
| **newUsers Organic Search** | −0,178 | sim | +0,154\* | −0,184\* | ★ volume + eficiência |
| *Busca orgânica (sessões)* | *−0,188* | *sim* | *+0,184\** | *−0,197\** | *★* |
| **newUsers Direct** | 0,390 | meio | +0,150\* | −0,115\* | ★ volume + eficiência |
| *Tráfego direto (sessões)* | *0,371* | *meio* | *+0,163\** | *−0,118\** | *★* |
| **newUsers Referral** | −0,098 | sim | +0,172\* | −0,084 | só volume |
| *Referral (sessões)* | *−0,071* | *sim* | *+0,211\** | *−0,070* | *só volume* |
| **newUsers TOTAL** | **0,793** | **NÃO** | +0,124\* | −0,108\* | **mede orçamento** |
| **newUsers Organic Social** | **0,832** | **NÃO** | −0,027 | −0,150\* | **mede orçamento** |
| *Social orgânico (sessões)* | *0,861* | *NÃO* | *+0,013* | *−0,137\** | *mede orçamento* |
| *Wikipedia — verbete BP (referência)* | *0,315* | *meio* | *+0,243\** | *−0,208\** | *★* |

\* p<0,05. Recortes session-scoped idênticos aos 1st-user (omitidos; estão no CSV).

**Leitura por recorte:**

1. **newUsers TOTAL mede orçamento** (ρ spend 0,793), exatamente como pré-registrado: é dominado
   pelo Organic Social, que sobe com campanha. Descartado.
2. **newUsers Organic Video** é o único recorte que encosta nos vencedores: +0,268/−0,156, contra
   +0,265/−0,143 das sessões YT. O "ganho" de −0,013 no CAC está dentro do ruído e vem com ρ
   spend maior (0,233 vs 0,162) e volume menor (338/dia vs 767) — e as duas séries têm ρ 0,953
   entre si: **é o mesmo termômetro**.
3. **newUsers da busca orgânica é ligeiramente PIOR que as sessões** (+0,154/−0,184 vs
   +0,184/−0,197) — na busca, o returning visitor que o newUsers exclui também carregava sinal.
4. **newUsers Direct não resolve o problema do Direct**: continua "meio" confundido com spend
   (0,390) e com o pior sinal dos recortes ★. A promessa de filtrar membro voltando falha porque
   o GA4 conta cookie novo, não pessoa nova (64% do direct "novo").

## Bônus — pareamento por spend do melhor recorte (newUsers Organic Video)

Mesmo desenho do `teste_pareado_spend.py` (alta vs baixa dentro de quintil de spend ×
fim-de-semana × fase de venda, bootstrap 2.000 reps). Saída completa em
`data/teste_c_pareado_resultado.txt`.

| Métrica | Baixa | Alta | Δ | IC95 |
|---|---:|---:|---:|---|
| Transações/dia | 1.125 | 1.382 | **+23,4%** \*\*\* | [+16,3%, +33,6%] |
| Receita/dia | R$ 454,6k | R$ 522,6k | +23,2% \*\*\* | [+14,6%, +37,7%] |
| CAC de ads | R$ 312 | R$ 278 | **−9,5%** \*\*\* | [−14,0%, −3,9%] |
| Tx digitais/1k sessões | 6,9 | 7,9 | +18,6% \*\*\* | [+9,5%, +31,2%] |
| ROAS | 3,6 | 4,4 | +19,7% \*\*\* | [+11,8%, +31,3%] |
| Ticket médio | R$ 395 | R$ 390 | +1,7% ns | — |
| **Spend [checagem]** | 144,7k | 148,6k | **+3,7%** \*\* | [+0,1%, +8,4%] |

Mesmo padrão das sessões YT (+24,7% tx / −11,9% CAC), com uma ressalva a mais: aqui o
**pareamento por spend não fechou perfeito** (+3,7%, p=0,046, vs +0,4% ns nas sessões) — parte
do efeito de volume pode ser mídia residual. O CAC menor com spend maior vai na direção contrária
à contaminação, mas a versão em sessões continua sendo o teste mais limpo.

## Veredito

| Recorte | Interpretação pré-registrada aplicável | Decisão |
|---|---|---|
| TOTAL | "mede orçamento (ρ>0,55) → descartar" | **descartado** |
| Organic Social | idem | **descartado** |
| Organic Video | passa no crivo, **não supera** YT orgânico (empate, ρ 0,95 entre as séries) | não entra — redundante com o termômetro atual |
| Organic Search | passa, mas pior que sessões da busca | não entra |
| Direct | passa por margem, "meio" confundido | não entra |
| Referral | só volume | não entra |

**O painel diário proposto na análise-mãe não muda**: YouTube orgânico (sessões) como termômetro
principal, busca orgânica e Wikipedia como confirmação. `newUsers` fica registrado como variante
redundante — se um dia a série de sessões quebrar (mudança de instrumentação), o newUsers
Organic Video é o substituto direto com sinal equivalente.

## Limitações

- **"Novo" ≠ pessoa nova.** `newUsers` = primeiro `first_visit` do client_id (cookie/device).
  Membro em outro aparelho, navegador ou aba anônima conta como novo — por isso 64–66% do
  tráfego "novo" em Direct/Social, impossível em pessoas. A limitação é estrutural do GA4, não
  do teste.
- **Thresholding do GA4**: não observado nesta extração (nenhum dia zerado; mínimos plausíveis,
  ex. Organic Video min 61), mas relatórios com métricas de usuário podem sofrer thresholding em
  dias de Google Signals — vale re-checar se a série for operacionalizada.
- **Escopo de canal**: `sessionDefaultChannelGroup` e `firstUserDefaultChannelGroup` combinam
  ambas com `newUsers` e coincidem por construção para usuários novos (ρ 0,9999, dif. máx.
  38/dia). Usado o first-user (canal de aquisição) como canônico.
- **Pareamento do bônus imperfeito** (spend +3,7%, p<0,05): ler o −9,5% de CAC como direcional.
- Mesmas limitações da rodada 4: correlação contemporânea ≠ causalidade; janela de 385 dias.

## Arquivos

| Arquivo | O quê |
|---|---|
| `scripts/teste_c_newusers.py` | fetch (GA4 Data API, credencial do MCP) + crivo + pareado. `--fetch` roda com `mcp-ga4/.venv/bin/python`; análise com python normal |
| `data/teste_c_ga4_newusers.csv` | série diária: total + 5 canais × 2 escopos (397 dias) |
| `data/teste_c_avaliacao.csv` | tabela do crivo: 11 indicadores da rodada 4 + 11 recortes de newUsers |
| `data/teste_c_pareado_resultado.txt` | pareamento por spend do newUsers Organic Video |
