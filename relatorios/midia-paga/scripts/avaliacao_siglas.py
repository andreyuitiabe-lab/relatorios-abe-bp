import csv
from collections import defaultdict
from statistics import mean, median

TETO=180
series=defaultdict(list)
with open('siglas4.csv') as f:
    for r in csv.DictReader(f):
        try: sp=float(r['spend']); sa=float(r['sales']); rv=float(r['revenue'])
        except: continue
        series[(r['sigla'],r['tipo'])].append({'d':r['reference_date'],'sp':sp,'sa':sa,'rv':rv})
for k in series: series[k].sort(key=lambda x:x['d'])

def cpa_window(rows): 
    s=sum(x['sp'] for x in rows); v=sum(x['sa'] for x in rows)
    return s/v if v else 9999

def sinalC(ru):
    if len(ru)<5: return None
    cpar=cpa_window(ru[-3:]); base=ru[:-3]
    if sum(x['sa'] for x in base)==0: return None
    ratio=cpar/cpa_window(base)
    return 'reduzir' if ratio>1.30 else 'aumentar' if ratio<0.85 else 'manter'

def regra_absoluta(ru):
    """CPA_3d vs teto + ROAS_3d. Independe de baseline próprio."""
    if len(ru)<3: return None
    l3=ru[-3:]; cpar=cpa_window(l3)
    roas=sum(x['rv'] for x in l3)/sum(x['sp'] for x in l3)
    if cpar>TETO*1.3 and roas<1.0: return 'reduzir'
    if cpar<TETO*0.8 and roas>1.2: return 'aumentar'
    return 'manter'

print(f"{'sigla':>8} {'regra':>10}  {'reduzir: n/ROAS3d':>20}  {'manter':>14}  {'aumentar':>14}")
for (sig,tipo),rows in sorted(series.items()):
    if sum(x['sp'] for x in rows)<100000: continue
    for nome,fn in [('C(rel)',sinalC),('absoluta',regra_absoluta)]:
        b=defaultdict(list)
        for i in range(len(rows)-1):
            fut=rows[i+1:i+4]; spf=sum(x['sp'] for x in fut)
            if spf==0: continue
            roasf=sum(x['rv'] for x in fut)/spf
            s=fn(rows[:i+1])
            if s: b[s].append(roasf)
        def fmt(a):
            v=b[a]; return f"{len(v)}/{median(v):.2f}" if v else "—"
        print(f"{sig+'-'+tipo:>8} {nome:>10}  {fmt('reduzir'):>20}  {fmt('manter'):>14}  {fmt('aumentar'):>14}")
    print()
