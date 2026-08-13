# Análise — Campanha Odisseia como um todo (13/ago/2026)

## Pergunta original

"Como está a campanha da Odisseia como um todo? CRM (disparos de WhatsApp/e-mail, o que está funcionando, KPIs), ads (métricas, retorno, volumetria), como isso chega no Comercial — e como vender mais." (André, 13/08/2026, via /data-analyst.)

Metas verificáveis: (a) volumetria e receita por canal de CRM + peças que vendem; (b) spend/CTR/CPM/ROAS por campanha de ads; (c) split da receita por origem de último clique, incluindo a última sessão antes das vendas comerciais; (d) recomendações acionáveis de crescimento com base nos números.

## Decisões de abordagem

- **Âncora de receita = `fct_transactions`** (R$ 2,36M): os cortes por origem usam o último clique da transação (`nm_pptc_tracking_publisher` + `nm_pptc_utm_medium`) e somam 100% sem dupla contagem. As visões de plataforma (Insider, Meta) usam a atribuição de cada modelo e **se sobrepõem** — nunca somar CRM + ads + fct.
- **CRM**: `dtm_analytics_revenue_insider_funnel` com `nm_campaign_tag='ODI'` (⚠️ a wiki dizia `ODD`; o dado real usa `ODI` — wiki corrigida).
- **Ads**: `dtm_analytics_facebook/google/pmax_ads_funnel`, campanhas `[ODI]`/`ODISSEIA`.
- **Comercial**: menções na transcrição Zenvia (método validado no `odisseia-lancamento`) + última sessão UTM das vendas comerciais.
- Janela: campanha inteira (spend desde 03/07, venda desde 17/07) até ontem; `refresh.py` atualiza tudo.

## Achados principais (17/07–12/08)

1. **Placar**: 1.953 vendas / R$ 2,36M (ticket R$ 1.206). Digital 70% da receita (R$ 1,65M), Comercial 30% (R$ 704k). Spend total de ads R$ 945k → retorno geral 2,49× (receita total ÷ spend).
2. **Origem digital (último clique)**: Ads Meta R$ 954k (58% do digital), CRM e-mail R$ 332k, CRM WhatsApp R$ 196k, Google/PMax R$ 48k, orgânico R$ 52k.
3. **O funil é integrado**: 49% das vendas do Comercial (297/602) chegam ao vendedor com clique em mídia paga na última sessão; CRM responde por mais ~26%. A mídia aquece os dois canais.
4. **CRM — WhatsApp rende ~24× mais por mensagem que o e-mail**: R$ 977/1k entregues vs R$ 41/1k — mas recebeu só 0,8% do volume (108k vs 13,6M). A peça top geral é WhatsApp (WA02 "Clistenes feliz": 31,6k msgs → R$ 45k, R$ 1.411/1k). No e-mail (68 peças, click rate ~0,21%), vendem as narrativas de curiosidade ("a cena que não foi para o filme de Nolan", "o perigo das sereias"), não oferta direta. Push: 2,6M entregues, R$ 0 direto (telemetria quebrada — gotcha conhecido da base).
5. **Ads — quente ≫ frio**: Membros CDL ROAS 4,66 (só R$ 4,7k de spend), PMax 3,90 (R$ 24k), "Só vídeos" 2,17 — contra 0,99–1,46 dos packs Advantage frios, que concentram 92% do budget. ROAS Meta agregado 1,40, **abaixo do gate de escala (1,5×)**. CPM R$ 23,64, CTR 2,0%, CPA R$ 793. Nos packs, ~1 em 4 vendas atribuídas fecha via Comercial.
6. **Leads**: captação começou só em 08/08 (2.253 leads, 92% Facebook), sem campanha [LEAD] — a campanha rodou 100% mídia [VENDA] direto ao checkout.
7. **Comercial**: 3.876 conversas mencionando a Odisseia no período → 602 vendas (~15,5%/conversa, a melhor taxa do portfólio), em ondas (picos fim de julho via carteira Mecenas, esvaziamento em agosto).

## Recomendações (seção "Como vender mais" do relatório)

1. **Escalar WhatsApp no CRM** — 24× a receita/mensagem do e-mail; listas quentes já entregues (reoferta ago/2026: 75,3k contatos; P1 clicantes com taxa observada 4,6%).
2. **Realocar mídia do frio para o quente** — escalar Membros CDL (4,7×), PMax (3,9×) e "Só vídeos" (2,2×); cortar Pack 5 (0,99×).
3. **Constância na oferta do Comercial** — lista dedicada (P1) + meta por vendedor; conversão/conversa já é a melhor do portfólio.
4. **E-mail: menos peças, mais dos ângulos vencedores** — reduzir fadiga da base.
5. **Push: consertar telemetria antes de escalar.**
6. **Leads: medir conversão da primeira safra antes de investir em captação.**

## Pendências / próximos passos

- Se as recomendações forem acatadas: acompanhar ROAS pós-realocação e receita/1k das ondas de WhatsApp pelas visões deste relatório (rodar `refresh.py`).
- Vendas "Sem UTM" (~R$ 130k) — se ganhar materialidade, investigar checkout direto vs perda de parâmetro.
- CPA por campanha considera atribuição Meta; para decisão fina de budget usar o recomendador de mídia (midia-paga).

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/funil_origem.sql](queries/funil_origem.sql) | Vendas por dia/canal + origem por último clique (digital e comercial) |
| [queries/crm_insider.sql](queries/crm_insider.sql) | CRM Insider tag ODI: diário por canal + top peças |
| [queries/ads_funnels.sql](queries/ads_funnels.sql) | Meta por dia + Meta/Google/PMax por campanha com ROAS |
| [queries/leads_mencoes.sql](queries/leads_mencoes.sql) | Leads por dia/fonte + menções Odisseia no Zenvia |

## Wiki atualizada

- `wiki-bp/meta-insider-ads.md` — tag Insider da Odisseia corrigida (`ODD` → `ODI` nos dados reais)
- `wiki-bp/bq-planos.md` — §Odisseia: leads só desde 08/08; mídia [VENDA] desde 03/07 (sem [LEAD])
- `wiki-brasil-paralelo/odisseia.md` — criada: página temática consolidando achados da campanha

## Artifact

Snapshot de 13/08 publicado como artifact (privado, compartilhável): `https://claude.ai/code/artifact/8178a599-5d6b-4778-a23f-c8e3087cda6b` — versão self-contained (SVG estático, temas claro/escuro). A versão viva é a do portal (esta pasta, via `refresh.py`).

## Relação com outros relatórios

- `odisseia-lancamento/` — comparativo estrutural vs CDL (D1–Dn alinhados)
- `comercial-abordagens/` — pulso operacional do canal Comercial (últimos 14 dias)
- `odisseia/` — SSR pré-lançamento (recomendação de faseamento)
