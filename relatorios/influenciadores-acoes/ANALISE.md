# Ações de Influs — realizado × resultado

## Pergunta original
Bárbara (03/11/2026): "como acompanhar o que influ está fazendo e resultado". Escopo acertado com o André:
acompanhamento do realizado e do resultado de cada ação de influenciadores, simples, com um padrão de registro.

## Decisões de abordagem
- **Ação = influ × campanha.** Registro em `acoes.json`, montado à mão a partir do Slack (ENTREGAS DE HOJE da Thais
  no #clubinho-bp, posts de ads da Isabella) e da planilha "01. [CLU] Controle de Curadores & Afiliados".
  Sem e-mail/telefone (a planilha tem e-mail pessoal: não entra).
- **Anúncios:** `dtm_analytics_facebook_ads_funnel`, casando o nome do anúncio normalizado com a `chave_anuncio`
  (regex) da ação. Campanha vem da sigla no nome ([CLU], [JOM], [PAR], [LAC], [ELS], [TLR]; [BNO26] sozinho = Clubinho).
  Mídia sem imposto; receita do funil (direta + comercial), mesma régua do fechamento mensal.
- **Link:** `fct_transactions` aprovadas, sem renovação, com o handle no rastreio (`sitebp.la/vd_<camp>_<handle>`);
  utm_medium com "ads" fica fora para não contar duas vezes.
- Influs com anúncio no ar e sem ação registrada entram por uma lista `LEGADO` no `refresh.py` e aparecem na
  tabela "sem ação registrada".
- A primeira versão foi um artefato do Claude (privado); esta é a versão pública no portal, com o mesmo conteúdo.
  O André aprovou publicar inclusive a remuneração combinada por influ.

## Achados principais (dados até 08/11/2026)
- 43 ações registradas, 11 entregando; 8 sem como medir venda (sem link nem anúncio).
- Anúncios das ações: R$ 607 mil de mídia → R$ 877 mil de receita (1,44). Links: R$ 7,4 mil em 8 vendas.
- Todos os anúncios com influ desde 01/10: 597 anúncios, 38 influs, R$ 690 mil → R$ 1,03 mi (1,50).
- Leomar Segundo tem o maior CTR entre os grandes (4,5%) e retorno abaixo de 1 (0,85).

## Pendências / próximos passos
- Registro manual: levar para o vendasbp (tabelas Ações e Entregas + aba "Ações" em /dashboard-canal/influenciadores).
- Beijato: anúncios [10R] não batem com a ação em Carlos Lacerda.
- Padronizar o link (três padrões em uso na planilha) para a venda por link ser medível.

## Queries
| Arquivo | O que faz |
|---|---|
| [queries/anuncios.sql](queries/anuncios.sql) | Métricas por anúncio do Meta desde 01/10 |
| [queries/semanal.sql](queries/semanal.sql) | Mídia e receita por semana e anúncio |
| [queries/vendas_link.sql](queries/vendas_link.sql) | Vendas pelo handle do influ no link |
| [queries/data_max.sql](queries/data_max.sql) | Último dia com gasto no Meta |

## Como atualizar
`python3 refresh.py` (regera `data.json`). Para incluir ação nova, editar `acoes.json`.

## Wiki atualizada
Nenhuma página nesta etapa.
