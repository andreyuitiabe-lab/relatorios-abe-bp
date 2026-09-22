# Carlos Lacerda (LAC) × Enéas (ENE) — os 4 primeiros dias

**Pedido:** Bárbara Olivieri (22/09/2026, 10h14): comparar os 4 primeiros dias de Enéas e Carlos —
CPM, volumetria de ads, e-mails disparados, visitas em LP e engajamento nos ads. Prazo: 22/09 15h.

**Apuração:** 22/09/2026 14h34 (⚠️ spend Meta sobe ao longo do dia — ver `wiki-bp/meta-insider-ads.md`).

## Decisões de abordagem

- **D1 = primeiro dia com spend registrado**: LAC 19/09, ENE 28/07. A LAC subiu 2 anúncios em 18/09
  sem entrega; a ENE teve criativos de pré-venda em 24–26/07 idem.
- **Comparação principal em D1–D3**, não D1–D4: o dia 22/09 (D4 da LAC) ainda não entrou no mart de
  mídia (Adveronix roda de manhã) nem no CRM. Vendas do D4 saem porque vêm de `fct_transactions`.
  ⚠️ **Todas as janelas — campanha, conta, CRM, LP — têm de ter o mesmo número de dias.** A 1ª versão
  desta análise comparou 4 dias de julho contra 3 de setembro no benchmark de CPM; corrigido.
- ⚠️ **Os dias da semana não são equivalentes**: ENE estreou numa terça (ter/qua/qui) e LAC num sábado
  (sáb/dom/seg). Valores absolutos de CPM, CRM e LP não são pareáveis entre as duas; por isso o CPM é
  lido pelo **índice contra a conta do mesmo dia**, que absorve o efeito do fim de semana.
- **Separar `[LEAD]` de `[VENDA]`**: a ENE rodava as duas fases juntas; a LAC só tem `[VENDA]`
  (pré-venda). Comparar o agregado das duas contra uma campanha só-venda mistura leilões diferentes.
- **CPM sempre contra a conta inteira no mesmo período** — sem esse controle não dá para separar
  campanha de leilão.
- Vendas por **rastro** (método ELS/ENE), não janela: lançamento de produto (`regras-negocio.md`).

## Achados principais

**1. O CPM da LAC não está caro — o leilão é que está.** LAC R$ 18,77 vs ENE (venda) R$ 16,31:
+15%. Mas a conta inteira, em campanhas de venda, foi de R$ 21,31 (jul) para R$ 27,81 (set): +30%.
Relativo à conta do próprio período, a LAC está **mais barata** que a ENE estava (índice **0,67 vs
0,77**). Dentro da LAC o CPM já caiu de R$ 25,60 (D1) para R$ 13,90 (D3), enquanto o da ENE subia
(13,40 → 18,15) — curva normal de aprendizado, e a favor da LAC.

**2. A diferença real é de escala e de modelo de lançamento, não de eficiência de leilão.**

| D1–D3 | ENE (28–30/07) | LAC (19–21/09) |
|---|---|---|
| Anúncios ativos | 102 (47 lead + 55 venda) | **26** (só venda) |
| Spend Meta | R$ 21,2k | R$ 7,4k (35%) |
| Impressões | 1,29 mi | 393 mil (30%) |
| CPM | R$ 16,39 | R$ 18,77 |
| Campanha de captação | sim (R$ 5,9k, 4.857 leads, CPL ~R$1,22) | **não existe** |
| PMax | — | R$ 1,3k |

**3. Engajamento no criativo é o ponto fraco da LAC.** Comparando venda × venda:

| Métrica | ENE venda | LAC |
|---|---|---|
| Hook rate (3s/impr) | 35,7% | 29,8% |
| **Hold rate (thruplay/3s)** | **60,1%** | **34,1%** |
| CTR outbound | 2,90% | 2,08% |
| CPC | R$ 0,56 | R$ 0,90 |

O hold rate é o sinal mais forte: quem começa a ver o vídeo da LAC abandona quase o dobro. Com CPM
controlado, é o criativo (retenção do vídeo), não a mídia, que puxa o CPC para cima.

**4. O CRM é o oposto: LAC dispara em massa, ENE quase não usou.**

| Canal, D1–D3 | ENE | LAC |
|---|---|---|
| E-mail entregue | 3.566 (jornada 1:1) | **697.333** (13 peças, ~232k/dia) |
| App push | 0 | 1.695.609 |
| WhatsApp | 3.605 | 9.251 |
| Abertura e-mail | — | 5,09% → 3,63% (caindo dia a dia) |
| Cliques e-mail | 26 | 6.492 |

A ENE nos primeiros dias vivia de mídia paga + captação; a LAC vive de base própria. A taxa de
abertura caindo (5,09 → 4,63 → 3,63%) com clique subindo (0,73 → 1,30%) indica fadiga de
frequência no topo da lista, com o clique se concentrando em quem já estava interessado.

**5. Visitas em LP acompanham o tamanho da mídia, não o do CRM.**

| LP, D1–D3 | ENE | LAC |
|---|---|---|
| LP de venda | 25.729 pv (`/seja-membro/filmes/eneas`) | 11.373 pv (`/seja-membro/filmes/carlos-lacerda`) |
| LP de cadastro | 15.415 pv (`/cadastro-eneas/a` + `/b`) | não existe |

**6. Vendas por rastro (D1–D3):** ENE 106 transações / R$ 25,6k; LAC 16 / R$ 5,2k. Em D1–D4:
ENE 148 tx / R$ 45,3k (ticket R$ 306) vs LAC 21 tx / R$ 6,9k (ticket R$ 327). Proporcional ao
investimento — a LAC converte o tráfego pago num ritmo parecido, ela só está menor.

## Conclusão para o time de campanha

1. Parar de olhar o CPM absoluto: setembro está 30% mais caro para todo mundo. O indexado da LAC é bom.
2. A alavanca imediata é **criativo** (hold rate 34% vs 60%), não verba nem público.
3. A LAC não tem captação de lead nenhuma — a ENE tinha 1,2–2 mil leads/dia a R$ 1,22 desde o D1.
   Se o filme só estreia depois, não montar base agora é o custo mais caro da campanha.
4. O CRM já está no talo (697k e-mails + 1,6M push em 3 dias) com abertura caindo — não há muito mais
   a extrair dali; o crescimento tem de vir de mídia + criativo.

## Pendências / próximos passos

- Conferir o spend contra o Gerenciador de Anúncios antes de circular os números (regra da wiki).
- Reavaliar a LAC com o D4 fechado (23/09, depois do rebuild das 8h).
- Confirmar com o time se a ausência de campanha `[LEAD]` na LAC é decisão ou lacuna.

## Relatório HTML

`index.html` + `data.json` + `refresh.py` (padrão do template). O `refresh.py` roda as queries no BQ
pelo cliente Python (ADC, como o `bqq`) e chama `ga4_lp.py` **na venv do MCP GA4**, que é onde vivem o
`google-analytics-data` e o token OAuth. Rodar: `python refresh.py` (ou `--push`).

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/01_meta_primeiros_dias.sql](queries/01_meta_primeiros_dias.sql) | Meta Ads dia a dia, D1–D4, por fase |
| [queries/02_insider_primeiros_dias.sql](queries/02_insider_primeiros_dias.sql) | Disparos CRM por canal/dia |
| [queries/03_vendas_rastro.sql](queries/03_vendas_rastro.sql) | Vendas atribuídas por rastro |
| [queries/04_cpm_benchmark_conta.sql](queries/04_cpm_benchmark_conta.sql) | CPM da conta inteira, dia a dia, + índice campanha ÷ conta (controle) |
| [queries/05_resumo_d1_d3.sql](queries/05_resumo_d1_d3.sql) | Anúncios distintos por sigla/fase em D1–D3 |

Visitas de LP: MCP GA4 (property 378996649), dimensões `date` + `pagePath`, métricas
`screenPageViews`/`sessions`. ⚠️ O parâmetro `dimension_filter` do MCP é ignorado — filtrar o path
no pós-processamento.
