# Canal no YouTube — diagnóstico Shorts × Longos

**Data:** 22/09/2026 · **Pedido por:** André (brainstorm de analytics para o time de YouTube)
**Relatório:** https://andreyuitiabe-lab.github.io/relatorios-abe-bp/relatorios/youtube-canal/
**Relacionado:** [`../youtube-vendas/`](../youtube-vendas/ANALISE.md) (YouTube × vendas, 21/09) · [`../relevancia-marca/`](../relevancia-marca/ANALISE.md) (histórico)

## Pergunta original

Levantar o que dá para montar de analytics para o time de YouTube — tendências, performance do canal,
perfil de público, teste de thumbnail — e, antes de pensar em plataforma, **produzir um primeiro
diagnóstico com o que o dado já permite**, com Shorts e vídeos longos sempre separados.

Alimentou o diagnóstico: o episódio *The New Rules of YouTube (2027)* (Colin & Samir com Paddy Galloway,
19/08/2026) e mais quatro vídeos do mesmo canal, indicados pelo André. Foram a origem de três hipóteses
testadas aqui: a virada para a TV, a mudança na contagem de views, e o corte core × novo (CCN).

## Decisões de abordagem

- **`engagedViews` como métrica-base, não `views`.** Em 27/08/2026 o YouTube passou a contar view no
  primeiro frame (inclui autoplay na home); a contagem antiga virou `engagedViews`, que a Analytics API
  entrega normalmente. Qualquer série que cruze essa data tem quebra estrutural. `views` aparece no
  relatório só para medir a própria inflação.
- **Shorts separados de longos em toda métrica**, via `creatorContentType` (`shorts` × `videoOnDemand`
  + `liveStream`). `posts` e `creatorContentTypeUnspecified` ficam fora dos agregados.
- **Short = duração ≤ 180 s** na classificação por vídeo, porque a dimensão `video` não devolve
  `creatorContentType`. É a regra atual do YouTube (era 60 s antes de out/2024) e é aproximação: um
  vídeo comum de 2 min entra como Short. Nos agregados do canal o corte vem da API, não da duração.
- **Top vídeos ranqueado duas vezes** (por minutos e por views) e unido: Shorts fazem pouquíssimos
  minutos e sumiriam de um ranking só por minutos.
- **Janela 2026** (01/01 → 19/09, fechada em `hoje-3` pela defasagem da API). Views acumuladas *durante*
  2026 — um vídeo publicado antes pode aparecer no ranking (é o caso do Short nº 1, de nov/2025).
- **Dispositivo por ano desde 2021** para testar a tese da "grande virada". A série **não é monotônica**
  e está registrada como tal no relatório: 2022 e 2023 destoam porque o share de dispositivo responde ao
  mix de conteúdo. O que sustenta é o retrato atual e o contraste entre formatos, não a tendência.
- Sem eixo duplo em nenhum gráfico; paleta do repo validada pelo validador de CVD antes de usar.
- **Layout editorial (23/09, escolhido pelo André entre 3 direções desenhadas no Claude Design):** leitura longa,
  Fraunces + Source Serif 4 + IBM Plex Mono sobre papel marfim, 7 seções numeradas com título-tese calculado do
  `data.json`. Canvas das variações: https://claude.ai/artifact/DrCUZ8iasCtcKeRxJuW3CX (privado).
- **Gráfico da quebra = views × views engajadas em dois painéis** (opção 1 do canvas), com a área entre as linhas
  = autoplay. Substituiu a razão `engagedViews ÷ views`, que pedia conta de cabeça e induzia a ler os Shorts como
  "inflados" (ver achado 1).
- **Cores novas validadas:** dispositivos TV `#4a3aa7` · celular `#eda100` · computador `#1baf7a`; público
  audiência YouTube `#e87ba4` · membros `#008300`. As neutras do primeiro desenho reprovaram no validador.
- **Fontes além da API do YouTube (23/09):** o `refresh.py` passou a rodar `queries/perfil_youtube_vs_membros.sql`,
  `genero_membros.sql` e a 1ª consulta de `consumo_plataforma.sql` no BigQuery, e o GA4 (dispositivo das sessões com
  `sessionSource` contendo "youtube") pelo `.venv` do `mcp-ga4`, que tem a biblioteca e o token. Nada fica fixo no HTML.

- **Parte 2 · O mercado e nós (23/09, pedido do André: "puxar tudo o que pesquisamos no começo").** Cada tendência
  da pesquisa inicial vira uma linha de placar: o que o mercado mostra (com fonte e link), onde a BP está (calculado)
  e uma leitura (à frente / no ritmo / atrás / oportunidade). Números de mercado ficam em `BENCH` no `refresh.py`,
  com a fonte — referência externa, não dado nosso. Fontes: Paddy Galloway em *The New Rules of YouTube (2027)*;
  Colin and Samir: *Emergency Pod* (views), *YouTube Playbook in 37 Minutes*, *11 Marketing Rules* (Kate Tolo).
- **Referência de duração do mercado mostrada só como nível de hoje (20 min ou mais):** a fonte publica dois pontos
  (12–16 min em 2020, 20+ hoje); ligar os dois inventaria uma trajetória ano a ano.
- **Urgente × atemporal × meio-termo** pelos 14 primeiros dias de cada vídeo (série vídeo × dia do youtube-vendas):
  urgente = ≥80% das views nos 3 primeiros dias; atemporal = ≥25% depois do 7º dia; só vídeos com ≥30 mil views em
  14 dias (vídeo pequeno some do top-200 e pareceria urgente por artefato). ⚠️ A primeira conta dividia inscritos
  acumulados por views de 14 dias e dava 3× a favor do atemporal — viés; com as duas métricas acumuladas, **1,7×**.
- **Tempo assistido por ano pela Analytics API (25/09):** vídeo sob demanda (`creatorContentType=videoOnDemand`, sem
  lives e sem Shorts), minutos ÷ views engajadas. Substituiu o número da base por vídeo (6 min 34 s), que usava a
  contagem de views inflada pós-27/08.
- **Busca em três tipos:** marca (BP ou programa do canal), título nosso (nome de produção original da plataforma,
  `queries/titulos_originais.sql`; chave = parte do nome antes de ":"/"|", com 2+ palavras ou 8+ letras) e tema.
  "el salvador" cai em título nosso mesmo podendo ser só o país.
- **Audiência internacional:** países por views engajadas; hispânicos = Espanha + 19 países das Américas;
  lusófonos = PT, AO, MZ, CV, GW, ST, TL. Medido no canal e nos 9 vídeos de maior alcance.
- **Formato e séries** vêm da `yt_base_videos.csv` (classificar_videos.py, uploads desde 01/08/2025); duração e
  mix por ano vêm de todos os uploads do canal pela Data API (chave, sem OAuth). `python3 refresh.py --so-mercado`
  recalcula só esse bloco sobre o `data.json` atual.

- ⚠️ **Estreia ≠ live (correção de 28/09).** A API marca Estreia (Premiere) com os mesmos dados de live, e a base
  (`yt_base_videos.csv`, tipo "live") misturava as duas: 482 das 578 "lives" eram vídeos editados lançados como estreia
  (mediana 15 min — Master × STF, Epstein, El Salvador). Regra adotada: live = marcada como live **e** título com
  "ao vivo"/"live"/"react" ou série de live (Rasta News, BP nas Eleições, Live/react); o resto é estreia = vídeo
  editado. A Analytics API conta estreia como vídeo sob demanda, então a Parte 1 (longos × Shorts, tempo assistido)
  não foi afetada — a soma dos carros-chefe em estreia já passaria do total de `liveStream` do ano.

## Achados principais

**1. A contagem de views quebrou em 27/08/2026 — e quem mudou foi o vídeo longo.**
Nos Shorts a contagem sempre foi assim: o ano inteiro, de cada 100 views ~50 eram engajadas (50% antes,
46% depois de 27/08). Nos vídeos longos eram 100 de 100 (99,7%) até 26/08 e passaram a **54 de 100**.
O vídeo longo passou a ser contado como o Short sempre foi. ⚠️ Correção de 23/09: a primeira versão dizia
"Shorts inflaram 1,99×, longos 1,12×" — são médias de 2026 inteiro; o 1,12× dos longos está diluído por oito
meses sem a contagem nova (depois de 27/08 é 1,84×) e o 1,99× dos Shorts não é efeito da mudança.
Em 2026 o canal tem 176,6 M views contra 121,3 M engajadas.

**2. São dois canais dentro de um.** Shorts = 31,8% das views engajadas e **3,3% dos minutos**.

| | Vídeos longos | Shorts |
|---|---|---|
| Views engajadas 2026 | 81,4 M | 38,0 M |
| Minutos assistidos | 834,7 M | 28,9 M |
| Minutos por view | 10,25 | 0,76 |
| **Inscritos por mil views** | **4,33** | **1,45** |
| Views na TV | 44% | 9% |
| Views no celular | 45% | 85% |

**3. Vídeo longo recruta 3,0× mais inscritos por view que Short.** A tese de que "Shorts alimentam o
funil de inscritos" não se sustenta nos nossos números. O maior recrutador do ano é o conteúdo mais
longo do canal: *El Salvador — O dia em que o medo mudou de lado* (1h37) trouxe **11,1 inscritos por mil
views** e segurou 25% da duração.

**4. TV é 50% dos minutos do canal e 44% das views de vídeo longo — e na TV não se clica em descrição.**
Todo o nosso rastreio de venda pelo YouTube depende de links `sitebp.la` na descrição. Isso torna a
atribuição do YouTube orgânico (1,1% das transações no `youtube-vendas`) um **piso**, não uma medida.
Não se resolve com mais UTM.

**5. O achado mais contraintuitivo: os sugeridos entregam 2,2× mais tempo que os inscritos.**
Nos vídeos longos, quem chega por **vídeo sugerido** assiste 14,5 min/view; quem vem do feed de
inscritos, 6,6. Inscritos trazem volume (53% das views), sugeridos trazem tempo (25% das views). A busca
do YouTube tem comportamento parecido e é só 8,6% das views — **a maior oportunidade subexplorada**.
55% das views de vídeo longo vêm de quem não é inscrito: o canal não está falando só com a própria base.

**6. Retenção: estamos na mediana da plataforma, com uma exceção.** `relativeRetentionPerformance`
compara cada vídeo com todos os do mesmo tamanho no YouTube. Nossos longos do topo ficam em ~0,49–0,54.
*El Salvador* dá **0,68** — retém melhor que a maioria dos vídeos daquele tamanho. Shorts marcam acima de
1,0 e retenção >100% porque são reassistidos em loop: não são comparáveis nessa coluna.

**7. Assiste na TV, compra no celular.** TV = 50% dos minutos no YouTube e 56% das horas na plataforma
(TV + Chromecast). Das 296 mil sessões que chegaram ao site vindas do YouTube em 2026, **11 foram em smart TV**
(GA4 com filtro, número exato). 85% celular, 15% computador — e o computador fica 77% mais tempo e dispara 12%
mais eventos-chave por sessão.

**8. Quem assiste não é quem assina.** Abaixo de 35 anos: 31% da audiência do YouTube, 8% dos membros ativos e
8,8% dos compradores novos de 2026 (não é estoque antigo). A partir de 45: 43% da audiência, 68% dos membros.
Mulheres: 24% da audiência, 38% dos membros. O perfil etário é o mesmo em Shorts, vídeos e lives. Ressalvas:
idade declarada cobre 22% dos membros; o YouTube mede % das views, a base mede pessoas.


### Parte 2 · O mercado e nós

**9. TV:** no ritmo do mercado — 50% dos minutos (32% em 2021), mercado >50%.
**10. Duração (corrigido 28/09):** contando as estreias, o vídeo editado médio foi de 24,4 min em 2025 (17,9 min em
2026 até set) — **no nível do mercado** (20+ min). A primeira versão dizia "9,8 min, metade do mercado": excluía as
estreias, que são o vídeo editado principal. Mediana bem menor (9,5 min em 2025) porque mistura cortes e documentários.
**11. A produção foi para o outro lado:** Shorts publicados saíram de 27 (2021) para 1.064 (2025).
**12. Esforço × retorno (ago/2025–set/2026, 2.788 vídeos):** vídeos editados lançados como estreia = 17% dos uploads,
**69% dos minutos e 67% dos inscritos**; cortes de 1–10 min = 44% dos uploads e 4% dos minutos; Shorts = 24% e 2%;
lives de verdade = 3% e 14%. (A primeira versão atribuía às "lives" 21% dos uploads e 82% dos minutos — eram estreias.)
**13. Programa (corrigido 28/09):** 86% dos vídeos de programa são avulsos. Entre vídeos editados, série e avulso
rendem parecido por vídeo (213 mil × 210 mil min, mediana; 66 × 53 inscritos). A comparação anterior "lives de série
2× avulsas" era artefato (comparava live de verdade com estreia). O argumento do mercado — maratona na TV — não aparece
no dado por vídeo. Só 6 das 126 playlists estão marcadas como podcast (Conversa Paralela, Sabatina, Especial de Natal,
Guerra do Imaginário, Red Pill, Xeque-Mate); Rasta News (210 vídeos) não.
**14. Atemporal:** 8% dos 608 vídeos avaliados, 5,1 inscritos/mil views — contra 3,0 no urgente (46% dos vídeos) e
4,2 no meio-termo (47%). O meio-termo não é o pior no nosso canal, ao contrário do que o mercado sugere.
**15. Abertura boa, miolo fraco:** retenção relativa à plataforma de 0,60 nos primeiros 10% do vídeo e 0,53 no resto
(7 vídeos longos do topo). O que falta é o ritmo do meio, não o gancho.
**16. Tempo assistido: já estávamos à frente, e o mercado está alcançando.** Vídeo sob demanda: 7 min 54 s por
view em 2021 e 8 min 33 s em 2026 (+8%), contra 4 min 35 s → 8 min no mercado (+77%). Lives: 19 min 44 s → 18 min 52 s.
**17. A busca é de quem já nos conhece:** entre os 25 termos que mais trazem views, 57% procuram a BP ou um programa e
14% o nome de uma produção nossa; só 29% chegam por um assunto (o grosso é Epstein, mais "documentarios", 11 de
Setembro). A busca é 8,6% das views de vídeo longo.
**18. Fora do Brasil o canal praticamente não existe:** 93,9% das views engajadas de 2026 são do Brasil, 2,5% de outros
lusófonos e 0,6% de hispânicos. O filme de El Salvador teve 0,4% de audiência hispânica. Dublagem é tendência de
mercado (4× views, Paddy Galloway) — para nós é terreno inexplorado, se fizer sentido para o negócio.

**19. Capítulos:** em 2026, 69% das estreias têm capítulos, mas só 1% dos vídeos de 10 min+ publicados direto e 4% das
lives. Capítulo é o principal preditor de o vídeo ser citado nas respostas de IA do Google (YouTube = 23% das citações).
**20. Produção em massa:** desde jul/2025 o YouTube desmonetiza conteúdo repetitivo/produzido em massa; cortes são 44%
dos nossos uploads. Conteúdo próprio recortado fica na regra de reutilizado — risco baixo, mas é o que a regra mira.

**Placar (28/09):** 14 tendências — 4 no ritmo ou à frente, 1 atrás (peso de Shorts), 8 oportunidades, 1 ponto de
atenção (produção em massa). Novas: programas/podcasts no app de TV, capítulos e busca por IA, produção em massa.
**Placar (25/09, superado):** 11 tendências — 3 no ritmo ou à frente (TV, tempo assistido, retenção), 2 atrás (duração do vídeo,
peso de Shorts), 6 oportunidades (programa, atemporal, miolo do vídeo, portas de entrada, idiomas, repetir o que funciona).

## Impacto no relatório `youtube-vendas` (não corrigido ainda)

Aquele relatório usa `views` e cobre uma janela que atravessa 27/08. Recalculando o top 10 com
`engagedViews`: 1º e 2º trocam de posição; *25 anos do 11 de Setembro* cai de 3º para 4º (perde para o
Epstein, de fevereiro); e a frase do ANALISE *"os 3 maiores são de setembro e somam mais que os outros 7"*
**se inverte** — 5,97 M contra 6,85 M. Decisão de corrigir ou não é do André, alinhada com a Bárbara.

## Pendências / próximos passos

- ⚠️ **Token OAuth do YouTube morreu em 23/09 (7 dias após o de 16/09):** o app OAuth do client da Bárbara está em
  modo "Testing", em que o Google expira o refresh token a cada 7 dias. Reautenticar: `auth_yt_manual.py` (URL gerada
  em 23/09, enviada ao André para repassar). Definitivo: Bárbara mudar o consent screen para "In production" (ou
  "Internal"). Sem token, `refresh.py` completo não roda; `--so-mercado` roda.
- ✅ Token recuperado em 25/09; busca, países e tempo assistido por ano entraram no placar. ⚠️ Se o app OAuth
  continuar em "Testing", o token morre de novo em 7 dias (~02/10) — confirmar com a Bárbara se ela mudou para
  "In production".

- **Decidir o que fazer com o `youtube-vendas`** — o ranking muda e uma conclusão publicada se inverte.
- **Passar os coletores a gravar `views` e `engagedViews`** (`fetch_youtube_daily.py`,
  `fetch_tipo_diario.py`, `fetch_video_semanal.py`). Enquanto não fizer, todo dado novo nasce ambíguo.
- **Plataforma de analytics** (próximo tema combinado com o André): manter isso vivo em vez de retrato.
  Candidatos já mapeados no brainstorm — radar de concorrentes via Data API (urgente: a API não devolve
  histórico de views, cada semana sem coletar é perdida), banco de testes de thumbnail, análise de
  atributos de thumbnail, R$ por mil views por tema.
- **Cruzar demografia por vídeo com perfil de comprador** (`dim_user` / `dim_contact`) — a API entrega
  `ageGroup,gender` por vídeo.
- **Classificar 2026 em timely / timeless / meio** e medir o tamanho do "meio" (conceito do episódio).
- Impressões e CTR de thumbnail **não saem por nenhuma API** (confirmado na doc oficial) — só export
  manual do Studio. Bloqueia qualquer análise de packaging baseada em CTR.

## Arquivos

| Arquivo | O que faz |
|---|---|
| [refresh.py](refresh.py) | coleta tudo da Analytics API + Data API e gera `data.json` |
| [queries/api_calls.md](queries/api_calls.md) | as 9 chamadas de API em forma legível + gotchas |
| [queries/perfil_youtube_vs_membros.sql](queries/perfil_youtube_vs_membros.sql) | idade dos membros ativos e dos compradores novos de 2026 |
| [queries/genero_membros.sql](queries/genero_membros.sql) | gênero (inferido) dos membros ativos |
| [queries/consumo_plataforma.sql](queries/consumo_plataforma.sql) | dispositivo e playlists mais assistidas na plataforma |
| [queries/titulos_originais.sql](queries/titulos_originais.sql) | títulos originais BP — classificam termos de busca em "título nosso" |
| [index.html](index.html) | layout e gráficos (`fetch('./data.json')`) |

## Wiki atualizada

- `wiki-bp/pages/youtube-instagram-acesso.md`: seção nova **"⚠️ Quebra na contagem de views — 27/08/2026"**
  com a data medida, as razões por período, as consequências e a instrução de usar `engagedViews`.
- Registrado em `wiki-bp/log.md` em 22/09/2026.
