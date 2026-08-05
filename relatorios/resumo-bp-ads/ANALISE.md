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
- **Janela:** móvel de 30 dias (edições com >50k entregues, para excluir testes/reenvios parciais).

## Achados principais

- ~390k enviados/edição diária, ~96% de entrega, ~37k aberturas humanas (~10%), 300–3.000 clicadores únicos.
- Cliques concentram em notícias BP (~74% no período inicial analisado); anunciantes ainda são <1% dos cliques.
- Anunciantes já veiculados: Sendflow (`sndflw.com`, 02–03/jul, 178 cliques) e Vimansca (`vimansca.com.br`, 14/07, 141 cliques / 67 pessoas).
- ⚠️ **Links de anunciante saem sem UTM** (ex.: `vimansca.com.br/` puro). Domínio funciona como
  identificador, mas recomenda-se padronizar `utm_source=resumo_bp&utm_campaign=<parceiro>&utm_content=<edição>`
  para o parceiro medir no analytics dele e para distinguir 2 anúncios do mesmo parceiro na mesma edição.

## Pendências / próximos passos

- Validar dash com Nicolas/Elias (mensagem na thread do #performance-e-bi).
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
