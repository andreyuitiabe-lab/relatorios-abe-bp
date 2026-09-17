# Base analítica de vídeos do canal (criada 16/09/2026)

**Arquivo:** `data/yt_base_videos.csv` — 2.806 uploads desde 01/08/2025, 2.788 com métricas da
Analytics API (lifetime até 14/09). **Script:** `BigQuery/youtube-analytics/classificar_videos.py`
(reexecutar após `fetch_youtube_public.py`).

## Regras de classificação (v1 — para validar com Bárbara / conteúdo)

| Camada | Tipo | Regra | Papel na análise |
|---|---|---|---|
| **PROGRAMA** | live | `liveStreamingDetails` presente e > 60 s | unidade de análise: 1 programa = 1 evento |
| PROGRAMA | longo | > 25 min, não live | idem |
| PROGRAMA | médio | 10–25 min, não live | idem (rever: parte pode ser corte longo) |
| **DERIVADO** | corte | 1–10 min | alcance do programa de origem, não evento |
| DERIVADO | short | ≤ 60 s | idem |
| **RUÍDO** | institucional | título com "já disponível", "novo documentário", "apresenta resumo", "lança", "trailer", "teaser", "box inédito", "compila" | fora |

Série (só PROGRAMA), por regex no título: Rasta News · BP nas Eleições · BP Entrevista · Live/react
de notícia (`AO VIVO`, `REACT`) · Documentário completo · Aparição TV · Investigação Paralela ·
BPeiro · 10 anos do Impeachment. **729 dos 849 programas ficaram "Avulso"** — a nomenclatura de
título não carrega a série; precisa de lista do time de conteúdo (ou playlists do canal via Data
API, `playlists.list`, ainda não puxadas).

## O que a base mostra (ago/2025 → set/2026)

| Camada | Vídeos | % views | % minutos | % inscritos ganhos | views mediana | % assistido |
|---|---:|---:|---:|---:|---:|---:|
| Programa live | 581 (21%) | 41% | **82%** | **76%** | 68.520 | 38% |
| Programa médio/longo | 268 (10%) | 7% | 10% | 8% | 12–23 mil | 30–37% |
| Corte | 1.230 (44%) | 18% | 4% | 7% | 11.497 | 52% |
| Short | 682 (24%) | 30% | 2% | 7% | 19.265 | 79% |
| Ruído | 45 | 4% | 2% | 2% | — | — |

- **Views engana; minutos e inscritos não.** Shorts são 30% das views e 2% do tempo assistido.
  Lives são 21% dos uploads e 82% dos minutos e 76% dos inscritos ganhos. É por isso que o crivo
  da rodada 9b deu minutos/inscritos como termômetros melhores que views.
- **Programas: mediana 44 mil views, p10 5,8 mil, p90 272 mil** — 47× entre p10 e p90. Comparar
  lives entre si exige normalizar por série ou por faixa de audiência.
- Top por inscritos ganhos: El Salvador filme completo (45,7k), Maduro (15k), Banco Master (13,8k),
  Rio Paraíso em Chamas (12,8k), Metanol (12,7k), Epstein (12,2k), Michael Jackson (11,5k),
  Master × STF (9,9k). **Documentário completo no YouTube é a máquina de inscritos**, não a live de
  notícia (react: 4,8% assistido, 371 inscritos/vídeo).

## Decisões pendentes (André/Bárbara)

1. Validar as regras da tabela e a lista de séries (ou liberar `playlists.list` para usar as
   playlists do canal como série).
2. "Médio (10–25 min)": programa ou corte longo? 242 vídeos dependem disso.
3. Cortes e Shorts: vincular ao programa de origem (por título/data) para somar alcance por programa?
4. A partir da base validada: (a) termômetro diário = minutos + inscritos **dos programas**;
   (b) ranking de "sucesso" por série; (c) pessoa-dia só para programas com espelho na plataforma.

## Rastreio por vídeo (adicionado 16/09/2026 à noite) — a ponte YouTube → venda existe

Toda descrição de vídeo tem links `sitebp.la/<slug>` (`vd_pgm_…` venda, `ld_pgm_…` lead) que redirecionam
com **`utm_source=organic_youtube`, `utm_medium=programas`, `utm_campaign=<lan|ppt>_<sigla>_…`,
`utm_term=<data>`, `utm_content=<slug do vídeo>`**. Lives usam `live_youtube`. Isso identifica o
vídeo na `fct_transactions` e na `dtm_analytics_lead_conversion`.
Arquivos: `yt_links_descricao.csv` (6.773 links), `yt_slugs_utm.csv` (680 slugs, 669 com UTM),
`yt_tx_por_utm.csv`, `yt_leads_por_utm.csv`, `yt_playlists_videos.csv` (138 playlists → 937 vídeos
da base). Tudo consolidado em `yt_base_videos.csv` (colunas `tx_rastr`, `receita_rastr`, `leads_rastr`,
`utm_campaigns`, `playlists`). Links compartilhados por vários vídeos são rateados igualmente.

**Números (ago/2025 → 15/09/2026):** 18.787 tx e **R$ 6,0M** com UTM de YouTube orgânico/live
(~R$ 460k/mês, ~1% da receita), 18.756 primeiras compras, 21.126 leads. **66% das tx casam com um
vídeo específico** (12.329 tx, R$ 3,3M); 1.114 vídeos têm CTA próprio, 854 têm ≥1 venda.

| Camada | Vídeos c/ CTA | Views | Tx rastreadas | Receita | Receita / 1k views |
|---|---:|---:|---:|---:|---:|
| Live | 556/581 | 91,3M | 8.984 | R$ 2,43M | **R$ 27** |
| Corte | 354/1.230 | 40,2M | 1.343 | R$ 412k | R$ 10 |
| Short | 23/682 | 67,2M | 630 | R$ 179k | R$ 3 |
| Médio | 157/242 | 15,2M | 649 | R$ 134k | R$ 9 |

Top vídeos por receita rastreada: Nascimento do Fascismo cap. 1 (R$ 134k, 759 tx), Epstein
(R$ 129k), Fim da Cracolândia (R$ 110k + 1.864 leads), Vida dos Santos ep. 1 (R$ 107k), Especial
10 anos (R$ 83k, 35 Vitalícios), Brasil Evangélico (R$ 77k). **Os 3 cases da Bárbara são
irrelevantes no rastreável**: 11 de Setembro **6 tx / R$ 2,1k / 428 leads** (CTA era freemium
Technocracia), Marçal **7 tx / R$ 4,8k**, Renan **7 tx / R$ 1,2k** — os CTAs apontavam para
Enéas, não para o próprio conteúdo. O que vende no rastreável é **documentário com CTA do próprio
produto**, não live de notícia nem sabatina.

⚠️ Rastreável ≠ efeito total: é a fração que clicou no link da descrição. A ativação da base
(pessoa-dia) e o pareado diário medem o resto. Mas agora o bloco "do view na LP até o objetivo"
da Bárbara tem dado: views → cliques (GA4 `organic_youtube`) → leads/tx por vídeo.

## Tipo de destino do CTA e "o lead do vídeo virou venda?" (16/09, noite)

Destino dos links específicos (coluna `destino_tipo` em `yt_slugs_utm.csv`): **venda/assinatura
(seja membro) 712 vídeos** · lead de campanha 151 · LP de venda de campanha 123 · produto físico
94 · WhatsApp 13 · freemium/app 9. Fase da campanha de destino: 703 vídeos → `ppt`, 402 → `lan`.
Todos os 2.783 vídeos têm ainda os CTAs genéricos (equipe de vendas / upgrade / freemium).

**Como metrificar "vídeo grande com CTA de lead ajudou a venda da campanha?"** — query
[33_leads_youtube_conversao.sql](queries/33_leads_youtube_conversao.sql): dentro da MESMA campanha
(`nm_tag`) e janela, comparar os leads por fonte em conversão ≤60d e receita por lead (RPL):

| Campanha | Fonte | Leads | Conv. 60d | RPL |
|---|---|---:|---:|---:|
| BMA (Banco Master) | **YouTube orgânico** | 7.941 | **7,9%** | **R$ 20,0** |
| | Meta Ads | 122.717 | 2,9% | R$ 5,6 |
| | Google/YouTube Ads | 37.295 | 3,3% | R$ 9,3 |
| NTL25 | YouTube orgânico | 440 | **9,1%** | **R$ 38,8** |
| | Meta Ads | 107.116 | 2,2% | R$ 4,5 |
| ABC | YouTube orgânico | 462 | 5,2% | R$ 19,3 |
| | Meta Ads | 71.140 | 1,5% | R$ 3,9 |
| EVG | YouTube orgânico | 557 | 4,9% | R$ 18,3 |
| | Meta Ads | 131.202 | 1,9% | R$ 5,1 |
| RBP (Resumo BP) | YouTube orgânico | 4.429 | 4,4% | R$ 27,7 |
| | outros | 96.824 | 3,1% | R$ 12,0 |

**O lead vindo do vídeo vale 3–4× o lead de Meta na mesma campanha**, consistente em 5
campanhas. Mas o volume é 1–6% do total de leads da campanha — o vídeo grande "ajuda 100%"? Não:
em BMA, 7.941 leads × R$ 20 = R$ 159k de R$ 1,49M de receita de leads (11%). Ajuda muito por
lead, pouco em volume. ⚠️ Isso é **qualidade por seleção** (quem viu 20 min e clicou já estava
morno), não incrementalidade — o lead de YouTube provavelmente compraria por outro caminho em
parte dos casos. A medida incremental exige holdout de lead ou geo.

Case TEC / 11 de Setembro: a live gerou **433 leads** para o Technocracia (tag TEC, `organic_youtube`)
+ **1.415 leads via Instagram orgânico com tag `11SET`** em 11/09 — a peça de Instagram que a
Bárbara pediu para olhar existe e está rastreada. Conversão ainda imatura (cadastros de 10/09).

### Framework para isolar as variáveis (o que cada camada mede)

| Pergunta | Métrica | Fonte | O que NÃO responde |
|---|---|---|---|
| O vídeo chamou atenção? | views, minutos, inscritos ganhos, origem do tráfego | Analytics API | nada de venda |
| Quem clicou no CTA? | sessões `organic_youtube`/`programas` na LP | GA4 (utm) | quem não clicou |
| O clique virou lead/venda? | tx e leads por `utm_content` do vídeo | fct_transactions, lead_conversion | venda por outro caminho |
| O lead do vídeo valeu mais? | conv. 60d e RPL por fonte dentro da campanha | query 33 | incrementalidade (seleção) |
| Quem assistiu na plataforma comprou mais? | pessoa-dia vs placebo, cluster por pessoa | queries 22/25/31/32 | audiência só-YouTube |
| O dia do vídeo vendeu mais no total? | pareado por spend, resíduo vs esperado | r9b_youtube_real.py, performance-diaria | causalidade (mix, lançamento) |
| Causou? | holdout de lead / geo | GeoLift (desenhado, não rodado) | — |
