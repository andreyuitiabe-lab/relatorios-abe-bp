# Resumo BP × BP Ads — Funil da Newsletter por Parceiro

## Pergunta original

Pedido do Elias (via Nicolas Zanirati, #performance-e-bi, 22/jul/2026): dash de acompanhamento
do Resumo BP para passar aos parceiros do BP Ads. Funil da newsletter (enviados, recebidos,
abertos, cliques) com visão consolidada (interna) e visão segmentada por anunciante — cada
parceiro enxerga só os cliques dos links dele.

## Decisões de abordagem

- **Fonte:** `staging.stg_insider__events`, campanhas `[RBP]` (nome `EM5XX - [RBP] [ENG] [CAD] Dia DD/MM`).
  Validado contra a UI do Insider (edição EM522, 14/07): entregues, cliques únicos e cliques
  do anunciante batem **exatos**; aberturas únicas ficam ~6% abaixo (janela de aberturas tardias).
- **Segmentação por parceiro:** `NET.REG_DOMAIN(nm_email_url)` do evento `email_click`.
  Domínios BP/sociais/editoriais são classificados em `refresh.py`; qualquer domínio externo fora
  dessas listas é tratado como anunciante (novos parceiros aparecem sozinhos no dropdown).
- **"Enviados"** ≈ delivered + blocked + dropped + bounce (Insider não expõe evento `sent`; ~1% acima do "Sent" da UI).
- **Duas taxas de abertura:** padrão mercado (~46%, inclui Apple MPP — comparável a benchmarks)
  e humana (`bl_human_open = 1`, ~10% — pessoas reais). O funil usa a humana; KPIs e tabela mostram ambas.
- **Janela:** móvel de **120 dias** (edições com >50k entregues, para excluir testes/reenvios parciais).
  Era 30 dias e estava errado para o caso de uso: anunciante repete a cada ~1 mês, então o parceiro
  via só a última inserção. Com 120 dias, cobre desde 23/04 (relançamento visual do Resumo BP) — 66 edições.
- **Execução das queries:** cliente Python + ADC (`google.cloud.bigquery`), igual ao `~/bin/bqq`.
  Não usar o `bq` CLI no `refresh.py`: o token dele expira e o refresh quebra sem forma de reautenticar.

## Achados principais

- ~390k enviados/edição diária, ~96% de entrega, ~37k aberturas humanas (~10%), 300–3.000 clicadores únicos.
- Cliques concentram em notícias BP (~74% no período inicial analisado); anunciantes ainda são <1% dos cliques.
- Anunciantes já veiculados: Sendflow (`sndflw.com`, 02–03/jul, 178 cliques) e Vimansca (`vimansca.com.br`, 14/07, 141 cliques / 67 pessoas).
- ⚠️ **Links de anunciante saem sem UTM** (ex.: `vimansca.com.br/` puro). Domínio funciona como
  identificador, mas recomenda-se padronizar `utm_source=resumo_bp&utm_campaign=<parceiro>&utm_content=<edição>`
  para o parceiro medir no analytics dele e para distinguir 2 anúncios do mesmo parceiro na mesma edição.

### Inserções por anunciante (ago/2026)

| Anunciante | Inserções | Detalhe (pessoas / cliques) |
|---|---|---|
| Sendflow | 3 | 02/07 (73 / 145), 03/07 (28 / 41), 28/07 (36 / 56) |
| Vimansca | 2 | 14/07 (69 / 145), 17/08 (90 / 111) |

Vimansca cresceu em alcance da 1ª para a 2ª inserção (69 → 90 pessoas) apesar de menos cliques totais —
na 1ª houve mais cliques repetidos. Sendflow caiu a cada inserção.

### ⚠️ Gotchas de leitura

- **A taxa de abertura humana oscila muito por período** — 7,6% (mai) → 23% (jun–jul) → 9,4% (semana de 27/07)
  → 23,5% (ago), medido sobre eventos `email_open`. `bl_human_open` está sempre populado (nunca NULL),
  então não é falha de dados: é mudança de composição/classificação MPP. **Não comparar taxa de abertura
  humana entre inserções distantes** sem olhar o período — cliques não sofrem esse efeito e são a métrica
  confiável para comparar veiculações.
- **CTR de anunciante fica na casa de 0,0x%** — o formato da página usa 2–3 decimais abaixo de 1%,
  senão o número vira "0%" para o parceiro.
- **O rótulo de edição é `DD/MM`** e serve de chave no match parceiro→edição no `index.html`.
  Seguro na janela de 120 dias; se algum dia a janela passar de 365 dias, colide e precisa virar data ISO.

## Pendências / próximos passos

- Validar dash com Nicolas/Elias (mensagem na thread do #performance-e-bi).
- Avaliar se a janela de 120 dias basta a longo prazo: quando o BP Ads tiver mais de 4 meses de
  histórico, o parceiro volta a perder inserções antigas. Alternativa é materializar uma tabela
  de histórico de edições em vez de reler a `stg_insider__events` a cada refresh.
- Decidir entrega da visão restrita por parceiro (página por parceiro com link não-listado vs Looker com ACL).
- Propor padrão de UTM para links de anunciante com quem monta as edições.
- Se aprovado, agendar refresh recorrente (launchd, padrão zenvia-custos).

## Queries

| Arquivo | O quê |
|---|---|
| [queries/funil_edicao.sql](queries/funil_edicao.sql) | Funil por edição: enviados, entregues, abertos (total e humano), clicadores, cliques, unsub |
| [queries/cliques_dominio.sql](queries/cliques_dominio.sql) | Cliques por domínio de destino e edição (segmentação de parceiro) |

## Wiki atualizada

- `wiki-bp/pages/meta-insider-ads.md`: tag `RBP` documentada (nomenclatura, fonte, gotcha de UTM, aproximação de "enviados").
