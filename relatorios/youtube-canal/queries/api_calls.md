# Chamadas de API — youtube-canal

Este relatório **não usa BigQuery**. A fonte é a YouTube Analytics API v2 (OAuth de conta gestora)
mais a Data API v3 (chave) para metadados de vídeo. O arquivo canônico é o
[`refresh.py`](../refresh.py) da pasta — aqui ficam as chamadas em forma legível, para conferência.

Auth: `~/meu_projeto/BigQuery/youtube-analytics/token_yt.json` (OAuth) e `.yt_api_key` (Data API).
Base: `https://youtubeanalytics.googleapis.com/v2/reports`, sempre com `ids=channel==MINE`.

| # | O que responde | dimensions | metrics | Observação |
|---|---|---|---|---|
| 1 | Série diária por formato | `day,creatorContentType` | `views,engagedViews,estimatedMinutesWatched,subscribersGained` | base de quase tudo; `creatorContentType` é o que separa Shorts |
| 2 | Quebra de contagem de views | `day,creatorContentType` | `views,engagedViews` | razão `engagedViews/views` por dia |
| 3 | Virada de dispositivo | `deviceType` | `views,estimatedMinutesWatched` | uma chamada por ano, 2021→atual |
| 4 | Dispositivo por formato | `deviceType,creatorContentType` | `views,engagedViews,estimatedMinutesWatched` | |
| 5 | Origem de tráfego por formato | `insightTrafficSourceType,creatorContentType` | `views,estimatedMinutesWatched` | **sem** `day`, senão a API limita a janelas de 5 dias |
| 6 | Inscrito × não inscrito | `subscribedStatus,creatorContentType` | `views,estimatedMinutesWatched` | o corte "core × novo" |
| 7 | Demografia | `ageGroup,gender` | `viewerPercentage` | percentual, não absoluto |
| 8 | Top vídeos | `video` | `views,engagedViews,estimatedMinutesWatched,averageViewDuration,subscribersGained` | duas chamadas: `sort=-estimatedMinutesWatched` e `sort=-views`, unidas |
| 9 | Curva de retenção | `elapsedVideoTimeRatio` | `audienceWatchRatio,relativeRetentionPerformance` | exige `filters=video==<id>` com **um** id por chamada e `maxResults<=200` |

Data API v3, para duração e título:
`GET /youtube/v3/videos?part=snippet,contentDetails,statistics&id=<até 50 ids>`

## Gotchas encontrados

- `engagedViews` **existe e funciona** — é a contagem de view anterior a 27/08/2026. A wiki dizia que
  impressões/CTR não saem por API (verdade, e confirmado na doc oficial), mas `engagedViews` sai.
- `insightTrafficSourceType` só aceita janelas de até 5 dias **quando combinado com `day`**. Sem `day`,
  cobre o período inteiro numa chamada.
- `audienceRetention` não aceita lista de vídeos em `filters` — um `video==<id>` por chamada.
- `month` como dimensão exige que `endDate` caia no fim do mês; por isso a série é por `day`.
- A dimensão `video` não devolve `creatorContentType`. A classificação Short × longo é feita pela
  **duração** vinda da Data API: `<= 180 s` = Short (regra do YouTube desde out/2024; antes eram 60 s).
  É uma aproximação — um vídeo normal de 2 min entra como Short.
- Defasagem de ~2 dias nos dados; o script fecha a janela em `hoje - 3`.
