#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relatório Influenciadores — refresh de dados.

Usage:
  python refresh.py          # roda queries BQ + atualiza data.json
  python refresh.py --push   # atualiza + git add/commit/push

Três fontes (queries/ *.sql):
  1. influs_direto.sql   — vendas por link/página de influ (publisher 'Influencers' + Afiliados)
  2. influs_indireto.sql — lead entrou por parceiro, comprou depois por outro canal
  3. influs_ads.sql      — anúncios pagos com criativo gravado por influ (VVS)

O nome do influenciador é extraído dos trackings por regex (INFLU_MAP / ad_influ_name).
Ao aparecer influ novo com tracking fora dos padrões, adicionar ao INFLU_MAP.
"""
import json, re, subprocess, sys, datetime, unicodedata
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "data.json"

# ─── BQ helper ───────────────────────────────────────────────────────────────
def bq(sql_file: str) -> list[dict]:
    sql = (HERE / "queries" / sql_file).read_text()
    # sql via stdin: comentários '--' no argv quebram o parser de flags do bq
    r = subprocess.run(
        ["bq", "query", "--nouse_legacy_sql", "--format=json",
         "--max_rows=200000", "--project_id=bp-datawarehouse"],
        input=sql, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    out = r.stdout.strip()
    return json.loads(out) if out else []

def fi(v):
    try: return float(v) if v not in (None, "", "null") else 0.0
    except: return 0.0

def norm(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()

# ─── mapa de influenciadores (links diretos) ─────────────────────────────────
INFLU_MAP = [
    (r'panico|\(pan\)|\[pan\]|/pan$|/pan\b', 'Pânico (Jovem Pan)'),
    (r'morning', 'Morning Show (Jovem Pan)'),
    (r'pingos', 'Os Pingos nos Is (Jovem Pan)'),
    (r'jovem.?pan', 'Jovem Pan (outros programas)'),
    (r'oeste', 'Revista Oeste'),
    (r'4x4|4por4', '4x4 Podcast'),
    (r'ticaracaticast', 'Ticaracaticast'),
    (r'linhagem.?geek', 'Linhagem Geek'),
    (r'sem.?filtro', 'Sem Filtro'),
    (r'lacombe', 'Lacombe'),
    (r'gustavo gayer', 'Gustavo Gayer'),
    (r'luiz camargo', 'Luiz Camargo'),
    (r'rodrigo constantino', 'Rodrigo Constantino'),
    (r'joaquin teixeira', 'Joaquin Teixeira'),
    (r'italo marsili', 'Italo Marsili'),
    (r'professor bellei|prof\. bellei', 'Professor Bellei'),
    (r'brasileirinhos', 'Brasileirinhos'),
    (r'lara bren|\[lara\]', 'Lara Brenner'),
    (r'daniel.?alvarenga', 'Daniel Alvarenga'),
    (r'alexandre.?garcia', 'Alexandre Garcia'),
    (r'vlog.?do.?lisboa', 'Vlog do Lisboa'),
    (r'cassia.?kawamura', 'Cassia Kawamura'),
    (r'nanda.?schmidt', 'Nanda Schmidt Baccelli'),
    (r'esquadr.?a?o.?nerdola', 'Esquadrão Nerdola'),
    (r'caio coppolla', 'Caio Coppolla'),
    (r'alvaro siviero', 'Álvaro Siviero'),
    (r'antonia fontenelle', 'Antonia Fontenelle'),
    (r'bruno magalhaes', 'Bruno Magalhães'),
    (r'senso incomum', 'Senso Incomum'),
    (r'pergunte ao rasta', 'Pergunte ao Rasta'),
    (r'rubro negro', 'Rubro Negro'),
    (r'giovanna mel', 'Giovanna Mel'),
    (r'fabiano baldasso', 'Fabiano Baldasso'),
    (r'conexao politica', 'Conexão Política'),
    (r'\biee\b', 'IEE'),
    (r'socialsoul', 'SocialSoul (afiliados)'),
    (r'\[filipe\]', 'Filipe (Barretos)'),
]
NAO_IDENT = 'Parceiros — link genérico (influ não identificado)'

def afiliado_name(t):
    m = re.match(r'Afiliado - ([^-]+?) - ', t)
    return m.group(1).strip() if m else None

def classify_influ(tracking, source=''):
    t, s = norm(tracking), norm(source)
    a = afiliado_name(tracking)
    if a:
        return a
    for rx, name in INFLU_MAP:
        if re.search(rx, t) or re.search(rx, s):
            return name
    m = re.search(r'\|\s*([^|\[\]]+?)\s*$', tracking)
    if m:
        suf = m.group(1).strip()
        if not re.match(r'(?i)a[cç][aã]o|outros|copia|cópia|v\d|teste', suf) and len(suf) > 2:
            return suf.title()
    return None

# ─── campanhas ───────────────────────────────────────────────────────────────
SIGLAS = {
 'VDS':'A Vida dos Santos (2026)','BMA':'Raio-X Banco Master (2026)','DBI':'Congresso Bitcoin (2026)',
 'DOM':'Domingo Sem Deus (2026)','ELS':'El Salvador (2026)','CDL':'Clube do Livro (2026)',
 'EVG':'Brasil Evangélico (2026)','BP10':'BP 10 Anos (2026)','ODD':'Oficina do Diabo (2025)',
 'RIO':'Rio de Janeiro (2025)','BIT':'A Nova Moeda (2025)','MST':'MST (2025)','CPT':'Contraparte (2025)',
 'BPD25':'BPDay 2025','AED':'Anjos e Demônios (2025)','PAP':'Papa (2025)','BPS':'BP Select (2025)',
 'TLR':'Teller (2025)','TLR12':'Teller (2025)','HDF':'História do Fascismo (2025)','VIS':'Visão (2025)',
 'PIN':'Pindorama','GEO':'Cert. Geopolítica (2025)','GOD':'God Complex (2025)','BNO25':'Black Friday 2025',
 'HID':'Hidden War (2025)','NTL25':'Natal 2025','CHO':'The Chosen (2024)','HDC':'História do Comunismo (2024)',
 'MAE':'Especial Mães (2024)','CHI':'China (2024)','FOC':'Face Oculta (2024)','DRS':'O Resgate (2024)',
 'UNI':'Unitopia (2024)','ISR':'From The River To The Sea (2024)','BPD24':'BPDay 2024',
 'BNO24':'Black Friday 2024','NTL24':'Natal 2024','FFS':'Fábrica da Sanidade (2023)','NIC':'Nicarágua (2023)',
 'DIR':'Direita no Brasil (2023)','VNZ':'Venezuela (2023)','LEI':'Aos Amigos, a Lei (2023)',
 'PRO':'Duas Vidas (2023)','BPD23':'BPDay 2023','BNO23':'Black Friday 2023','NTL23':'Natal 2023',
 'OFB':'O Fim da Beleza (2022)','INV':'Invasão Bolchevique (2022)','FEM':'Face Oculta do Feminismo (2022)',
 'ELB':'Entre Lobos (2022)','BPD22':'BPDay 2022','C3P':'Crise dos 3 Poderes (2022)',
 'GDI':'Guerra do Imaginário (2022)','BUC':'Brasil, A Última Cruzada (2022)','TDT':'Teatro das Tesouras (2022)',
 'FAC':'Facada (2022)','BF22':'Black Friday 2022','RET22':'Natal 2022','BNO':'Black Friday 2022',
 'VRG':'Varig (2022)','RET':'Natal 2022','FUT':'Futebol (2022)','NF':'Núcleo Feminino',
 'NTL21':'Natal 2021','BF21':'Black Friday 2021','ODD25':'Oficina do Diabo (2025)',
}
PAGE_CAMPAIGN = [
    (r'teatro-das-tesouras', 'Teatro das Tesouras (2022)'),
    (r'oficina-do-diabo|\bodd\b', 'Oficina do Diabo (2025)'),
    (r'from-the-river|documentario-israel|\bisr\b', 'From The River To The Sea (2024)'),
    (r'unitopia|\buni\b', 'Unitopia (2024)'),
    (r'som-da-liberdade', 'Som da Liberdade (2023)'),
    (r'mes-do-consumidor|semana-do-consumidor|\bsdc\b', 'Mês do Consumidor'),
    (r'black-november|black november|bno2\d|\bbno\b', 'Black Friday'),
    (r'morning-show|pingos-nos-is', 'Ação contínua (programa)'),
    (r'historia-do-comunismo|cadastro-comunismo|\bhdc\b', 'História do Comunismo (2024)'),
    (r'brasil-a-ultima-cruzada', 'Brasil, A Última Cruzada (2022)'),
    (r'3-poderes', 'Crise dos 3 Poderes (2022)'),
    (r'guerra-do-imaginario', 'Guerra do Imaginário (2022)'),
    (r'especial-de-natal|natal', 'Natal'),
    (r'curso-lara-brenner', 'Curso Lara Brenner (2021)'),
    (r'aula-bitcoin', 'Funil Bitcoin (2025)'),
    (r'entre-lobos', 'Entre Lobos (2022)'),
    (r'maria-da-penha', 'Investigação Maria da Penha (2023)'),
    (r'aos-amigos-a-lei', 'Aos Amigos, a Lei (2023)'),
    (r'vitalicio', 'Vitalício'),
    (r'10-reais|10r', 'Oferta R$10'),
    (r'teller|\btlr\b', 'Teller (2025)'),
    (r'marielle', 'Investigação Paralela (2024)'),
    (r'futebol', 'Futebol (2022)'),
    (r'pindorama', 'Pindorama'),
    (r'bpselect|bp-select|\bbps\b', 'BP Select (2025)'),
    (r'\brio\b', 'Rio de Janeiro (2025)'),
    (r'\bevg\b', 'Brasil Evangélico (2026)'),
    (r'\bdom\b', 'Domingo Sem Deus (2026)'),
    (r'\bpap\b|papa', 'Papa (2025)'),
    (r'seja-membro|seja\.membro|pg\. vendas|pagina venda|cupom|barretos|na-lata|sociedade do livro',
     'Sempre ativo (seja-membro)'),
]

def classify_campaign(text):
    for sig in re.findall(r'\[([A-Z0-9]{2,6})\]', text):
        if sig in SIGLAS:
            return SIGLAS[sig]
    t = norm(text)
    for rx, name in PAGE_CAMPAIGN:
        if re.search(rx, t):
            return name
    return 'Outros'

def campaign_from_utm(utm_campaign):
    # campanhas com colchetes ([LAN] [CDL] ...) resolvem direto pela sigla
    r1 = classify_campaign(utm_campaign)
    if r1 != 'Outros':
        return r1
    # códigos minúsculos tipo lan_odd / ppt_10r: strip do prefixo e tenta a sigla
    c = norm(utm_campaign)
    c = re.sub(r'^(lan|ppt|obp|free)_', '', c)
    return classify_campaign('[' + c.upper()[:6].split('_')[0] + '] ' + c)

# ─── criativos de ads ────────────────────────────────────────────────────────
AD_STOP = {'vvs','ps','ads','adapt','premier','react','tela','cena','audio','story','batismo',
           'reformatorio','anjo','guarda','descoberta','influ','influs','venda','melhores',
           'copia','h1','h2','2x','ugc','negacao','hdf','ad','aquecimento','ultimas','ultimos',
           'org','incrivel','filme'}
AD_CANON = {
    'Alam Carriom': 'Alam Carrion', 'Lara Brener': 'Lara Brenner',
    'Segundo Catolico': 'Segundo Católico', 'Opadrepio': 'O Padre Pio',
    'Esquadrao Nerdola': 'Esquadrão Nerdola', 'Sikera Jr': 'Sikêra Jr',
    'Thaina Lummertz': 'Thainá Lummertz', 'Angelo Pinheiro': 'Ângelo Pinheiro',
    'Padre Pio': 'O Padre Pio', 'Melhores': 'Mix Advantage+ (vários influs)',
}
def ad_influ_name(content):
    c = norm(content)
    c = re.sub(r'__\d+.*$', '', c)
    c = re.sub(r'^ad\d+\s*-\s*', '', c)
    c = re.sub(r'\[[^\]]*\]', ' ', c)
    c = c.replace('|', ' ').replace('-', ' ')
    words = [w for w in re.split(r'[_\s]+', c) if w]
    name_words = [w for w in words if w not in AD_STOP and not re.match(r'^v?\d+$', w)]
    if not name_words:
        return None
    name = ' '.join(name_words[:3]).strip()
    if len(name) < 3 or name == 'influencia':
        return None
    return AD_CANON.get(name.title(), name.title())

# ─── agregação ───────────────────────────────────────────────────────────────
def new_bucket():
    return {'qt': 0, 'receita': 0.0, 'anos': defaultdict(float),
            'produtos': defaultdict(float), 'campanhas': defaultdict(float)}

def add(bucket, row, camp):
    bucket['qt'] += int(row['qt'])
    v = fi(row['receita'])
    bucket['receita'] += v
    bucket['anos'][str(row['ano'])] += v
    bucket['produtos'][row['produto']] += v
    bucket['campanhas'][camp] += v

def top(d, n=4):
    return [[k, round(v)] for k, v in sorted(d.items(), key=lambda x: -x[1])[:n]]

def serialize(agg, n_camp=4):
    out = []
    for name, b in sorted(agg.items(), key=lambda x: -x[1]['receita']):
        out.append({
            'nome': name, 'qt': b['qt'], 'receita': round(b['receita']),
            'anos': {k: round(v) for k, v in sorted(b['anos'].items())},
            'produtos': top(b['produtos']), 'campanhas': top(b['campanhas'], n_camp),
        })
    return out

def new_camp():
    return {'qt': 0, 'receita': 0.0, 'direto': 0.0, 'ads': 0.0, 'indireto': 0.0,
            'influs': defaultdict(float)}

def add_camp(camps, camp, tipo, row, influ):
    b = camps[camp]
    v = fi(row['receita'])
    b['qt'] += int(row['qt']); b['receita'] += v; b[tipo] += v
    if influ:  # None = influ não identificado (não polui o top da campanha)
        b['influs'][influ] += v

def build():
    direto, ads, indireto = defaultdict(new_bucket), defaultdict(new_bucket), defaultdict(new_bucket)
    camps = defaultdict(new_camp)

    for r in bq('influs_direto.sql'):
        name = classify_influ(r['tracking_name'], r['utm_source']) or NAO_IDENT
        camp = classify_campaign(r['tracking_name'] + ' ' + r['utm_source'])
        add(direto[name], r, camp)
        add_camp(camps, camp, 'direto', r, name)

    for r in bq('influs_ads.sql'):
        name = ad_influ_name(r['utm_content'])
        camp = campaign_from_utm(r['utm_campaign'])
        add(ads[name or 'Criativo não identificado'], r, camp)
        add_camp(camps, camp, 'ads', r, name)

    for r in bq('influs_indireto.sql'):
        name = classify_influ(r['lead_tracking'])
        camp = classify_campaign(r['lead_tracking'])
        add(indireto[name or camp], r, camp)
        add_camp(camps, camp, 'indireto', r, name)

    anos = sorted({a for g in (direto, ads, indireto) for b in g.values() for a in b['anos']})
    por_ano = [{'ano': a,
                'direto': round(sum(b['anos'].get(a, 0) for b in direto.values())),
                'ads': round(sum(b['anos'].get(a, 0) for b in ads.values())),
                'indireto': round(sum(b['anos'].get(a, 0) for b in indireto.values()))}
               for a in anos]

    por_campanha = [{'nome': c, 'qt': b['qt'], 'receita': round(b['receita']),
                     'direto': round(b['direto']), 'ads': round(b['ads']),
                     'indireto': round(b['indireto']),
                     'influs': [[n, round(v)] for n, v in
                                sorted(b['influs'].items(), key=lambda x: -x[1])
                                if 'não identificado' not in n and 'link genérico' not in n][:5]}
                    for c, b in sorted(camps.items(), key=lambda x: -x[1]['receita'])]

    tot = lambda g: {'qt': sum(b['qt'] for b in g.values()),
                     'receita': round(sum(b['receita'] for b in g.values()))}
    return {
        'updated': datetime.date.today().isoformat(),
        'totais': {'direto': tot(direto), 'ads': tot(ads), 'indireto': tot(indireto)},
        'por_ano': por_ano,
        'por_campanha': por_campanha,
        'direto': serialize(direto),
        'ads': serialize(ads),
        'indireto': serialize(indireto),
    }

if __name__ == '__main__':
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    t = data['totais']
    print(f"data.json atualizado — direto R$ {t['direto']['receita']:,} | "
          f"ads R$ {t['ads']['receita']:,} | indireto R$ {t['indireto']['receita']:,}")
    if '--push' in sys.argv:
        subprocess.run(['git', 'add', 'data.json'], cwd=HERE)
        subprocess.run(['git', 'commit', '-m', 'Atualiza dados: influenciadores'], cwd=HERE)
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=HERE)
