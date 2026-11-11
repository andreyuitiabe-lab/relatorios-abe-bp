#!/usr/bin/env python3
"""
Ações de influs: realizado × resultado de cada ação.

Usage:
  python3 refresh.py     # roda as queries e regrava data.json (sem commit)

O registro de ações (acoes.json) é mantido à mão a partir do Slack e da planilha
de curadores e afiliados. Os anúncios entram pelo nome do influ no anúncio
(chave_anuncio, regex sobre o nome normalizado) e as vendas de link pelo handle.

Queries rodam pelo cliente Python do BigQuery (ADC, igual ao ~/bin/bqq).
"""

import json, re, sys, datetime, unicodedata, warnings
from pathlib import Path

INI  = "2026-10-01"
HERE = Path(__file__).parent
OUT  = HERE / "data.json"

# influs com anúncio no ar sem ação registrada no período (vêm de campanhas anteriores)
LEGADO = [('lucca', 'Lucca Almeida'), (r'\blara\b', 'Lara Brenner'), ('diego del rio', 'Diego Del Rio'),
  ('murillo capellozzi', 'Murillo Capellozzi'), ('br ?explora', 'BR Explora'), ('jonas ribas', 'Jonas Ribas'),
  ('isa tacaki', 'Isa Tacaki'), ('julliene salviano', 'Julliene Salviano'), ('tamie tominaga', 'Tamie Tominaga'),
  ('firmino', 'Firmino'), ('monica salgado', 'Mônica Salgado'), ('catholic nerd', 'Catholic Nerd'),
  ('stefano tony', 'Stefano Tony'), ('everton miranda', 'Everton Miranda'), ('caio leta', 'Caio Leta'),
  ('alan ghani', 'Alan Ghani'), ('jacque|tenorio', 'Jacque Tenório'), ('wilson pedroso|wilsinho', 'Wilson Pedroso')]

_CLIENT = None

def bq(nome: str, **fmt) -> list[dict]:
    global _CLIENT
    if _CLIENT is None:
        warnings.filterwarnings("ignore")
        from google.cloud import bigquery
        _CLIENT = bigquery.Client(project="bp-datawarehouse")
    sql = (HERE / "queries" / f"{nome}.sql").read_text(encoding="utf-8")
    for k, v in fmt.items():
        sql = sql.replace("{" + k + "}", v)
    return [dict(r.items()) for r in _CLIENT.query(sql).result()]

def norm(s: str) -> str:
    return unicodedata.normalize('NFD', (s or '').lower()).encode('ascii', 'ignore').decode()

def campanha(n: str) -> str:
    s = re.findall(r'\[([a-z0-9-]+)\]', n)
    if 'clu' in s or 'bno26-livros' in s: return 'Clubinho'
    if any(x.startswith('jom') for x in s): return 'Brenda (JOM)'
    if 'par' in s: return 'Paraguai'
    if 'lac' in s: return 'Carlos Lacerda'
    if 'els' in s: return 'El Salvador'
    if 'tlr' in s or 'tlr12' in s: return 'Teller'
    outras = [x for x in s if x not in ('lan', 'ppt', 'bno26', 'bno25', 'venda', 'lead')]
    if 'bno26' in s and not outras: return 'Clubinho'   # livros da Black (cards BNO26-LIVROS)
    return outras[0].upper() if outras else 'Outra'

def f2(v) -> float:
    return round(float(v or 0), 2)

def build() -> dict:
    acoes = json.loads((HERE / "acoes.json").read_text(encoding="utf-8"))
    chaves = sorted({a['chave_anuncio'] for a in acoes if a['chave_anuncio']})
    nome_por_chave = {a['chave_anuncio']: a['influ'] for a in acoes if a['chave_anuncio']}

    print("  anúncios...", flush=True)
    anuncios, by_id = [], {}
    for a in bq("anuncios", INI=INI):
        n = norm(a['anuncio'])
        chave = next((c for c in chaves if re.search(c, n)), '')
        nome = nome_por_chave.get(chave, '')
        if not chave:
            hit = next(((p, nm) for p, nm in LEGADO if re.search(p, n)), None)
            if hit: nome = hit[1]
            elif re.search(r'influ|inlfu', n): nome = '(influ não identificado)'
            else: continue
        r = dict(ad_id=a['ad_id'], anuncio=a['anuncio'], influ=nome, chave=chave, campanha=campanha(n),
                 campanha_meta=a['campanha_meta'], gasto=f2(a['gasto']), receita=f2(a['receita']),
                 vendas=int(a['vendas'] or 0), dias_no_ar=int(a['dias_no_ar'] or 0),
                 primeiro_dia=a['primeiro_dia'] or '', ultimo_dia=a['ultimo_dia'] or '',
                 impressoes=int(a['impressoes'] or 0), cliques=int(a['cliques'] or 0),
                 views_3s=int(a['views_3s'] or 0), thruplays=int(a['thruplays'] or 0), leads=int(a['leads'] or 0))
        anuncios.append(r); by_id[r['ad_id']] = r

    print("  semanal...", flush=True)
    agg = {}
    for s in bq("semanal", INI=INI):
        r = by_id.get(s['ad_id'])
        if not r: continue
        g = agg.setdefault((s['semana'], r['campanha']), [0.0, 0.0])
        g[0] += float(s['gasto'] or 0); g[1] += float(s['receita'] or 0)
    semanal = [dict(semana=sm, campanha=c, gasto=round(g, 2), receita=round(rc, 2))
               for (sm, c), (g, rc) in sorted(agg.items())]

    print("  vendas por link...", flush=True)
    handles = sorted({a['handle_link'] for a in acoes if a['handle_link']})
    got = {l['handle']: l for l in bq("vendas_link", INI=INI, HANDLES=','.join(f"'{h}'" for h in handles))}
    vendas_link = [dict(handle=h, vendas=int(got[h]['vendas']) if h in got else 0,
                        receita=f2(got[h]['receita']) if h in got else 0.0,
                        vendas_organico=int(got[h]['vendas_organico']) if h in got else 0,
                        vendas_publi=int(got[h]['vendas_publi']) if h in got else 0) for h in handles]

    data_max = bq("data_max")[0]['d']
    return {
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "inicio": INI,
        "dados_ate": data_max,
        "acoes": acoes,
        "anuncios": anuncios,
        "semanal": semanal,
        "vendas_link": vendas_link,
    }

if __name__ == "__main__":
    print("Refreshing ações de influs...")
    try:
        data = build()
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"✓ {OUT.name} — {data['updated_at']} · {len(data['anuncios'])} anúncios · dados até {data['dados_ate']}")
    except Exception as e:
        print(f"✗ Erro: {e}", file=sys.stderr)
        sys.exit(1)
