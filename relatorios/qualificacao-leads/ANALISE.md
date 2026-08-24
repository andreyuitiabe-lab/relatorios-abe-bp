# Análise: Qualificação de Leads — Framework CPL×CAC → IQL

**Data:** mai/2026 → jul/2026 (fase de produção)
**Status:** IQL v1 (pesos vivos) na **MR !2426** (pipeline verde, `mergeable`) — aguardando merge. **Dashboard já roda no modelo v1** (D44, 27/jul): 5 faixas A+/A/B/C/D, ELB26 monitorada, personas Fantasma/sem Reencontrado (D42–D43), visão por campanha Meta e métrica de página de obrigado (D45).
**Relatório:** [iql/index.html](iql/index.html) · **Metodologia canônica:** [METODOLOGIA-IQL.md](METODOLOGIA-IQL.md) (decisões D1–D45) · **Banco de perguntas:** [PERGUNTAS-FORMULARIO.md](PERGUNTAS-FORMULARIO.md)
**Wiki:** `~/.claude/wiki-bp/pages/iql.md` · `metricas-referencia.md` | memória: `project_lead_qualification_framework`

---

## Para retomar

**Estado:** MR !2426 **mergeada** em 31/jul (`fac983cd1`). Os 11 modelos estão em produção, distribuídos por prefixo pela macro `get_inferred_schema`: `int_` → `bp-datawarehouse.staging`, `dim_`/`fct_` → `masterdata`, `cbo_` → `datamart`. Relatório já lê produção (`DATASET = bp-datawarehouse.masterdata` — **não** `datamart`, como o plano antigo dizia). 2,91M leads escorados, versão `v1-d3245efb`, 14 tags no treino.

**Próximo passo:**
1. **Push do repo `relatorios-abe-bp`** — 4 commits locais (rename D50, documentação, cutover). Publica no GitHub Pages, incluindo a metodologia corrigida.
2. **Aposentar o protótipo**: dropar `tb_lead_iql` + `vw_lead_conversion_iql`. ⚠️ Manter `tb_iql_woe_respostas`/`tb_iql_iv_perguntas` até o `mart_iql_iv` existir — o dashboard ainda os consome.
3. **Recriar o health-check diário** apontando para `bp-datawarehouse.masterdata` (receita em `~/.claude/AGENDA.md` → Recorrentes).
4. **Avisar o Victor**: `dbt:CommitManifest` falhando na `main` desde este merge (2 tentativas), `manifest/manifest.json` com 14,5 MB, erro `curl 55` no push. O manifest do remoto está em 30/jul, então o `state:modified` do próximo MR de qualquer pessoa compara contra estado velho.
5. **Decidir a D51** (trava de maturidade por regime) — medida, não implementada.

**Wiki a carregar:** `wiki-bp/pages/iql.md` (mapa do modelo) → `dbt-status.md` → `dbt-overview.md`. Para mexer no código: `bp-dbt-dw/models/marts/marketing/iql/README.md`.

**Wiki a carregar:** `wiki-bp/pages/iql.md` (mapa do modelo) → `dbt-status.md` → `dbt-overview.md`. Para mexer no código: `bp-dbt-dw/models/marts/marketing/iql/README.md` (DAG + ordem de revisão + gotchas de CI).

**Contexto que não está em outro lugar:**
- **SQLFluff é pinado em 3.4.0** no CI (`requirements.txt`). Lintar com outra versão dá falso-verde — as regras de indentação de jinja divergem.
- Modelos incrementais têm `full_refresh=false`. Ao renomear coluna antes do merge, é preciso dropar as cópias stale em `bp-staging:docs_validation.<modelo>` e `pipeline_integrity_validation.<modelo>`, senão o CI quebra.
- Validação local usa **swap-materialization**: compilar e trocar os refs de upstream para produção antes de rodar em `bp-staging.dbt_abe`.
- Betas (`dim_iql_betas`) são **congelados**, estimados offline por `~/meu_projeto/BigQuery/iql_v0/iql_recalibra_v03.py`. Não rodam no pipeline (ver "por que" na D39).

### Operacionalização do IQL (plano de 31/jul — pedido do André)

Três frentes para colocar o modelo em prática, todas lendo `fct_lead_iql`/`cbo_lead_conversion_iql` (staging até o merge da !2426; cutover = 1 linha):

1. **Relatório IQL no marketing-bp** (time de marketing) — página nova no app (padrão das PRs #106/#110: página + hook + edge fn BQ), com (a) visão geral: leads/semana por faixa, % A+/A, CPLq; (b) por campanha: mix de faixas, CPLq vs CPL, EV acumulado; (c) personas/ICP: perfil das faixas altas em atributos legíveis (renda, tempo que conhece BP, relação com mídia, status). Linguagem de marketing: faixa + CPLq + "valor esperado por lead (R$)" — **nunca pontos/pesos (D20)**.
2. **Visão por anúncio para mídia** — mart `cbo_ads_iql_daily` (grain `id_advertising` × dia): spend/impressões do `dtm_analytics_facebook_ads_funnel` + leads por faixa via `REGEXP_EXTRACT(utm_content, r'(\d{10,})$')`. Métricas: CPL, CPLq, EV/spend, mix de faixas, taxa de resposta. Evolução do que a D45 já mostra no dashboard HTML.
3. **Send-back Meta (CAPI)** — modelo dbt `cbo_meta_capi_lead_iql` (grain lead): `event_id` surrogate (email×tag, dedup de reenvio), `event_time` = cadastro, match keys (SHA256 email, telefone E.164, `id_fbclid` — **88% de cobertura jun–jul/2026**), `value` = `vl_reference_ev`, `currency` BRL. **Métrica recomendada: EV da faixa como valor de evento único** (`LeadQualificado`) → otimização por valor no Meta; anti-Goodhart preservado (só 5 valores agregados circulam). Achado 31/jul: `js_metadata` da `lead_registration` existe mas está 100% vazio — **não há event_id de pixel**; o evento será novo, server-side, sem necessidade de dedup browser×server. Envio (script agendado vs edge fn) e criação do dataset/custom event: definir com o time de mídia. Janela CAPI = 7 dias; enviar D+1.

**Security review (Security Engineer, 07/ago) — aprovada com condições, M1 aplicada:** (M1 ✅ pré-merge) normalização E.164 tratava DDD 55 como código de país — 7,4% de match keys inválidas, 2,3k com risco de associar conversão a telefone de TERCEIRO; macro `normalize_phone_brazil_e164` + shape inválido → NULL (verificado: 0 inválidos). (B1 ✅) teste warn `rpl_date_anchored_tag_coverage` — tag com cara de campanha de data sem padrão no config (CBF20 não casa 'BF%'). (A1 🔲 **pré-requisito ANTES de conectar ponte/Data Manager**): mover os 2 feeds para dataset dedicado com IAM próprio (só a SA da ponte + conexão do Data Manager), como authorized views — mecânica já existe no repo (`custom_grant_access_to`); a SA growthbooks/dashboards não precisam dos feeds. (M2 🔲 LGPD) fbclid/gclid são dados pessoais — incluir no inventário/RoPA + retenção (NULL-ar click ids >13 meses no dtm). (M3 🔲) a ponte deve persistir log de envio (id_event, destino, timestamp, status — sem payload) p/ transparência Art. 18. (B3 ✓) D20 não violada pelo payload externo. Veredito: sem vulnerabilidade bloqueante de código.

**Protocolo do teste A/B valor × binário (desenhado 06/ago):** 1 evento (`LeadQualificado` com valor sempre), 3 braços por bid strategy — A maximizar valor · B maximizar conversões numa conversão personalizada filtrada A+/A · C controle cadastro padrão. Ferramenta A/B nativa da Meta, mesmo lançamento (com pesquisa in-funnel!), ~R$ 15–20k/braço (~4–5k leads), UTMs distintas por braço, semanas 1–2 = aprendizado (excluir da leitura, lição Lead Survey), campanha não pode ser de data. Métrica primária: RPL OBSERVADO por braço na mesma idade ÷ CPL (não depende do modelo — evita circularidade); secundárias: % A+/A, score, CPL, mix. Gates pré-registrados: A>B se retorno ≥+10% no regime estável; B>C se A+/A ≥+5pp com CPL ≤+30%; empate → binário. Decisão em D+30 pós-último lead; D+90 confirma. Se budget só p/ 2 braços: cortar C.

**Feeds de envio por plataforma (06/ago, commit 8 da MR):** `cbo_meta_capi_lead_event` (payload CAPI: id_event dedup, fbc formatado, e-mail/tel E.164, valor BRL) e `cbo_google_ads_lead_conversion` (gclid ~26% de Anúncios + enhanced conversions por e-mail/tel, datetime -03:00). 161k leads/30d, valor médio R$ 12,66. Consumo: Meta = script/Dataflow (push); Google = **Google Ads Data Manager com BigQuery como fonte nativa** (sem código) ou ClickConversionService. ⚠️ GA4↔BQ é EXPORT (GA4→BQ), não canal de envio — não serve para mandar conversões.

**Papel da âncora RIO + validação das razões entre faixas (06/ago):** com o `vl_campaign_factor`, o nível da campanha-âncora se cancela (`EV_faixa × RPL_campanha/EV_médio`) — o RIO sobrevive só no fallback D0 (0,8% dos leads) e na FORMA (razões entre faixas). Razões medidas em EVG/BP10 (D+30, vs B): ordenamento monotônico ✓ nas duas; B/C/D razoáveis; **topo achatado** — A+ realizado 8,2×/30,6× vs 2,18× da tabela (dominado por membros; tabela é NM-ancorada de propósito). Erro do lado seguro (não empurra a Meta a caçar membros). **Agenda: refit da FORMA ~nov/2026** (não precisa esperar mar/2027): rederivar múltiplos do regime novo separando NM (CAPI de prospecção; A+ NM ≈ 3,3× via D28) da base conhecida (recaptura paga deliberada = valor por cluster 481/131/46, validados). Re-ancorar o fallback D0 junto (nível atual ~R$ 9 cai no meio das projeções do regime novo, ok manter até lá).

**Validação dos EVs de tabela (06/ago):** nas 10 tags maduras (p99 ≥ 240d, sem pesquisa in-funnel) só existem 2 faixas — A+ (membros/ex, 121k) e B (NM, 869k). **B valida bem: realizado D+240 = R$ 8,12 vs tabela R$ 9,53 (−15%)**. A+ realizado = R$ 114 — 5,5× a tabela — porque a faixa é dominada pela base conhecida e a tabela é NM-ancorada (D35, topo 2% NM): por status, vitalício R$ 481,56 / membro R$ 131,20 / ex R$ 45,80 — **replica de forma independente os clusters da D31** (516/130/45). A/C/D só nascem com pesquisa in-funnel → validáveis no 1º refit (~mar/2027, EVG madura; evidência interina: backtest EVG→BP10 top decil 3,24×). Implicação CAPI em aberto: valor status-aware (membro vale 6–23× a tabela) vs NM-ancorado como está — recomendação: manter NM-ancorado e garantir exclusão da base nas campanhas de captação (otimizar ads para reencontrar membro compra o que o CRM entrega de graça).

**D+7 ancorado liberado (decisão André, 06/ago, commit 7 da MR):** o valor ancorado passa a valer já com janela D+7 completa (≥15k leads), EXCETO tags declaradas como campanha de data (`dim_rpl_date_anchored_tags` — BF%/BNO%/BPD%, mantido na criação da tag; para elas, ≥D+30). Racional: erro D+7 = 23 ≤ trava 30, calibração set/2025+ sem caso BF-like, e o risco de cauda é conhecido ex-ante pelo calendário (indetectável nos dados — refutado). Verificado: BP10/ELB26 elegíveis via d7. **Manutenção nova: registrar tag de campanha de data no config antes do lançamento** (BF25/BNO25 em nov!).

**Métrica de otimização Meta (decisão André, 06/ago): valor do evento = RPL esperado do lead → mídia trabalha com ROAS esperado.** Bid "maximizar valor" no evento `LeadQualificado` com `vl_capi_event_value` (EV da faixa no D0; × fator quando `bl_capi_value_eligible`). ROAS do Gerenciador = Σ RPL esperado ÷ spend = o retorno esperado (RPL/CPL) da página — métrica única nas duas ferramentas, meta 1,5× (D32). Valor é enviado **sempre** (EV desde o dia 0 — dentro de uma campanha o fator é constante, então o ordenamento/proporções que a Meta usa são idênticos com ou sem âncora; campanhas curtas otimizam desde o D0); binário fica só para a fase 1 do A/B. Piso de "ROAS mínimo 1,5" = evolução pós-learning, e só com nível ancorado ou intra-tag. Ressalvas registradas: ROAS do Gerenciador é *esperado* (nomear assim) e a atribuição Meta (7d clique) difere da nossa — comparar sempre dentro da mesma ferramenta. Nota: detecção precoce de campanha BF-like via razão D+1/D+7 foi **testada e refutada** (BF22 0,22 / DIR 0,17 vs normais 0,41–0,76 — sinal invertido: a venda imediata delas é do calendário, não da idade do lead), por isso o valor ancorado segue exigindo D+30.

**Implementado no dbt (06/ago — branch `feat/iql-rpl-projection-capi`, 2 commits, build 12/12 PASS em staging):** (1) `dtm_analytics_lead_conversion` ganhou `id_fbclid`/`id_gclid` (match keys CAPI; ENE: 99,6% com fbclid); (2) `dim_rpl_projector` (config-como-dado v1, 5 janelas incl. `rpl_d240` p/ tags maduras) + `cbo_campaign_rpl_estimate` (grão nm_tag, escada de estimadores, guarda-corpos de venda imediata e amostra pequena — 112 tags estimadas); (3) `cbo_lead_conversion_iql` agora carrega projeção da campanha + `vl_capi_event_value` (EV × fator, trava erro>30). Metodologia e validação: **[PROJECAO-RPL.md](PROJECAO-RPL.md)**. Falta: push + MR; recalibrar encadeamento 90→240 quando GOD/NTL25 maturarem (~set/2026).

**Modelo de valor para o CAPI (05/ago — ideia do André):** tabela `cbo_campaign_rpl_estimate` (grão `nm_tag`, diária) com a estimativa viva de RPL da campanha + erro estimado, para LEFT JOIN na hora do envio. Escada de estimadores (janela mais profunda que ≥70% dos leads completaram): D+90 ×1,69 (erro 0,15) → D+30 ×2,98 (0,10) → D+7 ×5,60 (0,18) → fallback EV IQL (0,35). Multiplicadores do **regime novo** (set/2025+, pós-tabela de vendas na confirmação — trecho 30→90 com CV 0,08); fonte canônica: `metricas-referencia.md` § Projetor de RPL. Valor do evento = `vl_reference_ev × vl_campaign_factor` (fator = projeção ÷ EV médio da tag — preserva o ordenamento por faixa, ancora o nível no observado). `pc_error_estimated` serve de trava: erro >0,30 (= fallback EV) → mandar evento binário, não valor. Rascunho SQL: `~/meu_projeto/BigQuery/sql/cbo_campaign_rpl_estimate.sql` — **⚠️ não validado no BQ ainda (auth expirou); testar com `test_estimate.sql` do scratchpad**. Achados que embasam: D+7 utilizável só no regime novo; validação out-of-window HID 19,50 proj vs 18,87 real.

**Decisão de métrica (04/ago):** a página de acompanhamento usa **retorno esperado (RPL esperado ÷ CPL, meta 1,5×)** como métrica-mestra — não CPLq. Racional do André: tudo bem captar lead ruim se ele for barato o bastante para se pagar; CPLq pune o mix sem olhar o custo. RPL esperado = Σ share_faixa × EV_faixa (fórmula D28). Mockup da aba "Aquecimento · Qualidade" (v3): artifact `a3fd60ec` — estrutura validada contra o guia de estilo do DashCampanha (abas AnimatedTabsList, KPI cards shadcn, heatmap 4 degraus emerald/amber/red, personas no formato "Perfis com maior conversão" da aba Perfil).

**Decisões do André (31/jul):** relatório vive no **marketing-bp**; CAPI começa **binário A+/A com teste A/B** (revisão dos EVs por tier fica para a fase de value optimization — usar fórmula D28 para reescalar por campanha); operação CAPI = **tabela BQ como fonte** + ponte de envio (recomendado: script agendado; alternativas: template Dataflow oficial da Meta `fbsamples/gcp-to-conversions-api-dataflow-template` ou reverse ETL SaaS).

**Auditoria marketing-bp (31/jul)** — como o app mostra ads de aquecimento hoje:
- Aba "Ads" do bloco Aquecimento em `/dashboard-campanha/:campaignName` → `src/components/dash-campanha/CampanhasAquecimentoAdsTab.tsx` (hierarquia Campanha→AdSet→Anúncio). Colunas: Criativo, Anúncio, Gasto (gross-up 1,1383), Hook, Hold, CTR, Leads, CPL, RPL, Respostas, Custo/Resp. Único proxy de qualidade = respostas de survey (CPR). **Nenhuma menção a IQL/CPLq no repo.**
- Fontes: spend/impressões vêm de **planilha Adveronix** (edge `fetch-google-sheet`), não do BQ; leads/respostas/receita vêm da edge `fetch-leads-attribution` (BQ: `lead_registration` + `dtm_analytics_lead_conversion`).
- ⚠️ **Bug encontrado:** `fetch-leads-attribution` extrai o ad_id com regex `__(\d+)$` — o padrão que **perde o BP10 inteiro** (utm_content com id puro). Corrigir para `(\d{10,})$` (gotcha documentado em `wiki-bp/pages/bq-leads.md`).
- Molde de página nova = PR #110 (edge fn + hook + página + rota) **mais** os 2 registros do PR #106 (`src/lib/systemResources.ts` → SYSTEM_PAGES; `src/components/SubHeader.tsx` → PAGE_ICONS/MENU_SECTIONS).
- Aba `perfil-leads` (`CampaignLeadProfile.tsx` + edge `fetch-campaign-lead-conversion`) já desdobra survey por pergunta/resposta com conversão — base natural para a visão de personas/ICP.

Implementação da frente 2 revisada: em vez de mart novo isolado, **estender a aba existente** — nova edge fn (ou extensão da `fetch-leads-attribution`) lendo `cbo_lead_conversion_iql` por ad_id (regex robusta) e adicionando colunas **IQL% (share A+/A), CPLq e mix de faixas** à tabela, com heatmap análogo ao do CPL. Pré-requisito: acesso da SA `growthbooks@bp-lake` ao dataset (staging `bp-staging.dbt_abe` pré-merge / `datamart` pós-merge).

**Fila do projeto (pós-merge):** (1) apresentação; (2) piloto ELB26 formalizado (gate Spearman CPLq×CAC, leitura D+60 ~set/2026; acompanhamento já no dashboard); (3) perguntas de intenção/motivação no próximo formulário (P1/P2 do [PERGUNTAS-FORMULARIO.md](PERGUNTAS-FORMULARIO.md)); (4) modelo IV no dbt (`mart_iql_iv` — hoje protótipo `tb_iql_iv_perguntas`), pré-requisito do dash de perguntas e da aposentadoria total do protótipo; (5) CAPI v2 (EV por faixa já disponível em `vl_reference_ev`); (6) **1º refit ~mar/2027** quando EVG maturar: revalidar β, reavaliar quarentena do DDD, threshold de uniformidade 2,0, ablação da `paga_conteudo`, re-medir múltiplos D28/D31 por 5 faixas (hoje aproximados A+∪A→A, C∪D→C), reavaliar promoção do "Reincidente silencioso" a persona e RFV pré-cadastro como família de atributos.

---

## Pergunta original

O time de mídia otimizava por CPL. A hipótese era que CPL e qualidade de lead são anticorrelacionados em algumas campanhas — e que falta um sistema de qualificação que funcione no momento do registro, antes da compra.

---

## Decisões de abordagem

- Comparação CPL×CAC entre campanhas (DOM vs VDS) para evidenciar o problema
- Qualificação em 3 camadas: (1) status no momento do registro, (2) dados internos dim_user, (3) pesquisa pós-registro
- Gap de cobertura: Membros/Ex-Membros têm 100% de cobertura em dim_user; Não Membros apenas 13% — para 87% dos Não Membros, o sistema interno é mudo
- Tabelas materializadas em `bp-staging.dbt_abe` para não depender de joins caros em análises futuras

---

## Achados principais

- CPL e CAC anticorrelacionam: DOM tem CPL 2,6× maior que VDS, mas CAC 6,4× maior — decisão por CPL levou a desperdício
- Lift de status: Membro converte 5–11× mais que Não Membro (consistente entre campanhas)
- 87% dos Não Membros sem cobertura em dim_user — o lead score ML atual (`dtm_lead_score_predictions_upsell_current`) foi treinado para upsell de membros, não funciona para qualificar leads de aquecimento
- Pesquisa pós-registro: renda gera lift 4,6×; intencionalidade (responder à pesquisa) já é sinal — +50% de conversão vs quem não responde
- 342k respostas normalizadas de 4 pesquisas (TLR/TPV/RIO/MST) em `tb_lead_surveys`

---

## Tabelas criadas

| Tabela | Conteúdo |
|--------|----------|
| `bp-staging.dbt_abe.tb_leads_qualification_base` | Leads jan/2025+ com status + atribuição last-click |
| `bp-staging.dbt_abe.tb_leads_qualification_enriched` | + dim_user + IBGE + renda decile + lead score ML |
| `bp-staging.dbt_abe.tb_lead_surveys` | 4 pesquisas normalizadas (342k respostas) |

---

## Análise EVG — jun/2026

**Relatório:** [2026-06-11/index.html](2026-06-11/index.html)  
**Período:** 21/mai–08/jun/2026 · 34.249 leads · 390 conversões · R$135.902 receita

### Achados EVG

- Mix: 84% Não Membros, mas Membros+Ex-Membros = 40% da receita
- Membro Ativo converte 3,64% (RPL R$14,23); Ex-Membro 2,79% (RPL R$7,68); Não Membro 0,74% (RPL R$1,85)
- Único ad set positivo: Pack 1 (+R$1,22 de folga). Pack 2 tem CPL mais baixo (R$1,84) mas pior mix de qualificados (11%)
- AD35 "alinhamento político": 30% de leads qualificados com CPL R$1,47 — melhor custo-benefício
- Survey renda: Não Membro com R$10k+ converte 4% (RPL R$9,79) — equivale a Ex-Membro
- Survey relação BP: "nunca ouvi falar" converte 0,24% vs 1% média — excluir ou orçamento mínimo
- Survey streaming: BP informal = 1,64% conv; plataformas educacionais = RPL R$5,13
- Orgânico/Portal: 980 leads, 8% conversão, RPL R$64, custo zero
- Reativação: leads >1 ano convertem 1,35% vs 0,90% de novos (+50%)

### Pendências / próximos passos

- [ ] Parte 1 (RPV): conectar GA4 MCP para comparar pageviews por variante
- [ ] Separar audiências no Meta (retargeting vs prospecting) para lançamento seguinte
- [ ] Integrar sinal de renda (survey) no fluxo de nurturing Insider no dia do cadastro
- [x] Treinar lead score específico para Não Membros em aquecimento — **IQL v0.2 implementado e backtestado (jul/2026)**: algoritmo em [ALGORITMO-IQL.md](ALGORITMO-IQL.md), metodologia + plano em [METODOLOGIA-IQL.md](METODOLOGIA-IQL.md), **dashboard em [iql/index.html](iql/index.html)**. Tabelas em `bp-staging.dbt_abe`: config (`tb_iql_de_para`, `tb_iql_pontos`, `tb_iql_cutoffs`, `tb_iql_ddd_regiao`), score (`tb_lead_iql`, 2,77M leads), monitoramento (`tb_iql_iv_perguntas`, `tb_iql_woe_respostas`) e view `vw_lead_conversion_iql`. **Backtest out-of-campaign (EVG→BP10): top decil NM captura 32,4% das vendas (lift 3,24×) vs 20,4% da v0.1**; faixas no teste A 2,36× / C 0,29× a base. Atributos v0.2 incluem identity graph (membro oculto 2,9×), região DDD e tempo_conhece. Artefatos/pesos em `~/meu_projeto/BigQuery/iql_v0/` (fora do repo público — anti-Goodhart). ⚠️ `tb_leads_qualification_base` é snapshot estático de mai/2026 — o IQL lê `dtm_analytics_lead_conversion` direto. Pendente: piloto na próxima campanha (gate: Spearman CPLq×CAC > CPL×CAC) → promoção ao dbt.
- [ ] Revisar CPL alvo por segmento com time de mídia (tabela no relatório)

### Dashboard IQL v2 — campanha-primeiro (08/jul/2026)

`iql/index.html` + `iql/refresh.py` evoluídos in-place para dashboard analítico:

- **Navegação campanha-primeiro**: uma aba por campanha (derivada de `data.json` — campanha nova aparece sozinha) + aba "Comparativo" secundária. Cada aba é o mini-dashboard da campanha: cards (leads, IQL, NM-A, cobertura da pesquisa, investimento, CPL, CPLq, NM-A/R$100), quadrante, tendência, anúncios, faixas, monotonia, IV.
- **Quadrante de decisão CPL×IQL** (SVG puro, sem libs): bolhas = anúncios (tamanho ∝ leads), zonas escalar/otimizar/cortar/matar divididas pelas **medianas da própria campanha** (nunca globais). No comparativo, scatter por cor de campanha sem zonas + aviso de não-comparabilidade.
- **Novos blocos no data.json**: `campanhas` (resumo por tag), `serie` (leads × faixa × dia, últimos 60 dias), `bandas` agora por campanha (agregação client-side no comparativo), `anuncios` ganhou `qualificados` e `investimento`.
- **Fix importante**: extração do id_ad em `utm_content` generalizada para `r'(\d{10,})$'` — o padrão antigo `r'__(\d+)$'` perdia o BP10 inteiro (48 anúncios recuperados; BP10 usa id puro, EVG usa `nome__id`). Documentado em `wiki-bp/pages/bq-leads.md`.
- Leituras dos dados atuais: BP10 IQL 38,0% vs EVG 19,5% (indicativo — coberturas de pesquisa diferentes); CPLq mediano por anúncio visível no quadrante de cada aba.

**Iteração 2 (08/jul/2026) — aba "Perguntas" + conversão/receita em tudo:**

- **Aba "Perguntas"**: ficha por pergunta da pesquisa (ordenada por IV máximo) com (a) estabilidade entre campanhas — cobertura, IV total, IV respondentes, chip de recomendação; (b) tabela de respostas — n, % da base, conversão (absoluta + %), lift vs base da tag, R$/lead. Objetivo: decidir promover/observar/aposentar/reformular cada pergunta.
- **Conversão e RPL em todas as visões**: cards da campanha ganharam "Conversão" e "R$/lead"; tabela de anúncios ganhou Conv. (absoluto + %, porque com poucas conversões o % engana) e R$/lead; monotonia (bandas) ganhou R$/lead. Aviso obrigatório por aba: "conversão/receita last-click, cohort maturando — leitura relativa, não ROI final".
- **Pipeline WOE com receita**: `iql_v0/sql/03_tb_iql_iv_perguntas.sql` agora propaga `vl_receita_atribuida` (inclusive no nível `__sem_resposta__`, derivado por diferença do total da tag) e `tb_iql_woe_respostas` ganhou coluna `rpl`. Tabelas recriadas no BigQuery.
- **Governança**: novo bloco `perguntas` no data.json exporta n/conv/lift/rpl mas **não** `woe`/`iv_contrib` (proxy dos pesos — repo público); verificação automatizada no fluxo de refresh confirma ausência.

**Iteração 3 (08/jul/2026) — reta de iso-CPLq no quadrante:**

- Fronteira de eficiência `IQL = 100·CPL/CPLq_ref` (reta pela origem), com `CPLq_ref` = CPLq **mediano** dos anúncios da campanha; clipada na área do gráfico (nos dados atuais sai pelo topo nas duas campanhas). Rótulo na ponta: "CPLq mediano R$ X — acima da linha = melhor". Só nas abas de campanha — no Comparativo não há referência comum válida.
- Tooltip dos anúncios ganhou posição relativa: "Z% melhor/pior que a mediana" = `(1 − CPLq/CPLq_ref)`. Subtítulo do gráfico explica o trade-off (CPL 2× maior é aceitável se o IQL for 2× maior; distância à reta = vantagem em custo por lead qualificado).
- Referências atuais: CPLq mediano BP10 R$ 11,54 · EVG R$ 22,44.

**Iteração 4 (10/jul/2026) — aba "ICPs" (personas para o time de conteúdo):**

- **Novo bloco `icps` no refresh.py**: segmentação mutuamente exclusiva sobre `tb_lead_iql` (NM, EVG+BP10), CASE em cascata nesta ordem: `reencontrado` (status_pessoa=membro_oculto) → `simpatizante_maduro` (tempo_conhece 6m_a_3a/mais_3a) → `pagante_de_conteudo` (paga_algum) → `curioso_frio` (primeiro_contato OU nunca_ouviu) → `neutro`. Por tag×persona: leads, % dos NM, convertidos, conv%, lift vs base NM da tag, RPL. Valores dos níveis validados contra a tabela antes de escrever o CASE.
- **Aba "ICPs" no dashboard**: escrita para o time de conteúdo — cards por persona com descrição humana, números (tamanho, conversão absoluta+%, lift colorido, R$/lead) e linha "Como falar"; Curioso Frio marcado como **anti-persona** (visual distinto). Neutro em linha discreta. Fim de cada campanha: mini-tabela "ângulos que atraíram qualificado vs frio" (top/bottom 3 por CPLq, client-side do bloco `anuncios`). Rodapé com 3 avisos: viés de seleção (perfis descrevem quem os anúncios atuais alcançam), traços de pesquisa só observáveis pós-cadastro (mirar via lookalike faixa A + geo + self-selection do criativo), last-click/cohort maturando.
- **Achados**: Reencontrado converte 2,8–3,7× o NM médio (EVG RPL R$ 13,06/lead vs R$ 1,87 do neutro); Simpatizante Maduro 1,8–2,1×; Curioso Frio 0,17–0,5× (no BP10 é 25,9% da base com conv 0,087% — o brinde atrai frio em massa).

**Iteração 5 (10/jul/2026) — dashboard v3: decomposição, perfis por anúncio, confiança estatística e pacote UX:**

- **refresh.py, 3 blocos novos + governança**: (1) `impacto` — contribuição por atributo via join níveis×`tb_iql_pontos` feito no SQL, mas **pontos ficam só na memória do processo**: o data.json recebe apenas `share_pct` relativo (importância da campanha = share do desvio-padrão da contribuição; por anúncio = share do desvio vs média da campanha, com sinal), fato de mix público por atributo (nível com maior desvio em p.p.: `nivel`, `pct_ad`, `pct_camp`) e flag `bl_tipico` (desvio total <2 pontos → UI mostra "próximo da média" em vez de barras sem significado); (2) `perfil_status` — traços públicos por status (respondeu, paga, recadastro, tempo_conhece, região DDD); (3) `perfil_anuncios` — mix de status e de personas (cascata ICP) por anúncio ≥50 leads. Assert de governança no próprio refresh: nenhuma chave de pontos/woe pode entrar no data.json (checagem por chave JSON, não por prosa — o 1º assert deu falso positivo com "pontos univariados" do texto do backtest). `anuncios` ganhou `id_ad` (liga quadrante↔tabela↔painéis). Config `CPLQ_ALVO` por tag (vazio até o negócio definir).
- **index.html reescrito (v3)**, aba de campanha com sub-nav sticky **Decidir/Perfis/Modelo**:
  - *Decidir*: bloco "Ações da campanha" (top/bottom 3 por CPLq, migrado da aba Personas) no topo; 5 cards primários com **delta 7d vs 7d anteriores** (leads e IQL — únicos com série diária; CPLq/investimento sem delta por falta de spend diário no data.json); quadrante com **reta de alvo de CPLq** (input do usuário, persiste em localStorage por tag; default futuro via `CPLQ_ALVO`), rótulos das medianas ancorados nos eixos e rótulo da iso-CPLq no meio da reta com fundo (fix da colisão com "OTIMIZAR CRIATIVO"), rótulo curto nos 5 anúncios de maior investimento, clique na bolha/linha seleciona (destaca e alimenta a lupa); tabela com busca + filtro por zona + títulos-tooltip; em <700px o quadrante vira lista de decisão.
  - *Perfis*: "Anúncio sob a lupa" — seletor único alimentando (a) decomposição do desvio do score em barras divergentes com fato de mix por atributo e (b) "quem o anúncio traz" (mix de status e personas vs campanha, barras pareadas) com **veredito automático** guardado contra ruído (só afirma persona com share ≥5%, ≥15 leads e desvio ≥1,5×/≤0,67×; senão "mix próximo da média"); "Perfil por tipo de pessoa" (status × traços).
  - *Modelo*: "O que move o score" (importância por atributo); **"IQL previu × aconteceu"** — terços de leads por IQL com conversão observada ±IC e R$/lead (leitura: terço alto deve converter mais; senão, recalibração) + Spearman IQL×conv% (anúncios ≥5 vendas); Tendência (com linha de % faixa A no eixo direito), Validação e Monotonia colapsadas em `<details>`; IV removido da aba (link para Perguntas).
  - **Camada de confiança** (client-side, IC 95% de Wilson, util único): semáforo ●/◐/○ sem jargão — coluna "Conf." na tabela (IC vs mediana do IQL; <80 leads rebaixa), bolhas tracejadas quando inconclusivas + whisker no hover, conversão nunca em % com <5 vendas ("○ N vendas"; 5–15 ◐; >15 ●, regra única também para RPL e Perguntas), coluna IC em faixas/bandas/terços, badge de amostra nos cards de persona (<30 conversões).
  - Comparativo: scatter misto substituído por **small multiples** (mini-quadrante por campanha, cada um com as próprias medianas — o gráfico misto induzia a comparação que a nota proíbe). Aba ICPs renomeada **Personas**. Header com frase de tese. Fix do sort (numéricas abrem descendente; CPL/CPLq ascendente). Robustez: localStorage pode existir e estar indisponível → wrapper try/catch.
- **Verificação**: node --check; cross-check de todos os campos JS×data.json (11 blocos + impacto); smoke Node das 5 abas com asserts (8 barras divergentes + 8 fatos de mix na lupa, 35 células "○ poucas vendas" no BP10 = exatamente os 35 anúncios com <5 conversões, 131 chips de confiança, 12 células de IC, reta de alvo aparece ao definir CPLq alvo); headless Chrome desktop 1280px e mobile (mínimo real da ferramenta é 500px — `--window-size=390` reporta `innerWidth=500`; o "overflow" dos screenshots era artefato disso; a 500px sem overflow e a auditoria de CSS não tem larguras fixas >310px fora de containers com scroll). Governança confirmada no data.json final.
- **Decisões de visualização**: scatter opcional do previu×aconteceu omitido (terços + Spearman entregam a leitura sem poluir); deltas 7d só onde a série diária permite; decomposição por anúncio fica na Lupa (Perfis) e a importância da campanha no Modelo — um seletor só para "por quê" + "quem".

**Iteração 6 (10/jul/2026) — régua de CPL máximo por terço ("escalar ou parar"):**

- **refresh.py**: constante `FATOR_MATURACAO = {30:1.90, 60:1.43, 90:1.25, 240:1.0}` — RPL(D+240)÷RPL(D+X), mediana de 10 campanhas 2025 (fonte `scratchpad/maturacao.csv`, GDC excluída por degenerada); **validada contra o CSV antes de gravar** (medianas batem; p25–p75 em D+30 = 1,66–2,36). Interpolação linear; idade <30d usa fator de D+30 (conservador). Novo campo por campanha: `idade_media_dias` (cohort NM) + `fator_maturacao` aplicado em Python. Config `META_ROAS = 1.5` publicada como `meta_roas`.
- **UI (tabela dos terços)**: novas linhas — R$/lead projetado (maturado), CPL máximo (break-even = projetado), CPL máximo (meta N×, input editável com persistência por campanha como o CPLq alvo) e linha **Veredito** com chip 🚀 escalar / ⚠️ segurar / ⛔ parar (CPL atual vs máx-com-meta e break-even). Linha informativa da cohort (idade + fator + aviso de conservador) e nota obrigatória: break-even sobre receita BRUTA last-click, meta é a folga para margem/incrementalidade. Tooltip do quadrante ganhou "CPL máx estimado" só para anúncios com ≥5 vendas (RPL próprio × fator ÷ meta).
- **Leitura atual (BP10, fator 1,90, meta 1,5×)**: terço IQL alto CPL R$4,30 vs máx R$10,52 → 🚀 escalar; médio → ⚠️ segurar; baixo CPL R$5,40 acima do break-even R$3,84 → ⛔ parar. Ambas as cohorts <30d (10,7d e 18,1d) → fator conservador.

**Iteração 7 (14/jul/2026) — RPL esperado e CPL alvo POR ANÚNCIO (D28):**

- **refresh.py**: constante `MULT_VALOR = {nao_nm: 11.0, nm_a: 3.3, nm_b: 1.05, nm_c: 0.83}` — múltiplos de R$/lead maduro vs NM médio da campanha, receita realizada pooled RIO/MST/TPV (fontes verificadas: `iql_v0/sql/07_backtest_rio_mst_tpv.sql` + decisão D28 na METODOLOGIA, incl. ressalva do A largo). Bloco `anuncios` ganhou `nm_b`, `nm_c`, `n_nao_nm` (validado: A+B+C+não-NM = leads em todos os 140 anúncios); `campanhas` ganhou `rpl_nm_observado` (base da projeção). `bq()` ganhou retry (falha transiente pegou o bloco impacto).
- **UI**: colunas **"RPL esp."** (base NM projetada por maturação × mix do anúncio × múltiplos) e **"CPL alvo"** (RPL esperado ÷ meta, chip verde/vermelho vs CPL atual, recalcula ao editar a meta) na tabela de anúncios, ordenáveis; card "RPL esperado" da campanha (mix total); nota explicando esperado ("o que o mix DEVE render") vs observado ("o que já apareceu"). **Decisão**: a linha "CPL máx estimado" do tooltip (RPL próprio, exigia ≥5 vendas) foi **substituída** por "CPL alvo (RPL esperado)" — mix-based é mais estável e cobre todos os anúncios.
- **Verificação**: conferência numérica independente bate ao centavo (AD15 EVG: R$16,48 = base 4,85 × mix 3,40); EVG: 84 anúncios compráveis / 8 acima do alvo; RPL esperado da campanha EVG R$11,81 · BP10 R$7,90. Governança ok (múltiplos e mixes são públicos; sem pontos).
- **Leitura**: os alvos são puxados pelo múltiplo 11× da recaptura — anúncio com muito não-NM tem CPL alvo alto por design (o guardrail continua sendo NM-A/R$100 para não "melhorar" recapturando membro).

**Iteração 8 (16/jul/2026) — "CPL × RPL projetado: o plano do dinheiro":**

- **Novo scatter no grupo Decidir** (após o quadrante, que fica como lente de qualidade): x = CPL atual, y = RPL esperado maturado (mesmo cálculo da coluna "RPL esp."). Duas diagonais pela origem — break-even bruto (RPL=CPL, linha clara) e meta N× (linha accent, mesmo input META_ROAS) — com 3 zonas nomeadas (lucro projetado com folga / acima do break-even, abaixo da meta / prejuízo projetado). Bolhas coloridas pela zona do dinheiro, tracejadas/opacas pela confiança (padrão do quadrante), rótulos nos top-5 por investimento; mobile vira lista ordenada por ROAS. Tooltip único ganhou "ROAS projetado" e folga em R$/lead. Editar a meta re-renderiza gráfico + tabela + terços.
- **Tabela de anúncios**: coluna ordenável "ROAS proj." com semáforo (≥meta verde, 1–meta âmbar, <1 vermelho). **Cards**: "ROAS projetado" virou card primário (RPL esp ÷ CPL). **Comparativo**: colunas RPL esp. e ROAS proj. na tabela-resumo.
- **Nota obrigatória**: projeção não é realizado (incerteza da base ±25–40%; diagonais em receita BRUTA; realizado em "IQL previu × aconteceu").
- **Verificação**: EVG ROAS projetado 3,34× (expectativa ~3,3× ✓); **BP10 deu 1,33×, não os ~1,7× esperados** (CPL atual R$5,96 — a expectativa estava defasada). Zonas EVG conferidas contra o SVG: 84 lucro / 7 meio / 1 prejuízo = 84 verdes / 7 amarelas / 1 vermelha. Screenshot desktop validou zonas, diagonais e rótulos.

**Iteração 9 (17/jul/2026) — seção "Forecast de receita" no grupo Modelo (D31):**

- **refresh.py**: constante `CLUSTER_VALOR` (D31, cohorts maduras RIO/MST/TPV 2025) — 6 clusters com valor maduro (status: RPL absoluto de referência; NM A/B/C: múltiplo × base NM da campanha, a mesma do RPL esperado D28) e curva de maturação própria `m30/m60/m180` (NM/Ex rápidas 43–48% até D+30; Membro 12,8% / Vitalício 17,1% — compram no evento seguinte). Publicada como `cluster_valor`. Novo bloco `receita_semanal`: SUM(vl_payment_gross) por bucket semanal de `days_to_purchase` (dtm_analytics_lead_conversion, UNNEST do array de transações), **restrita à população escorada em tb_lead_iql** (join email×tag com o mesmo dedup) — descoberto que sem o join a curva estoura o corredor: `tb_lead_iql` estava congelada em 08/07 (scheduled query não rodou) e o BP10 tinha 2× mais leads no dtm; com o join, numerador e denominador defasam juntos. Contagens por cluster NÃO duplicadas no data.json — derivadas client-side de `perfil_status` (status) e `faixas` (NM A/B/C).
- **index.html**: seção entre "O que move o score" e "IQL previu × aconteceu". (a) número-título: receita final projetada + faixa (incerteza ±40% se idade da cohort <30d, ±25% depois — D29) + cards realizado/corredor na idade atual; (b) veredito automático dentro/acima/abaixo do corredor; (c) decomposição por cluster (leads, valor/lead maduro, receita projetada, % esperado na idade — interpolação linear de M_c com 0 em t=0 e 1,0 em D+240, mesmo horizonte do fator de maturação — vs % observado = rpl÷valor maduro) com leitura-chave fixa: a cauda da projeção é dos membros por desenho, não atraso; (d) SVG do realizado acumulado semanal vs corredor projetado (banda ±25/40%, linha central tracejada, marcador "hoje"); mobile (<700px) troca o gráfico por lista (padrão decide/money-list); notas: receita bruta last-click, curvas de cohorts 2025 (D31), projeção ≠ compromisso.
- **Verificação**: `refresh.py` sem erro + assert de governança ok (cluster_valor não tem chaves de pontos/woe); node --check; smoke Node das 5 abas (posição da seção no grupo Modelo antes do previu×aconteceu, 6 clusters na tabela, SVG, lista mobile, notas); **conferência manual EVG em Python independente do JS bate ao centavo** (total R$ 2.983.219,25; corredor D+25,1 R$ 720.013,32); cross-check dos 19 blocos `D.*` referenciados no JS × data.json; servidor local + curl 200.
- **Leitura (17/jul)**: **EVG projeta R$ 2,98 mi** (faixa 1,79–4,18 mi; ±40%, cohort 25,1d) — 40% da projeção é Membro Ativo (9,2k leads × R$129,62); realizado R$ 932k vs corredor R$ 720k = dentro da banda, colado no teto. **BP10 projeta R$ 1,44 mi** (faixa 0,86–2,01 mi; cohort 17,7d) — 85% da projeção é Vitalício+Membro (1,2k vitalícios!); realizado R$ 368k = **2,3× o corredor central, acima da banda** — membros desta campanha realizam muito mais rápido que as cohorts 2025 (Vitalício já entregou 22% do valor maduro vs 10% esperado): projeção provavelmente conservadora; caso claro para o M(t) por fase estrutural/mix da v0.3 (D30).
- **Fora do escopo, sinalizado**: a scheduled query que recria `tb_lead_iql` não roda desde 08/07 — o dashboard inteiro lê o snapshot; reescorar atualiza tudo (não foi feito nesta sessão).

## Fase de produção — IQL no dbt (20–27/jul/2026)

O protótipo (`tb_lead_iql`, scheduled query) virou modelo dbt versionado. Detalhe técnico completo:
[README dos modelos](../../../bp-dbt-dw/models/marts/marketing/iql/README.md) · decisões: METODOLOGIA §7 (D35–D41).

**Arquitetura entregue (MR !2426)** — 6 modelos + 5 configs + 2 testes + 1 macro:

| Camada | Modelos |
|---|---|
| Níveis | `int_iql_lead_levels` (grão e-mail×tag; status direto do dtm) |
| Pesos vivos | `int_iql_woe_live` → `fct_iql_weights` (versionado, append-only, gate no insert) |
| Score | `fct_lead_iql` → `cbo_lead_conversion_iql` (consumo) + `fct_lead_iql_history` (auditoria) |
| Config | `dim_iql_mapping` · `_betas` · `_woe_bootstrap` · `_cutoffs` · `_ddd_region` |
| Testes | `iql_weights_sanity` (warn) · `iql_missing_weight_levels` (error) |

**A mudança de arquitetura (D39 — "pesos vivos")**: o WOE de cada resposta passou a ser **recalculado pelo próprio pipeline** a partir das campanhas maduras, congelado por evento de safra (`cd_version` = hash do conjunto de treino). A única manutenção humana que sobrou é o **de-para**. Motivador: pedido explícito de "recalcular o valor de cada resposta sem rodar script e subir MR".

**Três revisões independentes, todas aplicadas:**

1. **Model QA (metodologia)** — aprovado com 5 condições. Achados críticos confirmados no BQ: **leakage do `cd_contact_phone`** (preenchido na compra: conv 17–25% quando presente vs 0,05% — vazava o alvo para o atributo de DDD) e **trava de maturidade por `MAX(dt)` descartava 78% das conversões maduras** (stragglers seguravam RIO/ODD/MST fora do treino por 13 meses) → trocada por `p99 ≤ hoje−240d`.
2. **Revisão sênior de código** — gate de sanidade movido para **dentro do INSERT** (antes o teste rodava depois da materialização: versão ruim já persistida + deadlock diário); `NOT IN`→`NOT EXISTS`; `full_refresh=false` nas trilhas de auditoria.
3. **`/review` com 8 finders** — gate `delta_safra` com `LEFT JOIN` + teto para nível novo; precedência multi-select; macro `iql_attributes()` como fonte única; constantes → `vars DBT_IQL_*`. Refutados na verificação: regex de DDD (backtracking resolve DDD 55) e fanout do cbo (dtm tem grão único).

**Simplificações medidas (D41)**: status passou a vir do `st_member_status_at_registration` do dtm — bate 1:1 com a derivação por `dim_subscriptions` e **conserta o viés retroativo** do `dt_expires_in`. **Membro oculto descontinuado** (revoga D37): dropar não move a conversão do NM (3,807% → 3,807%), custo = subvalorizar 55k leads (1,9%) que convertem 8%; em troca, sai o identity graph inteiro do modelo.

**Estado numérico atual** (staging, versão `v1-d3245efb`, 13 tags no treino): âncoras monotônicas (membro_ativo +40 > vitalício +27 > ex +23 > NM −11); faixas nos NM in-funnel = A+ 1,9% / A 12,7% / B 30,9% / C 40,7% / D 13,9%; cortes v1 = A+ ≥6 / A ≥−7 / B ≥−24 / C ≥−32. **Atributos de pesquisa rodam 100% no prior de bootstrap** (nenhuma tag madura tem pesquisa in-funnel) — o auto-recálculo deles começa quando o EVG maturar, ~mar/2027.

**Governança**: pesos não circulam para quem opera campanha (D20, anti-Goodhart); `cd_scorecard_version` em toda linha; histórico incremental como trilha.

---

## Queries

| Arquivo | O que faz |
|---------|-----------|
| [queries/leads_com_status_e_cobertura.sql](queries/leads_com_status_e_cobertura.sql) | Status + cobertura dim_user por campanha |
| [queries/cpl_vs_cac_por_campanha.sql](queries/cpl_vs_cac_por_campanha.sql) | Leads e compradores por campanha (requer custo externo para calcular CPL/CAC) |
| [queries/06_cpl_por_tipo_lead_evg.sql](queries/06_cpl_por_tipo_lead_evg.sql) ✅ | CPL×RPL por anúncio × tipo de lead — EVG · jun/2026 |
| [queries/07_recencia_frequencia_cadastro.sql](queries/07_recencia_frequencia_cadastro.sql) ✅ | Conversão por recência/frequência de cadastro × status — cohort 2025 · jul/2026 (feature IQL) |

## Wiki atualizada

- `wiki-bp/pages/iql.md` — **página do modelo** (mapa, tabelas, rotinas, onde puxar dados) — jul/2026
- `wiki-bp/pages/dbt-status.md` — estado da branch/MR do IQL
- `memory/project_lead_qualification_framework.md` — framework e tabelas documentados
- `wiki-bp/pages/metricas-referencia.md` — benchmarks CPL×CAC por campanha
---

## Checklist de revisão

- [ ] Filtros padrão aplicados: `nm_status = 'approved'`, `bl_is_renovation = FALSE`
- [ ] Exclusões obrigatórias para o tipo de análise (ver `regras-negocio.md`)
- [ ] Resultados batem com benchmarks em `metricas-referencia.md` ou desvio explicado
- [ ] Método de atribuição de campanha correto (UTM vs lead_last_tracking — ver `bq-regras.md`)
- [ ] Métrica principal é a correta para o contexto (não CPL quando deveria ser CAC, etc.)
- [ ] Canal separado onde relevante (Comercial vs Digital)

---

## Organização da pasta (jul/2026)

- `index.html` — relatório do framework CPL×CAC (visão geral do tema)
- `evg-bp10-pesquisa/` — **versão viva** da análise de pesquisa de qualificação (EVG × BP10)
- `2026-06-19-v3/` — snapshot EVG v3 apresentado a stakeholders (URL compartilhada — não mover)
- `archive/` — iterações supersedidas (2026-06-10 a -12-v2), fora do portal
- `modelo_evg_bp10/` — artefatos do modelo ML (dataset, benchmark, scripts)

Regra: versão viva evolui in-place (git é o histórico); snapshots de apresentação vão para `archive/` e não ganham card no portal.
