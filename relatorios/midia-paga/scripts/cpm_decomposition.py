"""
Teste da tese LiftLab (two-stage) nos dados BP:
  CAC = CPM / (vendas por mil impressões)
  log(CAC) = log(CPM) - log(SPM)     [SPM = sales per mille]

1. Volatilidade do CPM (portfólio e por campanha)
2. Decomposição da variância do log(CAC): quanto vem do leilão (CPM)
   vs resposta do consumidor (SPM)
3. Elasticidade CPM × spend (escalar encarece o leilão?)
4. Teste direto: power fit vendas~spend vs vendas~impressões (R² pareado)

Resultado (23/jul/2026, 2026-01-01..2026-07-23): tese DESCARTADA — 5% da var(CAC)
vem do CPM; spend fita melhor que impressões em 14/16 campanhas. Ver REFERENCIAS.md.

Input: /tmp/camp_daily_cpm.csv — gerar com a query de all_camps.sql adicionando
SUM(qt_impressions) AS impressions e filtro UPPER(nm_campaign_name) LIKE '%VENDA%'.
"""
import csv, math, sys, os
from collections import defaultdict
from statistics import mean, median, stdev

sys.path.insert(0, '/Users/andre.abe/meu_projeto/relatorios-abe-bp/relatorios/midia-paga/scripts')
from curve_fits import fit_power

PATH = '/tmp/camp_daily_cpm.csv'

rows = []
with open(PATH) as f:
    for r in csv.DictReader(f):
        try:
            sp = float(r['daily_spend']); im = float(r['impressions'])
            sa = float(r['daily_sales']); rv = float(r['daily_revenue'])
        except (ValueError, TypeError):
            continue
        if sp <= 0 or im <= 0:
            continue
        rows.append({'camp': r['nm_campaign_name'], 'date': r['reference_date'],
                     'spend': sp, 'imp': im, 'sales': sa, 'rev': rv})

print(f'Linhas válidas: {len(rows)} | campanhas: {len(set(r["camp"] for r in rows))}')

# ---------- 1. CPM portfólio diário ----------
port = defaultdict(lambda: {'spend': 0, 'imp': 0, 'sales': 0})
for r in rows:
    d = port[r['date']]
    d['spend'] += r['spend']; d['imp'] += r['imp']; d['sales'] += r['sales']

dates = sorted(port)
cpm_p = [port[d]['spend'] / port[d]['imp'] * 1000 for d in dates]
print(f'\n== 1. CPM portfólio ({dates[0]} a {dates[-1]}, {len(dates)} dias) ==')
print(f'CPM: média R${mean(cpm_p):.2f} | mediana R${median(cpm_p):.2f} | '
      f'min R${min(cpm_p):.2f} | max R${max(cpm_p):.2f} | CV {stdev(cpm_p)/mean(cpm_p):.1%}')

# DOW
from datetime import datetime
dow_cpm = defaultdict(list)
for d in dates:
    dow_cpm[datetime.strptime(d, '%Y-%m-%d').weekday()].append(port[d]['spend']/port[d]['imp']*1000)
nm = ['seg','ter','qua','qui','sex','sab','dom']
print('CPM por DOW: ' + ' | '.join(f'{nm[k]} {mean(v):.2f}' for k, v in sorted(dow_cpm.items())))

# ---------- 2. Decomposição var(log CAC) ----------
def decompose(recs, label):
    pts = [(r['spend']/r['imp']*1000, r['sales']/r['imp']*1000, r['spend']/r['sales'])
           for r in recs if r['sales'] > 0]
    if len(pts) < 10:
        return None
    lcpm = [math.log(p[0]) for p in pts]
    lspm = [math.log(p[1]) for p in pts]
    lcac = [math.log(p[2]) for p in pts]
    n = len(pts)
    def var(x):
        m = mean(x); return sum((v-m)**2 for v in x)/(n-1)
    def cov(x, y):
        mx, my = mean(x), mean(y)
        return sum((x[i]-mx)*(y[i]-my) for i in range(n))/(n-1)
    v = var(lcac)
    if v == 0:
        return None
    share_cpm = cov(lcac, lcpm)/v      # atribuição de variância (soma = 1)
    share_spm = -cov(lcac, lspm)/v
    return {'label': label, 'n': n, 'v_cac': v,
            'share_cpm': share_cpm, 'share_spm': share_spm,
            'cv_cpm': math.sqrt(var(lcpm)), 'cv_spm': math.sqrt(var(lspm))}

# portfólio (dias com vendas)
port_recs = [{'spend': port[d]['spend'], 'imp': port[d]['imp'], 'sales': port[d]['sales']}
             for d in dates]
dec = decompose(port_recs, 'PORTFOLIO')
print(f'\n== 2. Decomposição var(log CAC) — log(CAC)=log(CPM)-log(SPM) ==')
print(f'{"nível":<12} {"n":>4} {"sd logCPM":>10} {"sd logSPM":>10} {"% var CAC <- CPM":>17} {"<- SPM":>8}')
print(f'{dec["label"]:<12} {dec["n"]:>4} {dec["cv_cpm"]:>10.3f} {dec["cv_spm"]:>10.3f} '
      f'{dec["share_cpm"]:>16.0%} {dec["share_spm"]:>8.0%}')

# por campanha (>=30 dias com vendas)
camps = defaultdict(list)
for r in rows:
    camps[r['camp']].append(r)
decs = []
for c, recs in camps.items():
    if len([r for r in recs if r['sales'] > 0]) >= 30:
        d = decompose(recs, c)
        if d:
            decs.append(d)
decs.sort(key=lambda d: -d['n'])
print(f'\nPor campanha (≥30 dias c/ vendas, n={len(decs)}):')
print(f'share CPM: mediana {median(d["share_cpm"] for d in decs):.0%} | '
      f'share SPM: mediana {median(d["share_spm"] for d in decs):.0%}')
for d in decs[:8]:
    print(f'  {d["label"][:52]:<52} n={d["n"]:>3} CPM {d["share_cpm"]:>4.0%} SPM {d["share_spm"]:>4.0%}')

# ---------- 3. Elasticidade CPM × spend (within campanha) ----------
elas = []
for c, recs in camps.items():
    if len(recs) < 20:
        continue
    lx = [math.log(r['spend']) for r in recs]
    ly = [math.log(r['spend']/r['imp']*1000) for r in recs]
    n = len(recs)
    mx, my = mean(lx), mean(ly)
    den = sum((x-mx)**2 for x in lx)
    if den == 0:
        continue
    b = sum((lx[i]-mx)*(ly[i]-my) for i in range(n))/den
    elas.append((c, b, n))
print(f'\n== 3. Elasticidade log(CPM)~log(spend) within campanha (≥20 dias, n={len(elas)}) ==')
bs = [e[1] for e in elas]
print(f'mediana {median(bs):+.3f} | p25 {sorted(bs)[len(bs)//4]:+.3f} | p75 {sorted(bs)[3*len(bs)//4]:+.3f}')
print(f'(interpretação: +0.10 = dobrar o gasto encarece o CPM em ~7%)')

# ---------- 4. Power fit: vendas~spend vs vendas~impressões ----------
print(f'\n== 4. R² power fit pareado (campanhas ≥30 dias c/ vendas) ==')
wins_imp, wins_sp, pairs = 0, 0, []
for c, recs in camps.items():
    recs_v = [r for r in recs if r['sales'] > 0]
    if len(recs_v) < 30:
        continue
    f_sp = fit_power([r['spend'] for r in recs_v], [r['sales'] for r in recs_v])
    f_im = fit_power([r['imp'] for r in recs_v], [r['sales'] for r in recs_v])
    if f_sp and f_im:
        pairs.append((c, f_sp['r2'], f_im['r2']))
        if f_im['r2'] > f_sp['r2']:
            wins_imp += 1
        else:
            wins_sp += 1
print(f'campanhas: {len(pairs)} | impressões vence: {wins_imp} | spend vence: {wins_sp}')
print(f'R² mediano — spend: {median(p[1] for p in pairs):.3f} | impressões: {median(p[2] for p in pairs):.3f}')
print(f'delta mediano (imp − spend): {median(p[2]-p[1] for p in pairs):+.3f}')
pairs.sort(key=lambda p: -(p[2]-p[1]))
print('maiores ganhos com impressões:')
for c, r2s, r2i in pairs[:5]:
    print(f'  {c[:52]:<52} spend {r2s:.2f} → imp {r2i:.2f}')
print('maiores perdas:')
for c, r2s, r2i in pairs[-3:]:
    print(f'  {c[:52]:<52} spend {r2s:.2f} → imp {r2i:.2f}')
