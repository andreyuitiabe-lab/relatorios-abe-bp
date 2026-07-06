# Teller — Análise de vendas, perfil e engajamento (2026 YTD)

## Pergunta original
Quanto vendemos de Teller por mês em 2026; qual o perfil dos compradores (membro / ex-membro / não-membro); se o Teller serve melhor para **aquisição**, **upsell** ou **recuperação**; e como está o **engajamento** de quem ouve e quem são essas pessoas.

## Decisões de abordagem
- **Duas lentes de "venda Teller", separadas** (como o produto opera):
  - **Produto Teller** — `nm_gateway_plan = 'teller'` (Teller **standalone**). Decisão do time: **NÃO** incluir premium-teller nem bundles base+Teller do Comercial (BP Select+Teller, Travessia+Teller etc.) — nesses o Teller é sweetener e o produto principal é outro.
  - **Campanha Teller** — `nm_pptc_utm_campaign` com tag `TLR`/`TLR12`; vende qualquer produto. As próprias tags separam `aquisicao`, `membros_crosssell` e `recuperacao`.
- Comparação de escopo (2026): `nm_gateway_plan='teller'` = 1.464 clientes; incluir premium-teller = 1.915; usar `nm_gateway_product LIKE '%teller%'` (com bundles) = 2.346. Escopo escolhido = **só `teller`**.
- **Perfil do comprador** classificado *no momento da compra*: membro (acesso ativo não-Teller OU vitalício anterior), ex-membro (teve assinatura, já expirada), não-membro (nunca teve). Vitalícios entram como membership permanente (têm `id_subscription IS NULL`).
- **Engajamento**: `events.fct_mixpanel__teller_media_playback_events`. Descoberta-chave: `user_id` = `dim_user.id_user` (17.713/17.714 casam) e `media_id` = `dim_teller__audiobooks.id_book` → dá pra cruzar escuta com membership e catálogo.
- Filtro padrão sempre: `nm_status='approved' AND bl_is_renovation=FALSE`.

## Achados principais
- **Volume 2026 (produto = Teller standalone):** ~1,5 mil transações, **estável ~120–400/mês** (jan e abr os picos). Receita ~R$ 320k YTD.
- **Campanha TLR/TLR12:** ~2,3 mil transações, dominadas por `aquisicao_geral`; picos de receita em mai–jun (R$ 230–250k/mês). Recuperação aparece pouco em volume mas com **ticket muito alto** (3 vendas = R$35k em fev; R$38k em mar) — winback de high-ticket.
- **Perfil dos compradores (Teller standalone, dedup por cliente — 1.464):** **48% membros (697), 32% não-membros (472), 20% ex-membros (295)**. Quase tudo digital (só ~8% via Comercial).
- **Aquisição vs upsell vs recuperação:**
  - **Upsell/cross-sell (membros):** maior fatia (48%), majoritariamente digital.
  - **Recuperação (ex-membros):** 20% do standalone; mais forte quando se olha o Comercial (bundles Premium+Teller, fora do escopo) e as campanhas `tlr_recuperacao` de alto ticket.
  - **Aquisição pura (não-membros):** 32%, MAS **só 7 de 472 não-membros (1,5%) compraram membership plena depois** → Teller **não** está funcionando como funil de entrada para o ecossistema BP. Ressalva: janela de conversão de não-membro é ~421 dias e boa parte comprou há poucos meses — reavaliar no fim de 2026.
- **Não-membros engajam, mas não sobem:** dos 472 não-membros, **87% ouviram algo e 76% ouviram em 2+ dias distintos** — audiência quente. O gargalo é ausência de rota de upgrade Teller→BP, não o produto.
- **Venda redundante (alerta):** dos 699 compradores-membros, **~236 estavam em Premium/Black** — planos que **já incluem Teller** — e o padrão **se repete todo mês** (não é resíduo de pré-inclusão). Para `good`/`supporter` (431) que querem audiolivro, o caminho de maior valor é **upsell para Premium**, não Teller avulso.
- **Teller não "pega carona" nas vendas da empresa (correlação):** vendas diárias Teller × GBB = **−0,23** (semanal −0,49); Teller × empresa = −0,14; controle GBB × empresa = +0,81. Nos maiores dias de venda da empresa o Teller vende quase nada; os picos do Teller são dias de campanha TLR própria. É **elástico à mídia própria**, levemente **contracíclico** ao push geral. (Ressalva: 6 meses; parte é competição por atenção/budget, não causalidade.)
- **Engajamento:** ~6,5–8,3 mil ouvintes/mês, estável; ~40k playbacks/mês. **82% dos compradores standalone efetivamente ouvem** (1.198/1.467) — ótima ativação.
- **Quem ouve:** dos ~17,7 mil ouvintes, **71% são membros plenos ativos**, 26% só-Teller, 3% sem assinatura ativa → Teller é hoje sobretudo um **benefício consumido por membros** (está incluído em básico/premium).
- **Conteúdo:** clássico/filosófico/católico. Top: *Críton* (Platão), *Sobre a Brevidade da Vida* (Sêneca), *Confissões* (Santo Agostinho), *Padre Brown* (Chesterton), *Revolução dos Bichos* (Orwell). Gêneros líderes: Filosofia, Religião, Ficção, Desenvolvimento Pessoal.

## Conclusão de negócio
Teller hoje é **mais retenção/upsell e reativação do que aquisição**. Gera receita incremental de membros e ex-membros (Premium+Teller do Comercial recupera ex-membros; campanhas de alto ticket recuperam winback), e tem alta ativação de escuta. Como **canal de aquisição de novos membros** o desempenho é fraco: quase nenhum não-membro sobe para membership plena (reavaliar com janela maior).

## Entregáveis
- **`index.html` + `data.json` + `refresh.py`** — relatório HTML no padrão do portal (dados externos; `python refresh.py --push` reatualiza). Card adicionado em `relatorios/index.html` (seção Base & Produtos).
- `Teller_analise_2026.xlsx` — planilha consolidada (13 abas: README, vendas produto/mês, vendas campanha/mês, perfil, canal×perfil, **tier_membros**, **retencao_nao_membros**, **correlacao_vendas**, engajamento/mês, **ouvintes_perfil**, top audiolivros, gêneros, **transações granulares**).
- `transacoes_teller_2026.csv` — transação a transação.
- `queries/analise_teller.sql` — queries A–D. `queries/export_transacoes.sql` — base granular.

## Pendências / próximos passos
- Reavaliar conversão de não-membros no fim de 2026 (janela ~421 dias).
- Medir profundidade de escuta (segundos ouvidos / % do audiolivro) — hoje medimos playbacks e ouvintes, não tempo. `vl_watch`/checkpoints não existem nesta tabela Mixpanel; avaliar `dim_teller__audiobooks.vl_duration_second` vs eventos de progresso.
- LTV do comprador Premium+Teller vs Teller standalone (não calculado).

## Wiki atualizada
- `wiki-brasil-paralelo/pages/produtos.md` — seção Teller (planos, footprint de vendas, tabelas de engajamento).
- `wiki-bp/pages/bq-planos.md` — mapeamento dos planos `-teller`.
- `wiki-bp/pages/bq-acesso.md` — tabelas `events.fct_mixpanel__teller_*` e joins (`user_id`=`id_user`, `media_id`=`id_book`).
