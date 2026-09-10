import csv
from collections import defaultdict
from statistics import mean, median

TETO = 180
series = defaultdict(list)
with open('siglas4.csv') as f:
    for r in csv.DictReader(f):
        try:
            sp=float(r['spend']); sa=float(r['sales']); rv=float(r['revenue'])
        except: continue
        series[(r['sigla'], r['tipo'])].append(
            {'d':r['reference_date'],'sp':sp,'sa':sa,'rv':rv})
for k in series: series[k].sort(key=lambda x:x['d'])

def ma(rows, t, key, w=3):
    seg = rows[max(0,t-w+1):t+1]
    return mean(x[key] for x in seg)

def signal_C(rows_until):
    """Abordagem C: ratio CPA_3d / CPA_acum. Precisa >=5 dias e vendas."""
    if len(rows_until) < 5: return None
    last3 = rows_until[-3:]
    sl_r = sum(x['sa'] for x in last3)
    if sl_r == 0: return 'reduzir'  # 3 dias sem venda = claramente cortar
    cpa_r = sum(x['sp'] for x in last3)/sl_r
    base = rows_until[:-3]
    sl_b = sum(x['sa'] for x in base)
    if sl_b == 0: return None
    cpa_b = sum(x['sp'] for x in base)/sl_b
    ratio = cpa_r/cpa_b
    return 'aumentar' if ratio<0.85 else 'reduzir' if ratio>1.30 else 'manter'

for (sig,tipo), rows in sorted(series.items()):
    tot_sp = sum(x['sp'] for x in rows); tot_sa=sum(x['sa'] for x in rows); tot_rv=sum(x['rv'] for x in rows)
    if tot_sp < 20000: continue  # ignora fragmentos
    peak = max(range(len(rows)), key=lambda t: ma(rows,t,'sp'))
    roas = tot_rv/tot_sp; cpa = tot_sp/tot_sa if tot_sa else 0
    print(f"\n{'='*78}\n{sig}-{tipo}  {rows[0]['d']}→{rows[-1]['d']}  {len(rows)}d  "
          f"R${tot_sp/1000:.0f}k  ROAS {roas:.2f}  CPA R${cpa:.0f}  pico dia {peak} ({rows[peak]['d']})")
    # backtest recomendação vs ROAS futuro 3d, por fase
    buckets = defaultdict(list)
    ramp_days = 0
    for i in range(len(rows)-1):
        fut = rows[i+1:i+4]
        sp_f=sum(x['sp'] for x in fut); rv_f=sum(x['rv'] for x in fut)
        if sp_f==0: continue
        roas_f = rv_f/sp_f
        is_ramp = ma(rows,i,'sp') > ma(rows,max(0,i-3),'sp') and i < peak+1
        if is_ramp: ramp_days += 1
        sig_c = signal_C(rows[:i+1])
        phase = 'RAMP(silêncio)' if is_ramp else 'pós-pico'
        if sig_c:
            buckets[(phase, sig_c)].append(roas_f)
    for phase in ['RAMP(silêncio)','pós-pico']:
        line=[]
        for act in ['aumentar','manter','reduzir']:
            v=buckets[(phase,act)]
            if v: line.append(f"{act} n={len(v)} ROAS3d={median(v):.2f}")
        if line: print(f"  [{phase}] " + " | ".join(line))
