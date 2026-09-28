#!/usr/bin/env python3
"""
Diagnóstico do canal @brasilparalelo no YouTube — Shorts x Longos.

Fontes:
- YouTube Analytics API (OAuth de conta gestora, token em
  ~/meu_projeto/BigQuery/youtube-analytics/token_yt.json) + Data API v3 (chave) — canal.
- BigQuery (ADC) — perfil dos membros e consumo na plataforma (queries/*.sql).
- GA4 (token do ~/meu_projeto/BigQuery/mcp-ga4, rodado no .venv de lá) — dispositivo de quem
  chega ao site vindo do YouTube.

Uso:
  python3 refresh.py            # coleta tudo e regrava data.json
  python3 refresh.py --push     # + git add/commit/push
  python3 refresh.py --so-mercado  # só o bloco de mercado, sobre o data.json atual (não precisa do OAuth)

⚠️ Toda métrica é reportada separando `shorts` de `longos` (videoOnDemand +
liveStream). A mistura dos dois é o erro nº 1 deste canal: em 2026 os Shorts são
~43% das views e ~3% dos minutos.

⚠️ Quebra de metodologia em 27/08/2026: o YouTube passou a contar view no
primeiro frame (inclui autoplay). A contagem antiga virou `engagedViews`.
Toda série histórica aqui usa `engagedViews`; `views` aparece só para medir a
própria inflação. Ver wiki-bp/pages/youtube-instagram-acesso.md.
"""

import json, subprocess, sys, datetime, urllib.request, urllib.parse, time
from pathlib import Path

YT_DIR = Path.home() / "meu_projeto/BigQuery/youtube-analytics"
OUT    = Path(__file__).parent / "data.json"
CHANNEL_ID = "UCKDjjeeBmdaiicey2nImISw"
ANO_INI, ANO_FIM = "2026-01-01", None          # FIM = ontem-2 (defasagem da API)
QUEBRA = "2026-08-27"                          # dia em que views != engagedViews

LONGOS = ("videoOnDemand", "liveStream")
SHORTS = ("shorts",)

sys.path.insert(0, str(YT_DIR))


# ─── auth ────────────────────────────────────────────────────────────────────
def creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    c = Credentials.from_authorized_user_file(str(YT_DIR / "token_yt.json"))
    if not c.valid:
        c.refresh(Request())
    return c


_C = None
def ya(**params):
    """YouTube Analytics API v2 -> lista de linhas (já em tipos nativos)."""
    global _C
    if _C is None:
        _C = creds()
    params.setdefault("ids", "channel==MINE")
    url = "https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {_C.token}"})
    for attempt in range(3):
        try:
            d = json.load(urllib.request.urlopen(req))
            return d.get("rows", []), [h["name"] for h in d["columnHeaders"]]
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)


def yd(endpoint, **params):
    """Data API v3 (chave) -> json."""
    key = (YT_DIR / ".yt_api_key").read_text().strip()
    params["key"] = key
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    return json.load(urllib.request.urlopen(url))


def grupo(tipo: str) -> str:
    if tipo in SHORTS:
        return "shorts"
    if tipo in LONGOS:
        return "longos"
    return "outros"          # posts, creatorContentTypeUnspecified


# ─── coleta ──────────────────────────────────────────────────────────────────
def serie_diaria(ini, fim):
    """dia x tipo de conteúdo: views, engagedViews, minutos, inscritos."""
    rows, _ = ya(startDate=ini, endDate=fim, dimensions="day,creatorContentType",
                 metrics="views,engagedViews,estimatedMinutesWatched,subscribersGained")
    out = {}
    for dia, tipo, v, e, m, s in rows:
        g = grupo(tipo)
        d = out.setdefault(dia, {"d": dia})
        d[f"{g}_v"] = d.get(f"{g}_v", 0) + v
        d[f"{g}_e"] = d.get(f"{g}_e", 0) + e
        d[f"{g}_m"] = d.get(f"{g}_m", 0) + m
        d[f"{g}_s"] = d.get(f"{g}_s", 0) + s
    return [out[k] for k in sorted(out)]


def device_por_ano():
    """A 'grande virada de dispositivo': share de minutos por device, por ano."""
    out = []
    hoje = datetime.date.today()
    for ano in range(2021, hoje.year + 1):
        ini = f"{ano}-01-01"
        fim = f"{ano}-12-31" if ano < hoje.year else str(hoje - datetime.timedelta(days=3))
        rows, _ = ya(startDate=ini, endDate=fim, dimensions="deviceType",
                     metrics="views,estimatedMinutesWatched")
        tot_v = sum(r[1] for r in rows) or 1
        tot_m = sum(r[2] for r in rows) or 1
        out.append({
            "ano": ano,
            "dev": {r[0]: {"v": r[1], "m": r[2], "pv": r[1] / tot_v, "pm": r[2] / tot_m}
                    for r in rows},
            "views": tot_v, "min": tot_m,
        })
    return out


def device_por_tipo(ini, fim):
    rows, _ = ya(startDate=ini, endDate=fim, dimensions="deviceType,creatorContentType",
                 metrics="views,engagedViews,estimatedMinutesWatched")
    out = {}
    for dev, tipo, v, e, m in rows:
        g = grupo(tipo)
        if g == "outros":
            continue
        d = out.setdefault(g, {})
        d[dev] = {"v": d.get(dev, {}).get("v", 0) + v,
                  "e": d.get(dev, {}).get("e", 0) + e,
                  "m": d.get(dev, {}).get("m", 0) + m}
    return out


def trafego_por_tipo(ini, fim):
    rows, _ = ya(startDate=ini, endDate=fim,
                 dimensions="insightTrafficSourceType,creatorContentType",
                 metrics="views,estimatedMinutesWatched")
    out = {}
    for src, tipo, v, m in rows:
        g = grupo(tipo)
        if g == "outros":
            continue
        d = out.setdefault(g, {})
        cur = d.get(src, {"v": 0, "m": 0})
        d[src] = {"v": cur["v"] + v, "m": cur["m"] + m}
    return out


def inscrito_vs_novo(ini, fim):
    """CCN: core (inscrito) x novo (não inscrito), por tipo."""
    rows, _ = ya(startDate=ini, endDate=fim,
                 dimensions="subscribedStatus,creatorContentType",
                 metrics="views,estimatedMinutesWatched")
    out = {}
    for st, tipo, v, m in rows:
        g = grupo(tipo)
        if g == "outros":
            continue
        d = out.setdefault(g, {})
        cur = d.get(st, {"v": 0, "m": 0})
        d[st] = {"v": cur["v"] + v, "m": cur["m"] + m}
    return out


def demografia(ini, fim):
    rows, _ = ya(startDate=ini, endDate=fim, dimensions="ageGroup,gender",
                 metrics="viewerPercentage")
    return [{"faixa": a.replace("age", ""), "genero": g, "pct": p} for a, g, p in rows]


def top_videos(ini, fim, n=40):
    """Top vídeos do período, com views x engagedViews e metadados.

    Ranqueia por minutos E por views e une os dois: Shorts fazem pouquíssimos
    minutos, então sumiriam de um ranking só por minutos.
    Short = duração <= 180 s (regra do YouTube desde out/2024; antes eram 60 s).
    """
    met = "views,engagedViews,estimatedMinutesWatched,averageViewDuration,subscribersGained"
    rows_m, _ = ya(startDate=ini, endDate=fim, dimensions="video", metrics=met,
                   sort="-estimatedMinutesWatched", maxResults=200)
    rows_v, _ = ya(startDate=ini, endDate=fim, dimensions="video", metrics=met,
                   sort="-views", maxResults=200)
    seen, rows = set(), []
    for r in rows_m + rows_v:
        if r[0] in seen:
            continue
        seen.add(r[0])
        rows.append(r)
    ids = [r[0] for r in rows]
    meta = {}
    for i in range(0, len(ids), 50):
        d = yd("videos", part="snippet,contentDetails,statistics", id=",".join(ids[i:i + 50]))
        for it in d.get("items", []):
            meta[it["id"]] = it
    import re
    def dur_s(iso):
        m = re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?", iso or "")
        if not m:
            return 0
        h, mi, s = m.groups()
        return int(h or 0) * 3600 + int(mi or 0) * 60 + int(float(s or 0))

    out = []
    for vid, v, e, m, avd, sg in rows:
        it = meta.get(vid)
        if not it:
            continue
        d = dur_s(it["contentDetails"]["duration"])
        if d == 0:
            continue
        out.append({
            "id": vid, "titulo": it["snippet"]["title"],
            "publicado": it["snippet"]["publishedAt"][:10],
            "dur_s": d, "grupo": "shorts" if d <= 180 else "longos",
            "v": v, "e": e, "m": m, "avd": avd, "sg": sg,
            "ret": (avd / d) if d else 0,
        })
    return out


def retencao(video_ids):
    """Curva de retenção (audienceWatchRatio) por vídeo — 100 segmentos."""
    out = {}
    for vid in video_ids:
        try:
            rows, _ = ya(startDate="2026-01-01", endDate=str(datetime.date.today() - datetime.timedelta(days=3)),
                         dimensions="elapsedVideoTimeRatio",
                         metrics="audienceWatchRatio,relativeRetentionPerformance",
                         filters=f"video=={vid}", maxResults=200)
            if rows:
                out[vid] = [{"x": r[0], "w": r[1], "rel": r[2]} for r in rows]
        except Exception as e:
            print(f"  ! retenção {vid}: {e}", file=sys.stderr)
    return out


def quebra_views(ini, fim):
    """Razão engagedViews/views por dia e por tipo — evidência da mudança de contagem."""
    rows, _ = ya(startDate=ini, endDate=fim, dimensions="day,creatorContentType",
                 metrics="views,engagedViews")
    out = {}
    for dia, tipo, v, e in rows:
        g = grupo(tipo)
        if g == "outros":
            continue
        d = out.setdefault(dia, {"d": dia})
        d[f"{g}_v"] = d.get(f"{g}_v", 0) + v
        d[f"{g}_e"] = d.get(f"{g}_e", 0) + e
    return [out[k] for k in sorted(out)]


# ─── público e jornada (BigQuery + GA4) ─────────────────────────────────────
QDIR    = Path(__file__).parent / "queries"
GA4_DIR = Path.home() / "meu_projeto/BigQuery/mcp-ga4"
GA4_PROPERTY = "378996649"


def bq(sql):
    """BigQuery pelo cliente Python (ADC — mesma credencial do bqq, não expira)."""
    from google.cloud import bigquery
    return [dict(r) for r in bigquery.Client(project="bp-datawarehouse").query(sql).result()]


def publico_membros():
    """Idade e gênero dos membros ativos e dos compradores novos de 2026 (queries/*.sql canônicas)."""
    rows = bq((QDIR / "perfil_youtube_vs_membros.sql").read_text())
    com_data = [r for r in rows if r["faixa"] != "zz sem data"]
    sem = next((r for r in rows if r["faixa"] == "zz sem data"), {"membros_ativos": 0, "compradores_novos_2026": 0})
    ta = sum(r["membros_ativos"] for r in com_data) or 1
    tn = sum(r["compradores_novos_2026"] for r in com_data) or 1
    faixas = [{"faixa": r["faixa"],
               "ativos": r["membros_ativos"] / ta,
               "novos": r["compradores_novos_2026"] / tn} for r in com_data]
    gen = {r["genero"]: r["pessoas"] for r in bq((QDIR / "genero_membros.sql").read_text())}
    tg = (gen.get("masculino", 0) + gen.get("feminino", 0)) or 1
    return {
        "faixas": faixas,
        "cobertura_idade": ta / (ta + sem["membros_ativos"]),
        "n_ativos_com_idade": ta, "n_novos_com_idade": tn,
        "pct_feminino": gen.get("feminino", 0) / tg,
    }


def consumo_plataforma():
    """Dispositivo de consumo na plataforma (1ª consulta de queries/consumo_plataforma.sql)."""
    sql = [q for q in (QDIR / "consumo_plataforma.sql").read_text().split(";") if "SELECT" in q][0]
    rows = bq(sql)
    tot = sum(float(r["horas"]) for r in rows) or 1
    grupo = {"TV": "TV", "CHROMECAST": "TV", "ANDROID": "celular", "IOS": "celular", "WEB": "computador"}
    out = {}
    for r in rows:
        g = grupo.get(r["cliente"], "outros")
        out[g] = out.get(g, 0) + float(r["horas"]) / tot
    return out


def ga4_device(ini, fim):
    """Sessões no site por dispositivo — tudo e só as que vêm do YouTube (sessionSource contém 'youtube').

    Roda no ambiente do mcp-ga4, que tem a biblioteca e o token do GA4.
    """
    code = f"""
import json, sys
sys.path.insert(0, {str(GA4_DIR)!r})
from auth import get_credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (RunReportRequest, Dimension, Metric, DateRange,
                                                FilterExpression, Filter)
c = BetaAnalyticsDataClient(credentials=get_credentials())
def run(filtro):
    req = RunReportRequest(property="properties/{GA4_PROPERTY}",
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[Metric(name=m) for m in ("sessions", "engagedSessions", "averageSessionDuration", "keyEvents")],
        date_ranges=[DateRange(start_date="{ini}", end_date="{fim}")],
        dimension_filter=filtro)
    return [[r.dimension_values[0].value] + [float(x.value) for x in r.metric_values] for r in c.run_report(req).rows]
yt = FilterExpression(filter=Filter(field_name="sessionSource", string_filter=Filter.StringFilter(
    value="youtube", match_type=Filter.StringFilter.MatchType.CONTAINS, case_sensitive=False)))
print(json.dumps({{"youtube": run(yt), "site": run(None)}}))
"""
    r = subprocess.run([str(GA4_DIR / ".venv/bin/python"), "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("GA4: " + r.stderr.strip()[-400:])
    raw = json.loads(r.stdout)
    def fmt(rows):
        tot = sum(x[1] for x in rows) or 1
        return {x[0]: {"sessoes": x[1], "share": x[1] / tot, "engaj": x[2] / x[1] if x[1] else 0,
                       "dur_s": x[3], "eventos_por_sessao": x[4] / x[1] if x[1] else 0} for x in rows}
    return {"youtube": fmt(raw["youtube"]), "site": fmt(raw["site"])}


# ─── mercado: tendências da pesquisa × onde estamos ─────────────────────────
# Números de mercado publicados nas fontes abaixo (pesquisa de 21–22/09/2026). São referência externa,
# não dado nosso — cada um carrega a fonte para aparecer no relatório.
VENDAS_DATA = Path(__file__).parent.parent / "youtube-vendas" / "data"
FONTE_PADDY = {"nome": "Paddy Galloway em The New Rules of YouTube (2027), Colin and Samir, 19/08/2026",
               "url": "https://www.youtube.com/watch?v=WyiGFFTnIS4"}
FONTE_VIEWS = {"nome": "Emergency Pod: YouTube Views Just Changed, Colin and Samir, 03/09/2026",
               "url": "https://www.youtube.com/watch?v=v-U35n9L3h4"}
FONTE_PLAYBOOK = {"nome": "The YouTube Playbook in 37 Minutes, Colin and Samir, 23/08/2025",
                  "url": "https://www.youtube.com/watch?v=8XSssH3B_Dk"}
FONTE_KATE = {"nome": "11 Marketing Rules Every YouTuber Needs to Know (Kate Tolo), Colin and Samir, 09/09/2026",
              "url": "https://www.youtube.com/watch?v=Ak-YNIBqEjI"}
FONTE_YT = {"nome": "YouTube Analytics API — relativeRetentionPerformance (0,5 = mediana da plataforma)",
            "url": "https://developers.google.com/youtube/analytics/metrics"}
BENCH = {
    "tv":       {"ref_2021": 0.235, "ref_hoje": 0.50, "texto": "TV passou de 23–24% da audiência em 2021 para mais de 50% hoje", "fonte": FONTE_PADDY},
    "duracao":  {"ref_2020_min": 14.0, "ref_hoje_min": 20.0, "var": 0.51, "texto": "vídeo longo médio subiu 51% desde 2020: de 12–16 min para 20 min ou mais", "fonte": FONTE_PADDY},
    "avd":      {"ref_2021_s": 275, "ref_2025_s": 480, "texto": "duração média assistida do vídeo longo subiu 77% em 4 anos: de 4min35 para 8min", "fonte": FONTE_PADDY},
    "shows":    {"texto": "canais que crescem viraram programas: formato repetido, nome e identidade, que a pessoa maratona na TV", "fonte": FONTE_PADDY},
    "repetir":  {"texto": "quando algo funciona, repita — se você não repetir o formato, outro canal repete", "fonte": FONTE_KATE},
    "ciclo":    {"texto": "conteúdo precisa ser urgente ou atemporal; o meio-termo, que leva semanas e não é nem um nem outro, é onde mais se perde", "fonte": FONTE_KATE},
    "abertura": {"texto": "os primeiros 7 s confirmam o clique e até 30 s entra um novo gancho; depois, ritmo de problemas novos, não de cortes", "fonte": FONTE_PLAYBOOK},
    "retencao": {"ref": 0.50, "texto": "a própria plataforma compara a retenção de cada vídeo com todos os de duração parecida; 0,50 é a mediana", "fonte": FONTE_YT},
    "shorts":   {"texto": "o algoritmo de vídeo longo é mais sofisticado que o de Shorts, e o YouTube está apertando a monetização de Shorts a partir de 2027", "fonte": FONTE_VIEWS},
    "sugeridos":{"texto": "a origem da audiência diz se um vídeo alimenta a base ou recruta gente nova; sugeridos e busca são as portas de entrada", "fonte": FONTE_PLAYBOOK},
    "capitulos":{"texto": "o YouTube é a fonte mais citada nas respostas de IA do Google (23% das citações); vídeo longo de referência com capítulos é o que mais aparece — views e inscritos não fazem diferença",
                 "fonte": {"nome": "OtterlyAI, YouTube AI Citation Study 2026 (+100 mi de citações em 30 dias)", "url": "https://otterly.ai/blog/youtube-ai-citation-study-2026/"}},
    "tvapp":    {"texto": "o app de TV passou a organizar playlists em programas com temporadas e episódios, com aba de podcasts; e desde 03/09/2026 o modo companheiro deixa ler a descrição, comentar e se inscrever pelo celular enquanto a TV toca",
                 "fonte": {"nome": "YouTube Blog, 5 New Features to Help Creators Shine on TV Screens, 29/10/2025", "url": "https://blog.youtube/news-and-events/new-features-to-help-creators/"}},
    "inautentico":{"texto": "desde julho de 2025 o YouTube tira a monetização de conteúdo repetitivo ou produzido em massa, feito de molde; cortes e compilações seguem na regra de conteúdo reutilizado",
                 "fonte": {"nome": "YouTube Help, Channel monetization policies", "url": "https://support.google.com/youtube/answer/1311392?hl=en"}},
    "dublagem": {"texto": "dublagem e audiência internacional multiplicam alcance — o mesmo vídeo dublado chega a ter 4× as views", "fonte": FONTE_PADDY},
}
# A API marca Estreia (Premiere) com os mesmos dados de live. Na BP, a maior parte do vídeo editado sai como estreia
# (482 de 578 "lives" na base de ago/2025–set/2026). Live de verdade = título diz ao vivo/live/react ou é série de live.
import re as _re
LIVE_TXT = _re.compile(r"\bao vivo\b|\blive\b|\breact\b|\bdireto\b|rasta news|bp nas elei", _re.I)
SERIES_LIVE = {"Rasta News", "Live / react de notícia", "BP nas Eleições"}
HISPANOS = {"ES", "MX", "AR", "CO", "CL", "PE", "VE", "EC", "GT", "SV", "HN", "NI", "CR", "PA", "DO", "BO", "PY", "UY", "CU", "PR"}
LUSOFONOS = {"PT", "AO", "MZ", "CV", "GW", "ST", "TL"}


def uploads_por_ano():
    """Histórico completo de uploads (Data API, chave): duração do vídeo editado e mix de formatos por ano."""
    import re
    ch = yd("channels", part="contentDetails", id=CHANNEL_ID)["items"][0]
    pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], ""
    while True:
        kw = {"pageToken": tok} if tok else {}
        d = yd("playlistItems", part="contentDetails", playlistId=pl, maxResults=50, **kw)
        ids += [i["contentDetails"]["videoId"] for i in d["items"]]
        tok = d.get("nextPageToken")
        if not tok:
            break
    def dur(iso):
        m = re.search(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?", iso or "")
        return sum(float(x or 0) * k for x, k in zip(m.groups(), (86400, 3600, 60, 1))) if m else 0
    anos = {}
    for i in range(0, len(ids), 50):
        for it in yd("videos", part="contentDetails,snippet,liveStreamingDetails", id=",".join(ids[i:i + 50])).get("items", []):
            if "duration" not in it.get("contentDetails", {}):   # live agendada ou vídeo processando
                continue
            pub = it["snippet"]["publishedAt"][:10]; d = dur(it["contentDetails"]["duration"])
            lim = 180 if pub >= "2024-10-15" else 60          # Short: 60 s até out/2024, 180 s depois
            marcado_live = "liveStreamingDetails" in it
            if d <= lim:
                k = "short"
            elif marcado_live and LIVE_TXT.search(it["snippet"]["title"]):
                k = "live"
            else:
                k = "editado"                                  # upload normal ou estreia de vídeo editado
            a = anos.setdefault(pub[:4], {"short": 0, "live": 0, "editado": 0, "estreia": 0, "dur_editado": []})
            a[k] += 1
            if k == "editado" and marcado_live:
                a["estreia"] += 1
            if k == "editado":
                a["dur_editado"].append(d / 60)
    out = []
    for y in sorted(anos):
        a = anos[y]; v = sorted(a.pop("dur_editado"))
        if int(y) < 2021:                                    # antes de 2021 o canal publicava pouco: amostra fraca
            continue
        out.append({"ano": int(y), **a, "media_min": sum(v) / len(v) if v else 0,
                    "mediana_min": v[len(v) // 2] if v else 0})
    return out


def base_videos():
    """yt_base_videos.csv (classificar_videos.py): uploads de ago/2025 em diante com analytics por vídeo."""
    import csv
    return [x for x in csv.DictReader(open(VENDAS_DATA / "yt_base_videos.csv", encoding="utf-8")) if x["an_minutos"]]


def formato(x):
    """Formato de um vídeo da base: separa estreia (vídeo editado) de live de verdade."""
    if x["tipo"] != "live":
        return x["tipo"]
    return "live" if (LIVE_TXT.search(x["titulo"]) or x["serie"] in SERIES_LIVE) else "estreia"


EDITADOS = ("estreia", "medio (10-25min)", "longo (>25min)")


def mix_formato(base):
    """Onde vai o esforço: % dos uploads × % dos minutos × % dos inscritos, por formato."""
    f = lambda x, k: float(x[k] or 0)
    nome = {"live": "lives", "estreia": "vídeos editados lançados como estreia", "medio (10-25min)": "vídeos de 10 a 25 min", "longo (>25min)": "vídeos de mais de 25 min",
            "corte (1-10min)": "cortes de 1 a 10 min", "short": "Shorts", "institucional/teaser": "institucional e teaser"}
    tu, tm, ts = len(base), sum(f(x, "an_minutos") for x in base), sum(f(x, "an_inscritos_ganhos") for x in base)
    grupos = {}
    for x in base:
        grupos.setdefault(formato(x), []).append(x)
    out = [{"formato": nome.get(k, k), "uploads": len(v), "p_uploads": len(v) / tu,
            "p_minutos": sum(f(x, "an_minutos") for x in v) / tm,
            "p_inscritos": sum(f(x, "an_inscritos_ganhos") for x in v) / ts} for k, v in grupos.items()]
    return {"janela": [min(x["publicado"] for x in base), max(x["publicado"] for x in base)],
            "n": tu, "formatos": sorted(out, key=lambda r: -r["p_minutos"])}


def series_vs_avulso(base):
    """Programa × avulso, comparando dentro do mesmo formato: vídeo editado (estreia + upload) e live."""
    import statistics as st
    f = lambda x, k: float(x[k] or 0)
    prog = [x for x in base if x["camada"] == "PROGRAMA"]
    avulso = lambda x: x["serie"] in ("", "Avulso")
    med = lambda xs, k: st.median(f(x, k) for x in xs) if xs else 0
    def compara(xs):
        ser, avu = [x for x in xs if not avulso(x)], [x for x in xs if avulso(x)]
        return {"serie": {"n": len(ser), "min_video": med(ser, "an_minutos"), "insc_video": med(ser, "an_inscritos_ganhos")},
                "avulso": {"n": len(avu), "min_video": med(avu, "an_minutos"), "insc_video": med(avu, "an_inscritos_ganhos")}}
    por_serie = {}
    for x in prog:
        if not avulso(x):
            por_serie[x["serie"]] = por_serie.get(x["serie"], 0) + 1
    editados = [x for x in prog if formato(x) in EDITADOS]
    return {
        "p_avulso_programa": sum(1 for x in prog if avulso(x)) / len(prog),
        "n_programa": len(prog),
        "editados": {**compara(editados), "n": len(editados), "avulsos": sum(1 for x in editados if avulso(x))},
        "lives": compara([x for x in prog if formato(x) == "live"]),
        "series": sorted(por_serie.items(), key=lambda kv: -kv[1]),
    }


def ciclo_de_vida(base):
    """Notícia (pico rápido) × atemporal (cauda) × meio-termo, pelos 14 primeiros dias de cada vídeo.

    Série vídeo × dia = top-200 do dia por minutos (fetch_video_semanal.py). Vídeo pequeno some do top-200
    e pareceria "pico rápido" por artefato — por isso só entram vídeos com 30 mil views ou mais em 14 dias.
    """
    import csv, datetime as dt, statistics as st
    ser = {}
    for x in csv.DictReader(open(VENDAS_DATA / "yt_video_diario.csv", encoding="utf-8")):
        ser.setdefault(x["video_id"], {})[x["dia"]] = float(x["views"] or 0)
    fim = max(d for s in ser.values() for d in s)
    f = lambda x, k: float(x[k] or 0)
    classes = {}
    exemplos = {}
    for b in base:
        if b["tipo"] in ("short", "institucional/teaser") or b["video_id"] not in ser:
            continue
        p = dt.date.fromisoformat(b["publicado"])
        if (dt.date.fromisoformat(fim) - p).days < 14:
            continue
        dias = [ser[b["video_id"]].get(str(p + dt.timedelta(days=i)), 0) for i in range(14)]
        t = sum(dias)
        if t < 30000:
            continue
        d3, cauda = sum(dias[:3]) / t, sum(dias[7:]) / t
        k = "noticia" if d3 >= .80 else ("atemporal" if cauda >= .25 else "meio")
        classes.setdefault(k, []).append(b)
        exemplos.setdefault(k, []).append((t, b["titulo"], b["video_id"]))
    tot = sum(len(v) for v in classes.values())
    out = {}
    for k, v in classes.items():
        out[k] = {"n": len(v), "p": len(v) / tot,
                  "insc_por_mil": sum(f(x, "an_inscritos_ganhos") for x in v) / sum(f(x, "an_views") for x in v) * 1000,
                  "min_video": st.median(f(x, "an_minutos") for x in v),
                  "exemplos": [{"titulo": t_, "id": i_} for _, t_, i_ in sorted(exemplos[k], reverse=True)[:3]]}
    return {"n": tot, "dados_ate": fim, "classes": out}


def abertura(D):
    """Retenção relativa à plataforma: primeiros 10% do vídeo × o resto (curvas já coletadas em D['retencao'])."""
    meta = {t["id"]: t for t in D["top_longos"] + D["top_shorts"]}
    out = []
    for vid, cur in D["retencao"].items():
        t = meta.get(vid)
        if not t or t["grupo"] != "longos" or t["dur_s"] > 4 * 3600:   # live de horas distorce o "início"
            continue
        w = sorted(cur, key=lambda p: p["x"])
        ini = [p["rel"] for p in w if p["x"] <= .10 and p["rel"] is not None]
        resto = [p["rel"] for p in w if p["x"] > .10 and p["rel"] is not None]
        i30 = min(100, max(1, round(30 / t["dur_s"] * 100)))
        out.append({"id": vid, "titulo": t["titulo"], "dur_s": t["dur_s"],
                    "ret_30s": min(w, key=lambda p: abs(p["x"] * 100 - i30))["w"],
                    "rel_inicio": sum(ini) / len(ini), "rel_resto": sum(resto) / len(resto)})
    return out


def avd_editado_vs_live(base):
    """Duração média assistida: vídeo editado × live (base por vídeo, minutos ÷ views)."""
    f = lambda x, k: float(x[k] or 0)
    ed = [x for x in base if formato(x) in EDITADOS + ("corte (1-10min)",)]
    lv = [x for x in base if formato(x) == "live"]
    avd = lambda xs: sum(f(x, "an_minutos") for x in xs) / sum(f(x, "an_views") for x in xs) * 60
    ed10 = [x for x in base if formato(x) in EDITADOS]
    return {"editado_s": avd(ed), "editado_10min_s": avd(ed10), "live_s": avd(lv)}


def capitulos_e_playlists(ano_ini="2026-01-01"):
    """% de vídeos com capítulos (regra do YouTube: começa em 0:00 e tem 3+ marcas) por formato, e as
    playlists do canal marcadas como podcast — no app de TV elas viram programa, com temporadas e aba própria."""
    import re
    pl = yd("channels", part="contentDetails", id=CHANNEL_ID)["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], ""
    while True:
        kw = {"pageToken": tok} if tok else {}
        d = yd("playlistItems", part="contentDetails", playlistId=pl, maxResults=50, **kw)
        lote = [(i["contentDetails"]["videoId"], i["contentDetails"].get("videoPublishedAt", "")) for i in d["items"]]
        ids += [v for v, p in lote if p >= ano_ini]
        tok = d.get("nextPageToken")
        if not tok or min(p for _, p in lote) < ano_ini:
            break
    ts = re.compile(r"(?<![\d:])(\d{1,2}:\d{2}(?::\d{2})?)(?![\d:])")
    def tem_cap(desc):
        m = ts.findall(desc or "")
        return len(m) >= 3 and m[0] in ("0:00", "00:00", "0:00:00", "00:00:00")
    def dur(iso):
        m = re.search(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?", iso or "")
        return sum(float(x or 0) * k for x, k in zip(m.groups(), (86400, 3600, 60, 1))) if m else 0
    cont = {}
    for i in range(0, len(ids), 50):
        for it in yd("videos", part="snippet,contentDetails,liveStreamingDetails", id=",".join(ids[i:i + 50])).get("items", []):
            d = dur(it["contentDetails"].get("duration"))
            if not d or d <= 180:
                continue
            live = "liveStreamingDetails" in it
            k = ("live" if LIVE_TXT.search(it["snippet"]["title"]) else "estreia") if live else ("upload" if d >= 600 else "corte")
            c = cont.setdefault(k, [0, 0]); c[0] += 1; c[1] += tem_cap(it["snippet"].get("description"))
    pls, tok = [], ""
    while True:
        kw = {"pageToken": tok} if tok else {}
        d = yd("playlists", part="snippet,status,contentDetails", channelId=CHANNEL_ID, maxResults=50, **kw)
        pls += d["items"]; tok = d.get("nextPageToken")
        if not tok:
            break
    lista = [{"titulo": p["snippet"]["title"], "videos": p["contentDetails"]["itemCount"],
              "podcast": p["status"].get("podcastStatus") == "enabled"} for p in pls]
    return {"capitulos": {k: {"n": n, "p": c / n} for k, (n, c) in cont.items()},
            "playlists": {"n": len(lista), "podcast": [x for x in lista if x["podcast"]],
                          "maiores_sem_podcast": sorted([x for x in lista if not x["podcast"]], key=lambda x: -x["videos"])[:8]}}


def avd_vod_por_ano():
    """Tempo assistido por view engajada do vídeo sob demanda (sem lives e sem Shorts), por ano — OAuth."""
    out = []
    hoje = datetime.date.today()
    for ano in range(2021, hoje.year + 1):
        fim = f"{ano}-12-31" if ano < hoje.year else str(hoje - datetime.timedelta(days=3))
        rows, _ = ya(startDate=f"{ano}-01-01", endDate=fim, dimensions="creatorContentType",
                     metrics="engagedViews,estimatedMinutesWatched")
        d = {t: (e, m) for t, e, m in rows}
        e, m = d.get("videoOnDemand", (0, 0))
        el, ml = d.get("liveStream", (0, 0))
        out.append({"ano": ano, "vod_s": m / e * 60 if e else 0, "live_s": ml / el * 60 if el else 0})
    return out


def paises(ini, fim, top_videos=()):
    """Audiência por país: canal e os vídeos de maior alcance (hispânicos × lusófonos) — OAuth."""
    def dist(filtro=None):
        kw = {"filters": filtro} if filtro else {}
        rows, _ = ya(startDate=ini, endDate=fim, dimensions="country", metrics="engagedViews",
                     sort="-engagedViews", maxResults=200, **kw)
        tot = sum(r[1] for r in rows) or 1
        return {"BR": sum(r[1] for r in rows if r[0] == "BR") / tot,
                "lusofonos": sum(r[1] for r in rows if r[0] in LUSOFONOS) / tot,
                "hispanos": sum(r[1] for r in rows if r[0] in HISPANOS) / tot,
                "n_paises": len(rows), "top": [[r[0], r[1] / tot] for r in rows[:8]]}
    return {"canal": dist(),
            "videos": [{"id": t["id"], "titulo": t["titulo"], **dist(f"video=={t['id']}")} for t in top_videos]}


def busca_termos(ini, fim):
    """Top 25 termos de busca no YouTube que trouxeram views, em três tipos:
    marca = procura pela BP ou por um programa do canal; titulo = nome de uma produção original BP
    (queries/titulos_originais.sql); tema = procura por um assunto em que aparecemos."""
    import re, unicodedata
    norm = lambda t: unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    rows, _ = ya(startDate=ini, endDate=fim, dimensions="insightTrafficSourceDetail", metrics="views",
                 filters="insightTrafficSourceType==YT_SEARCH", sort="-views", maxResults=25)
    marca = re.compile(r"brasil paralelo|paralela|rasta news|\bbp\b", re.I)
    chaves = set()
    for r in bq((QDIR / "titulos_originais.sql").read_text()):
        k = norm(re.split(r"\s*[:|]\s*|\s+-\s+", r["nm_playlist"])[0]).strip()
        if len(k.split()) >= 2 or len(k) >= 8:         # "Brasil" sozinho capturaria tudo
            chaves.add(k)
    def tipo(t):
        if marca.search(t):
            return "marca"
        n = norm(t)
        return "titulo" if any(k in n for k in chaves) else "tema"
    termos = [{"termo": t, "views": v, "tipo": tipo(t)} for t, v in rows]
    tot = sum(t["views"] for t in termos) or 1
    share = lambda k: sum(t["views"] for t in termos if t["tipo"] == k) / tot
    return {"termos": termos, "p_marca": share("marca"), "p_titulo": share("titulo"), "p_tema": share("tema")}


def mercado(D):
    print("· mercado: histórico de uploads (Data API)…")
    ups = uploads_por_ano()
    base = base_videos()
    print("· mercado: formato, séries, ciclo de vida, abertura…")
    extra = {}
    try:                                   # partes que precisam do OAuth: sem token, o resto do bloco sai igual
        ini, fim = D["meta"]["janela"]["ini"], D["meta"]["janela"]["fim"]
        print("· mercado: tempo assistido por ano, países, termos de busca (OAuth)…")
        extra = {"avd_ano": avd_vod_por_ano(),
                 "paises": paises(ini, fim, D["top_longos"][:6] + D["top_shorts"][:3]),
                 "busca": busca_termos(ini, fim)}
    except Exception as e:
        print(f"  ! sem OAuth, bloco parcial: {str(e)[:120]}", file=sys.stderr)
    return {**extra,
        "bench": BENCH,
        "uploads_ano": ups,
        "mix": mix_formato(base),
        "series": series_vs_avulso(base),
        "ciclo": ciclo_de_vida(base),
        "abertura": abertura(D),
        "avd": avd_editado_vs_live(base),
        "tv": capitulos_e_playlists(),
    }


# ─── build ───────────────────────────────────────────────────────────────────
def build():
    hoje = datetime.date.today()
    fim = ANO_FIM or str(hoje - datetime.timedelta(days=3))
    ini = ANO_INI
    print(f"janela: {ini} → {fim}")

    print("· série diária por tipo…")
    diaria = serie_diaria(ini, fim)
    print("· dispositivo por ano (2021→)…")
    dev_ano = device_por_ano()
    print("· dispositivo por tipo…")
    dev_tipo = device_por_tipo(ini, fim)
    print("· origem de tráfego por tipo…")
    traf = trafego_por_tipo(ini, fim)
    print("· inscrito x não inscrito…")
    ccn = inscrito_vs_novo(ini, fim)
    print("· demografia…")
    demo = demografia(ini, fim)
    print("· top vídeos…")
    tops = top_videos(ini, fim)
    print("· quebra de contagem…")
    qv = quebra_views(ini, fim)

    longos = [t for t in tops if t["grupo"] == "longos"]
    shorts = [t for t in tops if t["grupo"] == "shorts"]
    longos.sort(key=lambda t: -t["e"])
    shorts.sort(key=lambda t: -t["e"])

    print("· público dos membros (BigQuery)…")
    membros = publico_membros()
    print("· dispositivo na plataforma (BigQuery)…")
    plataforma = consumo_plataforma()
    print("· dispositivo de quem chega do YouTube (GA4)…")
    lp = ga4_device(ini, fim)

    print("· retenção (top 8 longos + top 5 shorts)…")
    ret = retencao([t["id"] for t in longos[:8]] + [t["id"] for t in shorts[:5]])

    # agregados por grupo
    def tot(g, campo):
        return sum(d.get(f"{g}_{campo}", 0) for d in diaria)

    resumo = {}
    for g in ("longos", "shorts"):
        v, e, m, s = tot(g, "v"), tot(g, "e"), tot(g, "m"), tot(g, "s")
        resumo[g] = {
            "views": v, "engaged": e, "min": m, "subs": s,
            "min_por_view": (m / e) if e else 0,
            "inflacao": (v / e) if e else 0,
            "subs_por_1k": (s / e * 1000) if e else 0,
        }

    return {
        "meta": {
            "gerado": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "janela": {"ini": ini, "fim": fim},
            "canal": CHANNEL_ID,
            "quebra": QUEBRA,
            "fonte": "YouTube Analytics API v2 + Data API v3",
        },
        "resumo": resumo,
        "diaria": diaria,
        "quebra_views": qv,
        "device_ano": dev_ano,
        "device_tipo": dev_tipo,
        "trafego": traf,
        "ccn": ccn,
        "demografia": demo,
        "top_longos": longos[:15],
        "top_shorts": shorts[:15],
        "retencao": ret,
        "membros": membros,
        "plataforma_device": plataforma,
        "lp_device": lp,
    }


def main():
    if "--so-mercado" in sys.argv:          # recalcula só o bloco de mercado sobre o data.json atual (sem OAuth)
        data = json.loads(OUT.read_text())
        data["mercado"] = mercado(data)
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
        print(f"✓ mercado recalculado em {OUT}")
        return
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))   # grava antes: falha no mercado não perde a coleta
    data["mercado"] = mercado(data)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"\n✓ {OUT} ({OUT.stat().st_size/1024:.0f} KB)")
    r = data["resumo"]
    for g in ("longos", "shorts"):
        x = r[g]
        print(f"  {g:<7} engaged={x['engaged']:>12,.0f}  min={x['min']:>13,.0f}  "
              f"min/view={x['min_por_view']:>6.2f}  inflação={x['inflacao']:.2f}x  "
              f"subs/1k={x['subs_por_1k']:.2f}")

    if "--push" in sys.argv:
        d = Path(__file__).parent
        subprocess.run(["git", "add", "-A", "."], cwd=d, check=True)
        subprocess.run(["git", "commit", "-m", "youtube-canal: refresh data.json"], cwd=d)
        subprocess.run(["git", "push"], cwd=d)


if __name__ == "__main__":
    main()
