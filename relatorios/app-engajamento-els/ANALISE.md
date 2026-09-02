# App Engajamento ELS — Google Ads (jun/2026)

> ANALISE.md criado retroativamente (jul/2026) na padronização do repo — detalhes de decisão não registrados na época.

## Pergunta original
Acompanhar o desempenho diário das campanhas de app/engajamento ligadas ao ELS no Google Ads.

## Estrutura
Padrão template completo: `index.html` + `data.json` + `refresh.py` (fonte: `datamart.dtm_analytics_google_ads_funnel`).

## Metodologia (ago/2026)

[metodologia.html](metodologia.html) — diagramas do pipeline de medição das campanhas `[APP]`: as três fontes que não se falam (Firebase, Guru, planilha Adveronix), a cadeia de chaves `id_pseudo_user → id_user → id_subscription → id_transaction` com os três pontos de vazamento, e a reconciliação teto/piso (7.092 conversões reportadas pelo Google vs 3.374 installs atribuídos pelo Firebase).

Pontos que a metodologia deixa explícitos:
- **O funil de cadastro subconta.** O trio de telas `welcome → signup_email → signup_password` não cobre `ios_signup`, `signup`, `signup_form` nem `signup_complete` — âncora mais defensável para "conta criada" é `masterdata.dim_user.dt_created_at`.
- **A receita fecha pela assinatura**, então perde vitalício e compra avulsa (`id_subscription IS NULL`).
- **O ROAS é teto**: ≥ 671 dos 3.374 devices já tinham conta antes do install, logo parte da receita da janela aconteceria sem a campanha.

## Cobertura de atribuição (18/06–13/08/2026)

| SO | first_open | com `medium='cpc'` | com token `[APP]` |
|---|---:|---:|---:|
| Android | 44.203 | 7.985 (18,1%) | 2.274 |
| iOS | 38.460 | 1.731 (4,5%) | 1.089 |

**Meta Ads é o buraco real, não o iOS.** No período o Firebase registrou **1** `first_open` com `apps.facebook.com` — a atribuição de install via Meta não existe sem deep link com UTM ou MMP. O iOS tem atribuição, ~4× pior que o Android.

## Revisão de 24/ago/2026 — Meta e o tamanho do erro do funil

Duas afirmações do relatório de 13/08 envelheceram:

**1. "Meta Ads não aparece" virou "Meta aparece como canal, nunca como campanha".** O Meta passou a ter 4 campanhas `[APP]` (R$ 6.012 desde 11/08) e o Firebase registra o canal: 359 devices `apps.facebook.com` + 81 `apps.instagram.com` em 18/06–24/08. Mas `nm_traffic_source_name` vem literalmente `fb4a`/`ig4a` (referrer do app FB/IG no Android), `medium` é NULL, e **não há um único device iOS**. Os installs se concentram em **14–18/08**, exatamente a janela das campanhas `[ADVANTAGE] Agosto | Android` (R$ 768) e `| ios` (R$ 725) — o que é inferência temporal, não atribuição, e o sinal ainda é contaminado por clique orgânico em link do FB/IG. Campanha Meta que manda para landing em vez da store não gera sinal nenhum (`Agosto App Pagina`, R$ 4.519, zero install rastreável). E `dtm_analytics_facebook_ads_funnel` não tem métrica de install, então não existe reconciliação teto/piso como a que foi feita com o Google.

A ponte device→conta funciona normalmente nesses devices — o buraco é só a chave de campanha: dos 412 devices FB/IG de 14–18/08, **221 entraram na conta, 105 consumiram conteúdo, 58 viram paywall**.

**2. O funil de cadastro subconta ~71%, não "um pouco".** A tela sai de `st_event_params` (param `view`) — não existe coluna `nm_view`. Medido em 20–22/08, o trio `welcome → signup_email → signup_password` pega 955 devices contra ~3.300 que passam por alguma tela de cadastro: `signup` 1.194, `email_check_signup` 710, `ios_signup` 609, `signup_form` 290, `signup_complete` 121 estão todos fora. Isso dimensiona a pendência de trocar a âncora para `dim_user.dt_created_at`.

**3. Rerodar o pipeline hoje muda os números — o snapshot de 13/08 pegou dias incompletos.** A query [pipeline_completo.sql](queries/pipeline_completo.sql) na mesma janela (18/06–13/08) devolve agora:

| Métrica | Relatório 13/08 | Rerodado 24/08 |
|---|---:|---:|
| Instalações atribuídas | 3.374 | **3.619** |
| Contas criadas (trio de telas) | 993 | **1.012** |
| Compradores | 65 | **74** |
| Receita | R$ 19.054 | **R$ 21.828** |
| ROAS | 1,18 | **1,35** |

Quase toda a diferença é **FREE Agosto Android: 392 → 645 instalações** (receita R$ 4.663 → R$ 6.813, ROAS 4,72 → **6,90**). A campanha começou em 11/08 e o relatório rodou em 13/08 — os três últimos dias estavam com dados intraday incompletos no Firebase. As campanhas de junho variaram <0,5% (reprocessamento normal). **Leitura: o FREE Agosto era ainda melhor do que o relatório mostrou.** `bl_is_renovation` continua zero em todas — a conclusão "todas são venda nova" se mantém.

**Entrega:** o artifact `bcf14572` ganhou o diagrama do pipeline de conexão (fig. 1 do [metodologia.html](metodologia.html) portado para dentro dele). Fonte local do artifact: [funil-jornada-app.html](funil-jornada-app.html) — é o arquivo a editar para republicar.

## Queries
| Query | O que faz |
|---|---|
| [diario_por_campanha.sql](queries/diario_por_campanha.sql) | Série diária por campanha (spend, cliques, vendas) |
| [pipeline_completo.sql](queries/pipeline_completo.sql) | **Os 5 blocos do diagrama numa query só** — atribuição → funil → ponte → receita → CPI/ROAS |
| [atribuicao_installs_app.sql](queries/atribuicao_installs_app.sql) | Universo atribuído: devices com `first_open` em campanha `[APP]` |
| [ponte_device_conta.sql](queries/ponte_device_conta.sql) | Ponte `id_pseudo_user → id_user` (habilita a receita) |
| [cobertura_atribuicao_por_so.sql](queries/cobertura_atribuicao_por_so.sql) | Cobertura de atribuição por SO — fact-check de "iOS sem atribuição" |
| [atribuicao_meta_por_fonte.sql](queries/atribuicao_meta_por_fonte.sql) | Atribuição por fonte — mede o buraco do Meta (`fb4a`/`ig4a`, só Android) |
| [funil_devices_meta.sql](queries/funil_devices_meta.sql) | Funil dos devices FB/IG de 14–18/08 — prova que a ponte é agnóstica de fonte |
| [inventario_telas_cadastro.sql](queries/inventario_telas_cadastro.sql) | Telas de cadastro/login — dimensiona o quanto o trio do funil subconta |

## Pendências
- [ ] Registrar achados principais da entrega original de jun/2026 (não documentados na época)
- [ ] Trocar a âncora de "conta criada" para `dim_user.dt_created_at` e remedir o funil — **erro dimensionado em 24/ago: o trio de telas cobre ~29% de quem passa por cadastro**
- [ ] Refazer a receita por `id_gateway_customer` em vez de `id_subscription`
- [ ] Acompanhar a implementação de deep link + UTM pedida ao time de Tech (doc no Notion: *[Tech] Rastreio de origem de campanha no App*)
