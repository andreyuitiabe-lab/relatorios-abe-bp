# Análise: ELB26 (relançamento Entre Lobos) — Públicos-semente para Lookalike

**Data:** 2026-07-30
**Status:** estudo concluído; exports de listas pendentes de decisão
**Relatório:** [index.html](index.html) (template padrão: `data.json` + `refresh.py`)
**Contexto:** ELB26 em aquecimento desde 14/07/2026 (82,6k leads até 30/07, acelerando); venda ainda não abriu.
Original: ELB (mai–jun/2022). Houve também relançamento ELB24 (36,7k leads, jun–dez/2024).
Listas com PII saem fora do repo.

---

## Pergunta original

Replicar para o relançamento do Entre Lobos o estudo de públicos do ELS, para gerar sementes
de lookalike (LKL) para a fase de venda do ELB26.

## Base de aprendizado (testes de segmentação ELS, fase de venda)

| Semente | ROAS | Lição |
|---|---|---|
| "Sinal forte" | 2,13 | melhor teste |
| LKL compradores ELS 1% | 1,90 | comprador da campanha é semente forte |
| LKL viewers do doc | 1,68 | CPA maior, ticket maior (R$344) |
| LKL 1% genérico | 0,98 | semente genérica não funciona |
| Remarketing "Viu o Doc" | 0 vendas | viewer em geral já comprou (96% assistem pós-compra) |

## Decisões de abordagem

- Compradores ELB22: união `tracking_name ∪ utm_campaign ∪ utm_content` com fronteira de
  não-letra (`(^|[^a-z])elb([^a-z0-9]|$)|entre[-_ ]?lobos`), janela 17/05→31/07/2022,
  `approved` + `bl_is_renovation=FALSE`; e-mail via `dim_contact` (`id_gateway_customer`)
- Viewers: `obt_kafka__view_sessions`, `nm_playlist LIKE 'Entre Lobos%'` (série + episódios), ≥5min
- Compradores ELS incluídos como semente candidata por proximidade temática (segurança pública)
- Perfil: decil (`dtm_purchasing_power`), cartão (`int_credit_card_level`), gênero inferido (`dim_user`)

## Resultado — sementes dimensionadas e perfiladas

| Semente | N | Decil | % decil7+ | % cartão premium | % masc |
|---|---|---|---|---|---|
| 1. Compradores ELB 2022 | 18.538 | **5,63** | **41,2%** | 53,8% | 74,6% |
| 2. Viewers ELB (todos, ≥5min) | 462.553 | 5,30 | 36,6% | 49,8% | 73,1% |
| 3. Viewers ELB últimos 12m | 59.977 | 5,17 | 34,2% | 51,6% | 73,6% |
| 4. Viewers ELB ≥1h | 295.941 | 5,33 | 37,0% | 50,0% | 74,8% |
| 5. Compradores ELS | 35.143 | 5,47 | 38,3% | **57,0%** | 68,7% |
| 6. Compradores ELS ∩ viewers ELB | 4.826 | 5,46 | 38,9% | **60,2%** | **76,8%** |

Sub-tamanhos úteis: viewers decil7+ = 135k; viewers cartão premium = 184k;
compradores ELB22 decil7+ = 6,4k.

## IQL integrado (30/07)

Seção de qualidade dos leads adicionada ao relatório, lendo `bp-staging.dbt_abe.fct_lead_iql`
(agregados por faixa apenas — governança D20). 59,5k leads escorados até 29/07: **21,3% A+/A**
(12.657). O % A+/A diário caiu de ~50% (dia 1, base quente) para platô de ~20% com a mídia escalada.
Os leads A+/A entraram como **semente nº 7** ("sinal forte" da própria campanha, recência máxima) —
perfil de renda menor por construção (decil 5,03 / 38% cartão premium): o IQL qualifica por
probabilidade de conversão, não por renda. ⚠️ Pré-merge da MR !2426 o fct atualiza só com dbt run
manual (ver `wiki-bp/iql.md`).

## Perfil socioeconômico completo (31/07)

Seção nova no relatório com todas as dimensões do warehouse (renda decil + R$ p.c., hierarquia
de cartão, gênero, idade, região, capital/porte via CEP→IBGE). Query:
`queries/elb26_perfil_socioeconomico.sql`. Achados:

- **A semente A+/A (IQL) é outro bicho**: idade média 58,8 (53% com 60+, vs ~19–23% das demais),
  56,5% masc (vs 73–77%), cartão mais fraco (12,9% black, 24% básico), renda menor (mediana R$972).
  O IQL seleciona por comportamento/conversão — que na prática significa público mais velho e mais
  feminino, não mais rico. LKL dela vai buscar um público diferente dos LKLs de compradores.
- **% black distingue comprador de viewer**: compradores ELS 32,9% black e overlap ELS∩ELB 34,0%,
  vs 22–26% dos viewers. Decil quase não separa (5,17–5,63); o cartão separa mais.
- **Idade e geo são homogêneas** nas sementes de compradores/viewers: média 48–50 anos (faixa
  45–59 dominante), SE 52–54%, capital 41–51%. ELB22 mais capital (51%); ELS mais Sul (22,3%).
- **Coberturas** (calculado sobre quem tem o dado): renda 79–83% (A+/A 39%), cartão 80–90%
  (A+/A 36%), idade 9–40% (A+/A 8,5% — amostra de quem informa nascimento é enviesada), geo 36–39%.

## Perfil expandido — todas as gerações de Entre Lobos (31/07 tarde)

Query: `queries/elb26_perfil_socio_expandido.sql`. Segmentos novos: compradores ELB24 (302 —
relançamento 2024 quase não teve venda direta), conversos de leads ELB24 (1.132 de 36,7k = 3,1%),
viewers por produção (série principal 441k / Parte I-2023 30,6k / entrevistas 15k / produção 2026
1,4k em 3 dias). Achados:

- **%black separa comprador de viewer em 3 gerações** (31–34% vs 19–27%); decil não separa.
  Critério de ranking de sementes daqui em diante: %black > decil. (Ressalva: parte do gap pode
  ser viés de cobertura — comprador sempre tem transação.)
- **Funil de lead envelhece/empobrece quem converte — 2 fontes independentes**: conversos reais
  ELB24 (55,5 anos, decil 4,64, 12% black) ≈ leads A+/A IQL (58,8, 5,08, 13%). Compradores
  diretos de mídia: 48–50 anos, 23–33% black. Nuance (agente growth): o IQL foi treinado em
  conversão de lead, então as fontes medem o mesmo fenômeno — é fato sobre o **caminho lead**
  (~4–8% da receita), não sobre a campanha.
- Viewers produção 2026 premium (27,5% black, decil 5,44) mas n=1.410/3 dias — direcional.
- Viewers Parte I (2023): cobertura de dados ~55% → audiência de fora (janela para leads),
  perfil ≈ funil de lead.

## Mergulho demográfico fino (31/07 — idade, gênero, geo, profissão, pesquisa)

Base: `bp-staging.dbt_abe.tb_elb26_segmentos` (segmento × email, materializada dos 9 segmentos —
recriar rodando o CTE de `elb26_perfil_socio_expandido.sql`). Cortes ad-hoc, não versionados como .sql.

- **Idade mediana**: compradores/viewers 47–50; conversos ELB24 55; leads A+/A **60** (472 com 65+
  vs 40 com 25–34 entre quem informa).
- **Gênero — conflito entre fontes no A+/A**: declarado (`nm_gender`, n=2,9k) 83,9% masc vs
  inferido por nome 56,5%. O declarado é enviesado na base toda (610k M vs 113k F declarados) —
  usar o inferido como estimador; registrar o conflito.
- **Profissões** (cobertura ~13%): compradores ELB22 = policial militar 5,5% + militar 4,6% (o
  tema atrai o próprio público de segurança); ELS = empresário 8,5%; funil de lead (conversos +
  A+/A) = aposentado/a no topo (13,6–15%). Superfãs (entrevistas) = policial militar 4,9%.
- **Geo**: distribuições parecidas (SP 22–30%). Desvios: conversos ELB24 e A+/A over-index RJ
  (~21%/15,4% vs 12,6% dos viewers); compradores ELS under-index RJ (8,5%) e over-index Sul (22,3%).
- **Pesquisa ELB26 (4 perguntas, ~50% cobertura) — A+/A vs B/C/D**: ⚠️ as 4 perguntas alimentam
  o IQL, então diferenças são parcialmente por construção. Retrato do lead A+/A: **73% conhece a
  BP há 1+ ano** (vs 67% de "primeiro contato" no B/C/D — a mídia capta novos, mas o lead
  qualificado é fã antigo se cadastrando); 87% "profundamente incomodado" com mídia tradicional;
  31,5% assina streaming (vs 17%); renda declarada R$5k+ = 33% de quem informa (vs 11% no B/C/D —
  **contradiz o proxy por CEP**: decil mede o bairro, não a pessoa; aposentado de renda ok em
  bairro médio).

## Arquitetura [VENDA] revisada (agente growth, pós-correção de benchmark)

Split de referência (R$4M): **Advantage 60%** · **"sinal forte" replicado 15%** (Advantage+ com
sugestão de audiência = compradores ELS, se a config original não for recuperada) · **LKL
compradores ELS 12%** (ELB22 só se match rate ok) · **carrinho abandonado always-on 2–3%**
(+79% no ELS, ligado tarde) · **Teste A: LKL "conversor de funil"** = A+/A ∪ conversos ELB24
(~16,8k, excluir leads ELB26 do targeting) 3%, sucesso = empatar com Advantage · **Teste B:
upsell membros** com audiência = viewers produção 2026 (interesse quente pré-venda, atualizar
2×/sem) 3%, sucesso = ROAS ≥2. **Cortado: qualquer LKL de semente viewer; remarketing Viu o Doc.**

Decisões de leitura: avaliação de adset por **delta vs Advantage na mesma janela +7d** (promover
≥ +15% com ≥50 compras; cortar ≤ −15% em 2 leituras), nunca vs agregado. Público 55+ do funil de
lead: criativo dedicado DENTRO dos adsets (não adset por idade) + oferta via CRM para os A+/A.

## Achados

- **Compradores ELB22 são a semente de melhor perfil** (decil 5,63 / 41,2% decil7+ — acima até
  dos compradores ELS) e tamanho ideal para seed Meta (18,5k). Risco: recência (compra há 4 anos).
- **13,7% dos compradores ELS assistiram Entre Lobos** — afinidade temática real. O overlap
  (4,8k) é o segmento mais premium (60,2% cartão) e mais masculino (76,8%).
- Viewers da série têm perfil ~= base (decil 5,30) — semente de volume, não de qualidade.
  Recorte de qualidade: viewers decil7+ (135k) reproduz a lógica do "sinal forte" do ELS.
- Público ELB é o mais masculino já medido (73–77% vs 68,5% ELS).

## Recomendação de sementes para a fase [VENDA] do ELB26

1. **LKL compradores ELB22** (18,5k) — análogo direto do que deu ROAS 1,90 no ELS
2. **LKL viewers decil7+ / cartão premium** (135k/184k) — análogo do "sinal forte" (ROAS 2,13)
3. **LKL compradores ELS** (35,1k) — semente temática já validada, sem custo de montagem
4. Opcional: overlap ELS∩ELB (4,8k) — pequeno mas premium; testar com spend marginal
5. **Não usar viewers ELB para remarketing de venda** — lição ELS: viewer em geral já é membro

## Revisão data-analyst implementada (04/08)

- **Bloco "Decisão & status"** no topo + **estado da campanha derivado dos dados** (aquecimento
  ativo / pausa pré-venda / venda aberta — regras sobre leads/dia e spend Meta por fase). Headline,
  chips e ledes mudam sozinhos com o estado. Estado atual: pausa pré-venda (captação encerrou ~31/07).
- **CPL R$ 1,55 / CPLq R$ 8,27** (spend Meta R$ 130k ÷ 83,9k leads / ÷ 15,7k A+/A) — CPL abaixo
  do benchmark DOM (R$ 2,27). CPL blendado (inclui leads orgânicos no denominador).
- **Forecast de cenários da venda**: 83,9k leads × R$/lead blendado → R$ 1,24M (âncora DOM) /
  R$ 3,98M (ELS, central) / R$ 9,25M (ODD). Coeficientes de `aquecimento-vendas`.
- **Matriz de overlap das sementes** (tb_elb26_segmentos): máx **1,3%** entre ELS × ELB22 ×
  conversor de funil — públicos disjuntos, 3 adsets independentes sem canibalização.
- **Conversão por faixa IQL visível**: A+ 2,92% / A 1,32% / B 0,49% / C 0,19% / D 0,23% —
  monotonia quase perfeita, lift A+ vs C ≈ 15× (compras da fase de cadastro; venda não abriu).
- Legenda do heat na tabela, nota do conflito gênero declarado×inferido, lede do header neutro.
- Fica para o D1 da venda: curva D+N com benchmark ELS/ODD/DOM recebendo o realizado; recorte
  de recência na semente compradores ELS.

## Pendências / próximos passos

- [ ] Decidir quais sementes exportar (listas de e-mail hasheadas para upload no Meta — fora do repo)
- [ ] Quando a venda abrir: acompanhar ROAS por semente vs Advantage amplo (benchmark ELS 1,40)
- [ ] Proxy de qualidade dos 51k leads ELB26 por criativo (metodologia `relatorios/campanhas/`)

## Queries

| Arquivo | O quê |
|---|---|
| [queries/elb26_sementes_lookalike.sql](queries/elb26_sementes_lookalike.sql) | Dimensiona e perfila as 7 sementes candidatas |
| [queries/elb26_perfil_socioeconomico.sql](queries/elb26_perfil_socioeconomico.sql) | Perfil socioeconômico completo (renda, cartão, idade, gênero, geo IBGE) |

## Wiki atualizada

- (pendente) criar página `wiki-brasil-paralelo/pages/entre-lobos.md` se o tema virar recorrente
