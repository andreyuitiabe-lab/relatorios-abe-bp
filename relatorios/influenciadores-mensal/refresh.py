#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fechamento mensal de Influenciadores — refresh de dados.

Usage:
  python refresh.py                  # mês anterior ao atual
  python refresh.py --mes 2026-08    # mês específico
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
    (r'pedro alaer',        'Pedro Alaer'),        (r'arthur schreiber', 'Arthur Schreiber'),
    (r'julliene salviano',  'Julliene Salviano'),  (r'mayara ranni',     'Mayara Ranni'),
    (r'leomar',             'Leomar Segundo'),     (r'tamie tominaga',   'Tamie Tominaga'),
    (r'math colo de deus',  'Math (Colo de Deus)'),(r'stefano tony',     'Stefano Tony'),
    (r'caprine',            'Caprine'),            (r'ticaracaticast',   'Ticaracaticast'),
    (r'nine borges',        'Nine Borges'),        (r'gustavo duarte',   'Gustavo Duarte'),
    (r'lu ruiz',            'Lu Ruiz'),            (r'raphael lima|rafael lima', 'Raphael Lima'),
    (r'gustavo trevisan',   'Gustavo Trevisan'),   (r'francisco litvay', 'Francisco Litvay'),
    (r'yasmin moreira',     'Yasmin Moreira'),     (r'firmino',          'Firmino'),
    (r'ricardo salles',     'Ricardo Salles'),     (r'lara bren',        'Lara Brenner'),
    (r'everton miranda',    'Everton Miranda'),    (r'lucca almeida',    'Lucca Almeida'),
    (r'sargento wagner',    'Sargento Wagner'),    (r'filipe lourenco',  'Filipe Lourenço'),
    (r'diego machado',      'Diego Machado'),      (r'leandro santos',   'Leandro Santos'),
    (r'beatriz villas',     'Beatriz Villas'),     (r'\bdimas\b',        'Dimas'),
    (r'cabo pires',         'Cabo Pires'),         (r'catholic nerd',    'Catholic Nerd'),
    (r'neto monge',         'Neto Monge'),         (r'rafa zicati',      'Rafa Zicati'),
]

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
      r'arthur[ _-]?schreiber|fran[ _-]?otto|lu[ _-]?ruiz|rapha?el[ _-]?lima|josue[ _-]?aragao|mayara[ _-]?ranni'))"""

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

def serie_ano(ano):
    return bqq(f"""
      WITH b AS (
        SELECT FORMAT_DATE('%Y-%m', reference_date) mes,
          {FILTRO_INFLU} AS is_influ,
          COALESCE(vl_amount_spent,0) s, COALESCE(vl_total_revenue,0) r
        FROM `{TABELA_ADS}`
        WHERE reference_date BETWEEN '{ano}-01-01' AND '{ano}-12-31')
      SELECT mes, ROUND(SUM(IF(is_influ,s,0)),0) spend_influ,
             ROUND(SAFE_DIVIDE(SUM(IF(is_influ,r,0)), SUM(IF(is_influ,s,0))),2) roas,
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

def build(mes: str):
    ini = f"{mes}-01"
    y, m = map(int, mes.split('-'))
    fim = (datetime.date(y + (m == 12), (m % 12) + 1, 1) - datetime.timedelta(days=1)).isoformat()

    manual = json.loads((HERE / "custo_manual.json").read_text())
    if mes not in manual:
        sys.exit(f"ERRO: {mes} não está em custo_manual.json.\n"
                 f"O cachê não existe no BigQuery — pedir a aba INFLUENCIADORES do controle\n"
                 f"de custo variável e preencher antes de rodar.")
    mm = manual[mes]
    cache = {k: v for k, v in mm["cache_peca_venda"].items()}
    acao_marca = sum(v for k, v in mm["acao_de_marca"].items() if not k.startswith("_"))

    ads = ads_do_mes(ini, fim)
    print(f"{len(ads)} anúncios de influenciador em {mes}")

    agg, sem_nome = {}, []
    for r in ads:
        nome = influ_de(r['ad'])
        if nome is None:
            sem_nome.append(r); nome = 'Outros influenciadores'
        d = agg.setdefault(nome, dict(n=nome, s=0.0, f=0.0, ra=0.0, rc=0.0,
                                      rdir=0.0, rcom=0.0, v=0, ads=0, rodou=0, c=''))
        spend = f(r['spend'])
        d['s'] += spend
        d['ra' if spend >= 1 else 'rc'] += f(r['receita'])   # peça que rodou x venda atrasada
        d['rdir'] += f(r['receita_direta']); d['rcom'] += f(r['receita_comercial'])
        d['v'] += int(f(r['vendas'])); d['ads'] += 1
        if spend >= CORTE_ESCALADA: d['rodou'] += 1
    if sem_nome:
        print(f"  ⚠️ {len(sem_nome)} anúncios sem influ identificado — conferir e adicionar ao MAPA")

    for nome, v in cache.items():
        if nome in agg: agg[nome]['f'] = v
        else: print(f"  ⚠️ cachê de {nome} sem anúncio correspondente no mês")

    influs = sorted(agg.values(), key=lambda d: -(d['s'] + d['f']))
    for d in influs:
        for k in ('s', 'f', 'ra', 'rc', 'rdir', 'rcom'): d[k] = round(d[k])
        d['r'] = d['ra'] + d['rc']

    midia = sum(d['s'] for d in influs)
    cache_total = sum(cache.values())
    gasto = midia + cache_total
    rec = sum(d['r'] for d in influs)
    rec_ativa = sum(d['ra'] for d in influs)
    rec_direta = sum(d['rdir'] for d in influs)

    outros = {r['caminho']: r for r in outros_caminhos(ini, fim)}
    link = f(outros.get('link_proprio', {}).get('receita'))
    lead = f(outros.get('lead_parceria', {}).get('receita'))

    ads_top = sorted(ads, key=lambda r: -f(r['receita']))[:12]
    camps = {}
    for r in ads:
        tags = re.findall(r'\[([A-Z0-9]+)\]', r['ad'])
        sig = next((t for t in tags if t not in ('LAN', 'PPT', 'BNO25', 'BIT')), tags[0] if tags else '?')
        nome = CAMPANHAS.get(sig, sig)
        c = camps.setdefault(nome, {'n': nome, 's': 0.0, 'r': 0.0, 'v': 0})
        c['s'] += f(r['spend']); c['r'] += f(r['receita']); c['v'] += int(f(r['vendas']))

    data = {
        "meta": {"periodo": mes, "apurado_em": datetime.date.today().isoformat(),
                 "fonte_midia": TABELA_ADS, "fonte_venda": TABELA_TX,
                 "fonte_cache": "custo_manual.json (aba INFLUENCIADORES, manual)"},
        "gasto": {"midia": midia, "cache": cache_total, "total": gasto,
                  "acao_de_marca": round(acao_marca),
                  "total_com_acao_marca": round(gasto + acao_marca),
                  "retorno_com_acao_marca": round(rec / (gasto + acao_marca), 2)},
        "receita": {"anuncio_total": rec, "anuncio_direto": rec_direta,
                    "anuncio_comercial": rec - rec_direta,
                    "vendas_total": sum(d['v'] for d in influs),
                    "lead_parceria": round(lead), "link_proprio": round(link),
                    "canal_total": round(rec + lead + link),
                    "peca_que_rodou": rec_ativa, "venda_atrasada": rec - rec_ativa},
        "retorno": {"caixa": round(rec / gasto, 2),
                    "so_pecas_que_rodaram": round(rec_ativa / gasto, 2),
                    "midia_caixa": round(rec / midia, 2),
                    "midia_so_ativas": round(rec_ativa / midia, 2)},
        "contexto_bp": mm.get("contexto_bp", {}),
        "pecas": {"no_ar": len(ads),
                  "escaladas": sum(1 for r in ads if f(r['spend']) >= CORTE_ESCALADA),
                  "quase_sem_verba": sum(1 for r in ads if f(r['spend']) < 1)},
        "cache": cache,
        "influs": influs,
        "ads_top": [{"ad": nome_bonito(r['ad']), "s": round(f(r['spend'])), "r": round(f(r['receita'])),
                     "v": int(f(r['vendas'])), "d": int(f(r['dias_no_ar']))} for r in ads_top],
        "campanhas": sorted(({**c, 's': round(c['s']), 'r': round(c['r'])} for c in camps.values()),
                            key=lambda c: -c['s']),
        "serie_2026": [{"m": r['mes'][-2:], "s": round(f(r['spend_influ'])),
                        "roas": f(r['roas']), "geral": f(r['geral'])} for r in serie_ano(mes[:4])],
        "pendencias": mm.get("pendencias", []),
    }
    (HERE / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"\ndata.json atualizado — gasto R$ {gasto:,.0f} · receita R$ {rec:,.0f} · "
          f"retorno R$ {rec/gasto:.2f} (caixa) / R$ {rec_ativa/gasto:.2f} (só peça que rodou)")
    print("⚠️ O texto das páginas é escrito à mão — revisar index.html e detalhado.html.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mes", help="AAAA-MM (padrão: mês anterior)")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    mes = a.mes or (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")
    build(mes)
    if a.push:
        subprocess.run(['git', 'add', 'data.json'], cwd=HERE)
        subprocess.run(['git', 'commit', '-m', f'Atualiza dados: influenciadores {mes}'], cwd=HERE)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=HERE)
