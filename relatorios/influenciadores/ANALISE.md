# Análise — Ranking de Influenciadores por Vendas

## Pergunta original

Pedido da Thais Schönerwald (time de influenciadores, Slack 21/07/2026): *"puxar os
influenciadores que mais venderam BP, para ter noção do ranking — quanto vendeu e o que vendeu"*.
Contexto adicional: o dash antigo (segmento Insider "Influ: venda direta e indireta") usava
canal contém "Influ" OU last tracking contém "PARC" excluindo utm_medium "ads"; existem também
vendas de anúncios de tráfego pago com criativos de influs, marcadas nas UTMs.

## Decisões de abordagem

- **Base:** `fct_transactions`, aprovadas, sem renovação. **Recorte: jan/2025 em diante**
  (pedido do André em 21/07 — a primeira versão era o histórico completo 2020–2026; os números
  históricos ficaram registrados na wiki `influenciadores.md`). Granularidade mensal.
- **Três categorias, mutuamente exclusivas:**
  1. **Venda direta** — `nm_pptc_tracking_publisher = 'Influencers'` (classificação de canal da
     própria base, mais completa que a regra do print) + trackings `Afiliado - <nome>` do programa
     de afiliados 2020–21 (que têm publisher variado e ficariam de fora).
  2. **Anúncios com criativo de influ** — `utm_content`/`utm_campaign` contém `influ`
     (excluindo "sem influs" e o criativo temático "VVS influencia" da campanha Banco Master,
     que fala de *influência*, não é influenciador).
  3. **Venda indireta** — replica a regra PARC do dash antigo: `nm_lead_last_tracking` contém
     INFLU/PARC, compra não veio de ads nem do canal Influencers.
- **Nome do influenciador não existe como coluna** — é extraído por regex do
  `nm_pptc_tracking_name` / `nm_utm_source` (direto) e do `nm_pptc_utm_content` (ads).
  Mapa de ~40 regexes + parser genérico de sufixo `| nome` e `Afiliado - nome`; variações de
  grafia unificadas (ex: "alam carriom" → Alam Carrion, "lara brener" → Lara Brenner).
- Por que não usar só a regra do print: ela roda sobre o `[2023] Canais` do Insider (só INFLUS/
  PARCEIROS no last tracking) e perde os afiliados 2020–21 e todos os anúncios com criativo de influ.

## Achados principais (recorte 2025 → hoje)

- **R$ 9,7 mi de receita atribuída a influs desde jan/2025** (~53 mil vendas): R$ 8,2 mi (84%)
  de anúncios com criativo de influ, R$ 591 mil venda direta por link, R$ 942 mil venda indireta.
- **O canal hoje é essencialmente criativo de influ em mídia paga.** Top: **Alam Carrion
  (R$ 1,15 mi)**, Brexplora (R$ 415 mil), Lucca Almeida (R$ 389 mil), Sikêra Jr (R$ 379 mil),
  Arthur Schreiber (R$ 367 mil), Tiba Camargo (R$ 352 mil), Yago Martins (R$ 326 mil).
  Campanhas que mais usaram: Oficina do Diabo (2025) e Clube do Livro (2026).
- **Venda direta por link encolheu** (R$ 591 mil no período): Pânico R$ 108 mil, Ticaracaticast
  R$ 49 mil, 4x4 Podcast R$ 21 mil.
- **⚠️ R$ 397 mil (67% da venda direta do período) vieram de links genéricos de parceria** que não
  identificam o influ individual — mesmo problema visto na análise CDL de jul/2026. Recomendação
  operacional: todo influ deve ter link/UTM próprio.
- **Por campanha** (seção própria no relatório): Oficina do Diabo 2025 é disparado a maior
  (R$ 3,7 mi — Alam Carrion, Tiba Camargo, Yago Martins), depois Clube do Livro 2026 (R$ 1,3 mi —
  Arthur Schreiber, Tamie Tominaga, Lu Ruiz), Teller 2025 (R$ 1,1 mi — Lucca Almeida, Lara Brenner)
  e Rio de Janeiro 2025 (R$ 705 mil — Brexplora, Sikêra Jr).
- Contexto histórico (2020–2026 completo, registrado na wiki): total R$ 19,7 mi; o auge da venda
  direta foi 2022 com o grupo Jovem Pan (Pânico R$ 3,0 mi histórico, BF22 via QR code R$ 893 mil).

## Pendências / próximos passos

- Publicar no portal (card em `relatorios/index.html`, seção Campanhas & Leads) — aguardando OK.
- Se o time quiser ROI por influ, falta o custo (fee de cada parceria) — não existe na base.
- Cauda longa dos criativos de ads (~460 nomes) pode ter grafias não unificadas.

## Queries

| Query | O que faz |
|-------|-----------|
| [influs_direto.sql](queries/influs_direto.sql) | Vendas por link de influ (publisher Influencers + Afiliados) |
| [influs_indireto.sql](queries/influs_indireto.sql) | Lead veio de parceiro, compra por outro canal (regra PARC do dash antigo) |
| [influs_ads.sql](queries/influs_ads.sql) | Anúncios pagos com criativo de influ (VVS) |

## Wiki atualizada

- `wiki-bp/pages/bq-schema-core.md` — documentadas `nm_pptc_tracking_publisher`, `nm_pptc_tracking_name`, `nm_pptc_utm_content`, `nm_utm_source`
- `wiki-brasil-paralelo/pages/influenciadores.md` — criada com achados e como medir vendas de influs
