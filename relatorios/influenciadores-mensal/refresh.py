#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fechamento mensal de Influenciadores — refresh de dados.

Usage:
  python refresh.py                  # mês anterior ao atual
  python refresh.py --mes 2026-08    # mês específico
  python refresh.py --mes 2026-08 --ate 2026-09   # vários meses juntos
  python refresh.py --push           # atualiza + git add/commit/push

O que este script FAZ:
  - puxa do BigQuery a mídia, a receita e as peças dos anúncios de influenciador
  - separa receita de peça que rodou no mês x venda atrasada (peça sem gasto)
  - separa venda direta do anúncio x venda fechada pelo time comercial
  - monta data.json

O que este script NÃO faz (e por que):
  - o CACHÊ não existe no BigQuery. Vem de `custo_manual.json`, preenchido à mão
    a partir da aba INFLUENCIADORES do controle de custo variável. Sem a entrada
    do mês em custo_manual.json, o script para e avisa.
  - o TEXTO das páginas é escrito à mão a cada fechamento. O data.json alimenta
    gráficos e tabelas; as frases de análise não. Ao rodar um mês novo, revisar
    index.html e detalhado.html — o console do navegador avisa se a soma do
    data.json divergir dos totais declarados.

⚠️ Usar `bqq` (ADC, não expira). Nunca `bq query` — a credencial do bq CLI expira
   diariamente e falha em sessão não-interativa.
"""
import json, re, subprocess, sys, unicodedata, argparse, datetime
from pathlib import Path

HERE = Path(__file__).parent
TABELA_ADS = "bp-datawarehouse.datamart.dtm_analytics_facebook_ads_funnel"
TABELA_TX  = "bp-datawarehouse.masterdata.fct_transactions"

# nome do influ não é coluna — sai por regex do nm_ad_name. Adicionar nomes novos aqui.
MAPA = [
    (r'murillo capellozzi', 'Murillo Capellozzi'), (r'alam carri',       'Alam Carrion'),
    (r'diego del rio',      'Diego Del Rio'),      (r'josue aragao',     'Josué Aragão'),
    (r'fran otto',          'Fran Otto'),          (r'br ?explora',      'BR Explora'),
    (r'pedro alaer',        'Pedro Alaer'),        (r'arthur sch', 'Arthur Schreiber'),
    (r'julliene salviano',  'Julliene Salviano'),  (r'mayara rann',      'Mayara Ranni'),
    (r'leomar',             'Leomar Segundo'),     (r'tamie tominaga',   'Tamie Tominaga'),
    (r'math colo de deus',  'Math (Colo de Deus)'),(r'stefano tony',     'Stefano Tony'),
    (r'caprine',            'Caprine'),            (r'ticaracaticast',   'Ticaracaticast'),
    (r'nine borges',        'Nine Borges'),        (r'gustavo duarte',   'Gustavo Duarte'),
    (r'lu ruiz',            'Lu Ruiz'),            (r'raphael lima|rafael lima', 'Raphael Lima'),
    (r'gustavo trevisan',   'Gustavo Trevisan'),   (r'francisco litvay', 'Francisco Litvay'),
    (r'yasmin moreira',     'Yasmin Moreira'),     (r'firmino',          'Firmino'),
    (r'ricardo salles',     'Ricardo Salles'),     (r'\blara\b',        'Lara Brenner'),
    (r'everton miranda',    'Everton Miranda'),    (r'\blucca\b',       'Lucca Almeida'),
    (r'sargento wagner',    'Sargento Wagner'),    (r'filipe lourenco',  'Filipe Lourenço'),
    (r'diego machado',      'Diego Machado'),      (r'leandro santos',   'Leandro Santos'),
    (r'beatriz villas',     'Beatriz Villas'),     (r'\bdimas\b',        'Dimas'),
    (r'cabo pires',         'Cabo Pires'),         (r'catholic nerd',    'Catholic Nerd'),
    (r'neto monge',         'Neto Monge'),         (r'rafa z[iu]ca',     'Rafa Zicati'),
    # set/2026 — base já filtrada por "influ", então "alam" solto não pega o perpétuo "alam morte apostolos"
    (r'\balam\b',           'Alam Carrion'),       (r'beijato',          'Roberto Beijato'),
    (r'morgana',            'Morgana Klein'),      (r'ben pontes',       'Ben Pontes'),
    (r'mega ?cinefilo',    'Mega Cinéfilo'),      (r'suely',            'Suely Utiyama'),
    (r'mackenzie',          'Mackenzie'),          (r'camila sande',     'Camila Sande'),
    (r'lucas miranda',      'Lucas Miranda'),      (r'rafael nascimento','Rafael Nascimento'),
    (r'aline magalhaes',    'Aline Magalhães'),    (r'giovanne baruch',  'Giovanne Baruch'),
    (r'alexandre k',      'Alexandre Kennedy'),  (r'jacque|tenorio',   'Jacque Tenório'),
    (r'vitor esprega',      'Vitor Esprega'),      (r'wilson pedroso|wilsinho', 'Wilson Pedroso'),
    (r'monica salgado',     'Mônica Salgado'),     (r'caio leta',        'Caio Leta'),
    (r'henrique felini',    'Henrique Felini'),
    (r'alan ghani',         'Alan Ghani'),         (r'\bnine\b',         'Nine Borges'),
]

# influs com contrato recorrente (fluxo contínuo + Alam) — o toggle "Recorrentes" das páginas
RECORRENTES = ['Alam Carrion', 'Fran Otto', 'Arthur Schreiber', 'Josué Aragão', 'Mayara Ranni']

# siglas de campanha -> nome que o time usa
CAMPANHAS = {
    'ELS': 'El Salvador', 'BP10': 'BP 10 anos', 'ENE': 'Enéas', 'TLR': 'Teller',
    'TLR12': 'Teller', 'FNC': 'Fundação Clássica', 'JOM': 'Jornada', 'ELB26': 'Entre Lobos',
    'CDL': 'Clube do Livro', 'DOM': 'Domingo sem Deus', 'ODD': 'Oficina do Diabo',
    'BMA': 'Banco Master', 'GOD': 'Godo', 'HDF': 'Hidden War', 'D48': 'D48', 'ABC': 'Pedagogia do Abandono',
}

def nome_bonito(ad: str) -> str:
    """'AD303 - [LAN] [ELS] VVS murillo capellozzi 05 influ' -> 'AD303 · El Salvador · Murillo Capellozzi 05'"""
    cod = (re.match(r'\s*(AD\d+)', ad) or [None, ''])[1]
    tags = re.findall(r'\[([A-Z0-9]+)\]', ad)
    sig = next((t for t in tags if t in CAMPANHAS), None)
    corpo = re.sub(r'^\s*AD\d+\s*-\s*', '', ad)
    corpo = re.sub(r'\[[A-Z0-9]+\]', '', corpo)
    corpo = re.sub(r'(?i)\bvvs\b|\binflus?\b|\bvenda\b', '', corpo)
    corpo = re.sub(r'\|', ' ', corpo)
    corpo = re.sub(r'\s+', ' ', corpo).strip(' -·|')
    corpo = ' '.join(p if p.isdigit() or len(p) <= 2 else p[:1].upper() + p[1:] for p in corpo.split())
    partes = [p for p in (cod, CAMPANHAS.get(sig), corpo) if p]
    return ' · '.join(partes)
# peça "escalada" = recebeu esta verba ou mais no mês
CORTE_ESCALADA = 500

def bqq(sql: str) -> list[dict]:
    import csv, io, tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as f:
        out = f.name
    r = subprocess.run(["bqq", "-o", out, "-n", "1"], input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-2000:])
    return list(csv.DictReader(open(out)))

def f(v):
    try: return float(v) if v not in (None, '', 'null', 'NaN') else 0.0
    except (TypeError, ValueError): return 0.0

def norm(s): return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()

def influ_de(ad_name: str) -> str | None:
    a = norm(ad_name)
    for pat, nome in MAPA:
        if re.search(pat, a): return nome
    return None

FILTRO_INFLU = r"""(REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'influ|inlfu')
   OR REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')),
      r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni|alam[ _-]?can?rrion'))"""

def ads_do_mes(ini, fim):
    """1 linha por anúncio (id_advertising). dias_no_ar conta só dia COM impressão."""
    return bqq(f"""
      SELECT id_advertising, ANY_VALUE(nm_ad_name) ad, ANY_VALUE(nm_campaign_name) campanha,
        SUM(COALESCE(vl_amount_spent,0))             spend,
        SUM(COALESCE(vl_total_revenue,0))            receita,
        SUM(COALESCE(vl_direct_revenue,0))           receita_direta,
        SUM(COALESCE(vl_commercial_total_revenue,0)) receita_comercial,
        SUM(COALESCE(qt_total_sales,0))              vendas,
        COUNTIF(COALESCE(qt_impressions,0) > 0)      dias_no_ar
      FROM `{TABELA_ADS}`
      WHERE reference_date BETWEEN '{ini}' AND '{fim}' AND {FILTRO_INFLU}
      GROUP BY id_advertising""")

# mesmos nomes de RECORRENTES, em regex BigQuery (base já filtrada por FILTRO_INFLU)
REGEX_RECORRENTES = r'\balam\b|fran[ _-]?otto|arthur[ _-]?sch|josue[ _-]?aragao|mayara[ _-]?rann'

def serie_ano(ano):
    return bqq(f"""
      WITH b AS (
        SELECT FORMAT_DATE('%Y-%m', reference_date) mes,
          {FILTRO_INFLU} AS is_influ,
          REGEXP_CONTAINS(LOWER(REGEXP_REPLACE(NORMALIZE(nm_ad_name,NFD),r'\pM','')), r'{REGEX_RECORRENTES}') AS is_rec,
          COALESCE(vl_amount_spent,0) s, COALESCE(vl_total_revenue,0) r
        FROM `{TABELA_ADS}`
        WHERE reference_date BETWEEN '{ano}-01-01' AND '{ano}-12-31')
      SELECT mes, ROUND(SUM(IF(is_influ,s,0)),0) spend_influ,
             ROUND(SAFE_DIVIDE(SUM(IF(is_influ,r,0)), SUM(IF(is_influ,s,0))),2) roas,
             ROUND(SUM(IF(is_influ AND is_rec,s,0)),0) spend_rec,
             ROUND(SAFE_DIVIDE(SUM(IF(is_influ AND is_rec,r,0)), SUM(IF(is_influ AND is_rec,s,0))),2) roas_rec,
             ROUND(SAFE_DIVIDE(SUM(r), SUM(s)),2) geral
      FROM b GROUP BY mes ORDER BY mes""")

def outros_caminhos(ini, fim):
    """Venda direta por link do influ e venda indireta por lead de parceria."""
    return bqq(f"""
      SELECT CASE WHEN COALESCE(nm_pptc_tracking_publisher,'')='Influencers'
                    OR STARTS_WITH(COALESCE(nm_pptc_tracking_name,''),'Afiliado')
                  THEN 'link_proprio' ELSE 'lead_parceria' END AS caminho,
             COUNT(*) vendas, ROUND(SUM(vl_payment_gross),2) receita
      FROM `{TABELA_TX}`
      WHERE nm_status='approved' AND bl_is_renovation=FALSE
        AND DATE(dt_ordered_at) BETWEEN '{ini}' AND '{fim}'
        AND (COALESCE(nm_pptc_tracking_publisher,'')='Influencers'
             OR STARTS_WITH(COALESCE(nm_pptc_tracking_name,''),'Afiliado')
             OR (REGEXP_CONTAINS(UPPER(COALESCE(nm_lead_last_tracking,'')), r'INFLU|PARC')
                 AND NOT REGEXP_CONTAINS(LOWER(COALESCE(nm_pptc_utm_medium,'')), r'ads')))
      GROUP BY caminho""")

def media_casa(ini, fim):
    """Retorno de TODA a mídia Meta no período, nas duas réguas (caixa e só peça que rodou)."""
    r = bqq(f"""
      WITH b AS (
        SELECT id_advertising, SUM(COALESCE(vl_amount_spent,0)) s, SUM(COALESCE(vl_total_revenue,0)) r
        FROM `{TABELA_ADS}` WHERE reference_date BETWEEN '{ini}' AND '{fim}' GROUP BY 1)
      SELECT ROUND(SUM(s)) spend, ROUND(SAFE_DIVIDE(SUM(r), SUM(s)), 2) caixa,
             ROUND(SAFE_DIVIDE(SUM(IF(s >= 1, r, 0)), SUM(s)), 2) so_ativas FROM b""")[0]
    return {"spend_meta_total": round(f(r['spend'])), "retorno_medio_casa_caixa": f(r['caixa']),
            "retorno_medio_casa_so_ativas": f(r['so_ativas'])}

def fim_do_mes(mes):
    y, m = map(int, mes.split('-'))
    return (datetime.date(y + (m == 12), (m % 12) + 1, 1) - datetime.timedelta(days=1)).isoformat()

def meses_entre(de, ate):
    y, m = map(int, de.split('-')); out = []
    while f"{y}-{m:02d}" <= ate:
        out.append(f"{y}-{m:02d}"); y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out

def visao(ads, cache, acao_marca, outros, ini, fim):
    """Monta o bloco de números de um recorte (todos os influs ou só os recorrentes).
    `outros` (link próprio / lead de parceria) só existe no recorte geral — não é atribuível a influ."""
    agg = {}
    for r in ads:
        nome = r['_influ']
        d = agg.setdefault(nome, dict(n=nome, s=0.0, f=0.0, ra=0.0, rc=0.0,
                                      rdir=0.0, rcom=0.0, v=0, ads=0, rodou=0, c=''))
        spend = f(r['spend'])
        d['s'] += spend
        d['ra' if spend >= 1 else 'rc'] += f(r['receita'])   # peça que rodou x venda atrasada
        d['rdir'] += f(r['receita_direta']); d['rcom'] += f(r['receita_comercial'])
        d['v'] += int(f(r['vendas'])); d['ads'] += 1
        if spend >= CORTE_ESCALADA: d['rodou'] += 1

    for nome, v in cache.items():
        if nome in agg: agg[nome]['f'] = v
        else:
            print(f"  ⚠️ cachê de {nome} sem anúncio correspondente no período")
            agg[nome] = dict(n=nome, s=0.0, f=v, ra=0.0, rc=0.0, rdir=0.0, rcom=0.0, v=0, ads=0, rodou=0, c='')

    # agrupa a cauda: quem não teve verba nem receita relevante vira uma linha só,
    # senão a tabela do relatório vem com dezenas de linhas de R$ 0 e fica ilegível.
    CORTE_LINHA_PROPRIA = dict(gasto=100, receita=1000)
    grandes, cauda = [], dict(n='Outros influenciadores', s=0.0, f=0.0, ra=0.0, rc=0.0,
                              rdir=0.0, rcom=0.0, v=0, ads=0, rodou=0, c='diversas')
    for d in agg.values():
        if (d['s'] + d['f']) >= CORTE_LINHA_PROPRIA['gasto'] or (d['ra'] + d['rc']) >= CORTE_LINHA_PROPRIA['receita']:
            grandes.append(d)
        else:
            for k in ('s','f','ra','rc','rdir','rcom','v','ads','rodou'): cauda[k] += d[k]
    influs = sorted(grandes, key=lambda d: -(d['s'] + d['f']))
    if cauda['ads']:
        cauda['n'] = f"Outros ({cauda['ads']} peças de {len(agg) - len(grandes)} influenciadores)"
        influs.append(cauda)
    for d in influs:
        for k in ('s', 'f', 'ra', 'rc', 'rdir', 'rcom'): d[k] = round(d[k])
        d['r'] = d['ra'] + d['rc']

    midia = sum(d['s'] for d in influs)
    cache_total = round(sum(cache.values()))
    gasto = midia + cache_total
    rec = sum(d['r'] for d in influs)
    rec_ativa = sum(d['ra'] for d in influs)
    rec_direta = sum(d['rdir'] for d in influs)
    div = lambda a, b: round(a / b, 2) if b else None

    ads_top = sorted(ads, key=lambda r: -f(r['receita']))[:12]
    camps = {}
    for r in ads:
        tags = re.findall(r'\[([A-Z0-9]+)\]', r['ad'])
        sig = next((t for t in tags if t not in ('LAN', 'PPT', 'BNO25', 'BIT')), tags[0] if tags else '?')
        nome = CAMPANHAS.get(sig, sig)
        c = camps.setdefault(nome, {'n': nome, 's': 0.0, 'r': 0.0, 'v': 0})
        c['s'] += f(r['spend']); c['r'] += f(r['receita']); c['v'] += int(f(r['vendas']))

    receita = {"anuncio_total": rec, "anuncio_direto": rec_direta,
               "anuncio_comercial": rec - rec_direta,
               "vendas_total": sum(d['v'] for d in influs),
               "peca_que_rodou": rec_ativa, "venda_atrasada": rec - rec_ativa}
    if outros is not None:
        link = f(outros.get('link_proprio', {}).get('receita'))
        lead = f(outros.get('lead_parceria', {}).get('receita'))
        receita.update({"lead_parceria": round(lead), "link_proprio": round(link),
                        "canal_total": round(rec + lead + link),
                        "vendas_lead_parceria": int(f(outros.get('lead_parceria', {}).get('vendas'))),
                        "vendas_link_proprio": int(f(outros.get('link_proprio', {}).get('vendas')))})
    return {
        "gasto": {"midia": midia, "cache": cache_total, "total": gasto,
                  "acao_de_marca": round(acao_marca),
                  "total_com_acao_marca": round(gasto + acao_marca),
                  "retorno_com_acao_marca": div(rec, gasto + acao_marca)},
        "receita": receita,
        "retorno": {"caixa": div(rec, gasto), "so_pecas_que_rodaram": div(rec_ativa, gasto),
                    "so_direto": div(rec_direta, gasto),
                    "midia_caixa": div(rec, midia), "midia_so_ativas": div(rec_ativa, midia)},
        "pecas": {"no_ar": len(ads),
                  "escaladas": sum(1 for r in ads if f(r['spend']) >= CORTE_ESCALADA),
                  "quase_sem_verba": sum(1 for r in ads if f(r['spend']) < 1)},
        "cache": cache,
        "influs": influs,
        "ads_top": [{"ad": nome_bonito(r['ad']), "n": r['_influ'], "s": round(f(r['spend'])),
                     "r": round(f(r['receita'])), "v": int(f(r['vendas'])), "d": int(f(r['dias_no_ar']))}
                    for r in ads_top],
        "campanhas": sorted(({**c, 's': round(c['s']), 'r': round(c['r'])} for c in camps.values()),
                            key=lambda c: -c['s']),
    }

def cache_do(manual, meses, so=None):
    """Soma o cachê de peça de venda dos meses; `so` restringe a uma lista de nomes."""
    out = {}
    for m in meses:
        for k, v in manual[m]["cache_peca_venda"].items():
            if k.startswith('_') or (so is not None and k not in so): continue
            out[k] = out.get(k, 0) + v
    return out

def recorte(manual, meses, ini, fim, ads, outros):
    acao = sum(v for m in meses for k, v in manual[m]["acao_de_marca"].items() if not k.startswith('_'))
    rec_ads = [r for r in ads if r['_influ'] in RECORRENTES]
    return {
        "todos": visao(ads, cache_do(manual, meses), acao, outros, ini, fim),
        # ação de marca é do canal, não de uma pessoa — fica fora do recorte dos recorrentes
        "recorrentes": visao(rec_ads, cache_do(manual, meses, RECORRENTES), 0, None, ini, fim),
    }

def classifica(ads):
    sem_nome = 0
    for r in ads:
        r['_influ'] = influ_de(r['ad'])
        if r['_influ'] is None:
            sem_nome += 1; r['_influ'] = 'Outros influenciadores'
    return sem_nome

def build(de: str, ate: str):
    meses = meses_entre(de, ate)
    ini, fim = f"{de}-01", fim_do_mes(ate)

    manual = json.loads((HERE / "custo_manual.json").read_text())
    falta = [m for m in meses if m not in manual]
    if falta:
        sys.exit(f"ERRO: {', '.join(falta)} não está em custo_manual.json.\n"
                 f"O cachê não existe no BigQuery — pedir a aba INFLUENCIADORES do controle\n"
                 f"de custo variável e preencher antes de rodar.")

    ads = ads_do_mes(ini, fim)
    print(f"{len(ads)} anúncios de influenciador de {ini} a {fim}")
    sem = classifica(ads)
    if sem:
        print(f"  ⚠️ {sem} anúncios sem influ identificado — conferir e adicionar ao MAPA")
    outros = {r['caminho']: r for r in outros_caminhos(ini, fim)}
    principal = recorte(manual, meses, ini, fim, ads, outros)

    # mês a mês: mesma conta, cada mês isolado (a "peça que rodou" é medida dentro do mês)
    mensal, periodos = {}, {}
    for m in meses:
        mi, mf = f"{m}-01", fim_do_mes(m)
        a = ads_do_mes(mi, mf); classifica(a)
        o = {r['caminho']: r for r in outros_caminhos(mi, mf)}
        v = recorte(manual, [m], mi, mf, a, o)
        mensal[m] = {k: {kk: v[k][kk] for kk in ('gasto', 'receita', 'retorno', 'pecas', 'cache')} for k in v}
        mensal[m]["casa"] = media_casa(mi, mf)
        periodos[m] = {**v, "casa": mensal[m]["casa"]}

    ctx = {"venda_nova": sum(manual[m]["contexto_bp"].get("venda_nova", 0) for m in meses),
           "custo_marginal": sum(manual[m]["contexto_bp"].get("custo_marginal", 0) for m in meses),
           **media_casa(ini, fim)}

    data = {
        "meta": {"periodo": de if de == ate else f"{de}..{ate}", "meses": meses,
                 "apurado_em": datetime.date.today().isoformat(), "recorrentes": RECORRENTES,
                 "fonte_midia": TABELA_ADS, "fonte_venda": TABELA_TX,
                 "fonte_cache": "custo_manual.json (aba INFLUENCIADORES, manual)"},
        **principal["todos"],                      # raiz = recorte "todos" (compatível com as páginas)
        "views": principal,
        "mensal": mensal,
        # recorte completo por período — o botão de mês das páginas troca entre eles
        "periodos": {"total": {**principal, "casa": ctx}, **periodos},
        "contexto_bp": ctx,
        "serie_2026": [{"m": r['mes'][-2:], "s": round(f(r['spend_influ'])), "roas": f(r['roas']),
                        "s_rec": round(f(r['spend_rec'])), "roas_rec": f(r['roas_rec']) if f(r['spend_rec']) >= 100 else None,
                        "geral": f(r['geral'])} for r in serie_ano(ate[:4]) if r['mes'] <= ate],
        "pendencias": [p for m in meses for p in manual[m].get("pendencias", [])],
    }
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    for k, v in principal.items():
        g, r = v['gasto']['total'], v['receita']['anuncio_total']
        print(f"\n[{k}] gasto R$ {g:,.0f} · receita R$ {r:,.0f} · retorno R$ {v['retorno']['caixa']} (caixa)"
              f" / R$ {v['retorno']['so_pecas_que_rodaram']} (só peça que rodou)")
    print(f"casa: {ctx['retorno_medio_casa_caixa']} caixa / {ctx['retorno_medio_casa_so_ativas']} só ativas")
    print("⚠️ O texto das páginas é escrito à mão — revisar index.html e detalhado.html.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mes", help="AAAA-MM inicial (padrão: mês anterior)")
    ap.add_argument("--ate", help="AAAA-MM final, para apurar vários meses juntos (padrão: = --mes)")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    mes = a.mes or (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")
    build(mes, a.ate or mes)
    if a.push:
        subprocess.run(['git', 'add', 'data.json'], cwd=HERE)
        subprocess.run(['git', 'commit', '-m', f'Atualiza dados: influenciadores {mes}'], cwd=HERE)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=HERE)
