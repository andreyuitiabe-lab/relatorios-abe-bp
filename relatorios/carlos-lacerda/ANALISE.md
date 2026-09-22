# Carlos Lacerda (LAC) × Enéas (ENE) — os primeiros dias

**Pedido:** Bárbara Olivieri (22/09/2026, 10h14): comparar os 4 primeiros dias de Enéas e Carlos —
CPM, volumetria de ads, e-mails disparados, visitas em LP e engajamento nos ads. Prazo: 22/09 15h.

**Relatório:** https://andreyuitiabe-lab.github.io/relatorios-abe-bp/relatorios/carlos-lacerda/
**Apuração:** 22/09/2026 (⚠️ spend Meta sobe ao longo do dia — ver `wiki-bp/meta-insider-ads.md`).

## Decisões de abordagem

- **D1 = primeiro dia com entrega registrada**: LAC 19/09, ENE 28/07.
- **Comparação em D1–D3**, não D1–D4: o dia 22/09 (D4 da LAC) só tem vendas fechadas; mídia e CRM do
  dia ainda não estavam no warehouse. ⚠️ **Todas as janelas — campanha, conta, CRM, LP — com o mesmo
  número de dias.** A 1ª versão comparava 4 dias de julho contra 3 de setembro no benchmark de CPM.
- ⚠️ **Os dias da semana não são equivalentes**: ENE estreou numa terça (ter/qua/qui) e LAC num sábado
  (sáb/dom/seg). Valores absolutos não são pareáveis; o CPM é lido pelo **índice contra a conta do
  mesmo dia**, que absorve o efeito do fim de semana.
- **Separar `[LEAD]` de `[VENDA]`**: a ENE rodava as duas fases; a LAC só tem `[VENDA]`.
- **Hook e hold só sobre anúncios com vídeo** (ver achado 2 — mudou a conclusão).
- **Somar os 3 canais de mídia** (Meta + PMax + Google), regra de `meta-insider-ads.md`.
- Vendas por **rastro** (método ELS/ENE), não janela: lançamento de produto (`regras-negocio.md`).

## Achados principais

**1. O CPM subiu porque o leilão subiu — e isso foi testado, não suposto.** LAC R$ 18,77 × ENE
R$ 16,31 (+15%); a conta Meta em campanhas de venda foi de R$ 21,31 (jul) para R$ 27,81 (set), +30%;
índice campanha ÷ conta **0,67 (LAC) × 0,77 (ENE)**. O controle que fecha o argumento: das **7
campanhas de venda que rodaram nos dois meses** com volume relevante, **as 7 encareceram** — CPM
pareado R$ 20,42 → R$ 29,20, **+43%**. Não é mudança de composição da carteira, é preço de leilão.
Dentro da LAC o CPM caiu de R$ 25,60 (D1) para R$ 13,90 (D3) enquanto o da ENE subia — aprendizado
normal, a favor da LAC.

**2. O criativo prende a atenção e perde no meio — e o número anterior estava diluído.**
**17 dos 26 anúncios da LAC são estáticos** e não geram métrica de vídeo (30% das impressões).
Incluí-los derrubava o hook para 29,8% e produzia a conclusão errada ("hook pior que o da ENE").
Só sobre anúncios com vídeo:

| | ENE | LAC |
|---|---|---|
| Hook rate | 35,7% | **42,5%** |
| Hold rate | **60,1%** | 34,1% |
| CTR outbound | 2,90% | 2,08% |
| CPC | R$ 0,56 | R$ 0,90 |

A LAC chama *mais* atenção e segura *bem menos*. ⚠️ `thruplay` conta vídeo completo **ou** 15s, o que
vier antes: se as peças da LAC forem mais longas, parte do gap é duração e não retenção — confirmar
com o time de criação.

**3. A mídia da LAC rende metade — é a trava para escalar verba.** Receita atribuída ÷ investimento
no Meta: **0,56 (LAC) × 1,08 (ENE)**; custo por venda **R$ 737 × R$ 191** (3,9×). Por rastro e
somando os 3 canais: 0,60 × 1,07. A versão anterior dizia "converte em ritmo parecido, só está
menor" — **estava errado**.

**4. São dois modelos de lançamento.** ENE: 102 anúncios, R$ 23,9k nos 3 canais, **captação ativa**
(R$ 5,9k em `[LEAD]` → 4.857 leads, **CPL de mídia R$ 1,34**). LAC: 26 anúncios, R$ 8,7k, **zero
captação** — não existe campanha `[LEAD]`, nem tag `LAC` em `lead_conversion`, nem LP de cadastro.
No ritmo da ENE são ~1,6 mil leads/dia a ~R$ 2 mil/dia de mídia que a LAC não está construindo.

**5. O e-mail não está saturado: está com abertura baixa.** 697k e-mails + 1,70M push + 9,2k WhatsApp
em 3 dias (335× o volume de CRM da ENE, que fazia jornada 1:1). Mas:

| | LAC | Referência da casa |
|---|---|---|
| Abertura | 4,45% | 7,6% |
| Clique ÷ abertura (CTOR) | **21,1%** | 3,4% |
| Descadastros | 342 (0,05%) | — |
| Spam | 15 | — |

Quem abre clica ~6× mais que a média da casa e a lista não está sendo queimada. O diagnóstico não é
fadiga: é **assunto/remetente/entregabilidade**. Mexer nisso, não no volume. ⚠️ App push não tem
telemetria de abertura/clique no warehouse — é volume entregue, não engajamento medido.

**6. A LP recebe menos gente e converte um terço.** LP de venda: 25.729 pv (ENE) × 11.373 (LAC);
a ENE ainda tinha 21.237 pv nas LPs de cadastro. Conversão de sessão em venda: **0,16% (LAC) ×
0,43% (ENE)**, 2,7× pior. ⚠️ O numerador da ENE inclui vendas vindas também da LP de cadastro e do
CRM — a vantagem dela está algo superestimada, mas a ordem de grandeza se mantém. Aponta para
**oferta e página**, não só criativo.

**7. Vendas por rastro (D1–D3):** ENE 106 transações / R$ 25,6k; LAC 16 / R$ 5,2k.

## Conclusão para o time de campanha

1. **Não escalar verba** com retorno de mídia em 0,56 e venda a R$ 737. Régua: escalar só acima de 1,0.
2. **Atacar retenção**, não atenção — o hook já é melhor que o da ENE; o problema é do 3º segundo em diante.
3. **Testar oferta e LP em paralelo** — conversão de sessão é um terço da ENE.
4. **No e-mail, mexer em assunto e remetente**, não no volume.
5. **Decidir explicitamente sobre captação** — cada dia sem captar é base que não existirá na venda.

## Críticas levantadas na revisão e como foram resolvidas

Duas revisões independentes (agentes de dataviz e de análise) auditaram a 1ª versão. O que foi testado:

| Crítica | Veredito | Evidência |
|---|---|---|
| "O +30% do leilão é mix da conta, não preço" (CPM `[LEAD]` caiu 24% no mesmo período) | **Refutada** | Teste pareado within-campaign: 7 de 7 campanhas encareceram, +43% (`queries/07`) |
| "Hook/hold contaminados por anúncios estáticos" | **Confirmada — mudou a conclusão** | 17 de 26 ads da LAC sem métrica de vídeo; hook real 42,5% e não 29,8% (`queries/06`) |
| "A LAC não converte 'em ritmo parecido'" | **Confirmada — mudou a conclusão** | ROAS de mídia 0,56 × 1,08; custo/venda R$ 737 × R$ 191 (`queries/06`) |
| "Só o Meta foi varrido; falta PMax/Google" | **Confirmada** | LAC +R$ 1,3k de PMax; ENE +R$ 1,9k PMax +R$ 761 Google (`queries/08`) |
| "CPL de R$ 1,22 subestimado (numerador Meta, denominador todas as fontes)" | **Confirmada, impacto pequeno** | CPL de mídia real R$ 1,34 (91% dos leads da ENE vieram do Meta) |
| "CRM: fadiga de lista" (versão 1) | **Corrigida** | Descadastro 0,05% e CTOR 6× a casa: o problema é abertura, não saturação (`queries/09`) |
| Série de abertura por data de evento | **Corrigida** | A cauda de abertura do dia anterior contaminava a série — passou a ser por data de disparo |
| Regex `lacerda` no CRM | **Corrigida** | Casava `EM10 - [INP] [VEN] [NME] - Marina Lacerda`; agora só `[lac]` |
| Vazamento de janela no CRM | **Corrigida** | A ENE segue ativa em set/2026 e entrava no lado da LAC; cada sigla só na sua janela |

## Pendências / próximos passos

- Conferir o spend contra o Gerenciador de Anúncios antes de circular (regra da wiki).
- Reavaliar com o D4 fechado (23/09, após o rebuild das 8h).
- Confirmar com o time se a ausência de campanha `[LEAD]` na LAC é decisão ou lacuna.
- Pedir ao time de criação a **duração** das peças de LAC e ENE — sem isso o gap de hold fica parcialmente
  explicável por formato (`thruplay` = 15s ou vídeo completo).
- Ranking por anúncio dentro da LAC (matar/escalar) — com 3 dias e 10 vendas, ranquear por CPC/CTR, não por ROAS.
- Comparar a LAC com outras pré-vendas sem captação (TEC, ODI, CDL) em vez de só com a ENE.

## Relatório HTML

`index.html` + `data.json` + `refresh.py` (padrão do template). O `refresh.py` roda as queries no BQ
pelo cliente Python (ADC, como o `bqq`) e chama `ga4_lp.py` **na venv do MCP GA4**, onde vivem o
`google-analytics-data` e o token OAuth. Rodar: `python refresh.py` (ou `--push`).

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/01_meta_primeiros_dias.sql](queries/01_meta_primeiros_dias.sql) | Meta Ads dia a dia, D1–D4, por fase |
| [queries/02_insider_primeiros_dias.sql](queries/02_insider_primeiros_dias.sql) | Disparos CRM por canal/dia (exploratória) |
| [queries/03_vendas_rastro.sql](queries/03_vendas_rastro.sql) | Vendas atribuídas por rastro |
| [queries/04_cpm_benchmark_conta.sql](queries/04_cpm_benchmark_conta.sql) | CPM da conta, dia a dia, + índice campanha ÷ conta |
| [queries/05_resumo_d1_d3.sql](queries/05_resumo_d1_d3.sql) | Anúncios distintos por sigla/fase |
| [queries/06_criativo_e_roas.sql](queries/06_criativo_e_roas.sql) | Hook/hold só sobre vídeo, CTR, CPC, ROAS de mídia, custo por venda |
| [queries/07_cpm_pareado.sql](queries/07_cpm_pareado.sql) | Teste within-campaign: leilão × mix de carteira |
| [queries/08_midia_todos_canais.sql](queries/08_midia_todos_canais.sql) | Meta + PMax + Google |
| [queries/09_crm_por_disparo.sql](queries/09_crm_por_disparo.sql) | E-mail por data de disparo + saúde da lista |

Visitas de LP: MCP GA4 (property 378996649). ⚠️ O `dimension_filter` do MCP é ignorado — filtrar o
path no pós-processamento (é o que o `ga4_lp.py` faz).
