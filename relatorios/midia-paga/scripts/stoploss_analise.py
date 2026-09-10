import csv, re
from collections import defaultdict
from statistics import mean, median

TETO=180
# agrega camp_daily_full por (sigla, tipo) por dia — só LAN
raw=defaultdict(lambda: defaultdict(lambda:[0.0,0.0,0.0]))
with open('camp_daily_full.csv') as f:
    for r in csv.DictReader(f):
        name=r['nm_campaign_name']
        if not name.startswith('[LAN]'): continue
        m=re.findall(r'\[([^\]]+)\]', name)
        sig=m[1] if len(m)>1 else '?'
        try: sp=float(r['daily_spend']); sa=float(r['daily_sales']); rv=float(r['daily_revenue'])
        except: continue
        c=raw[sig][r['reference_date']]; c[0]+=sp; c[1]+=sa; c[2]+=rv

# série por sigla
lans={}
for sig,dd in raw.items():
    rows=[{'d':d,'sp':v[0],'sa':v[1],'rv':v[2]} for d,v in sorted(dd.items()) if v[0]>0]
    if len(rows)>=10 and sum(x['sp'] for x in rows)>=50000:
        lans[sig]=rows
print(f"LANs (sigla-nível, >=10d, >=R$50k): {len(lans)}")

def cpa(rows): 
    v=sum(x['sa'] for x in rows); return sum(x['sp'] for x in rows)/v if v else 9999
def roas(rows):
    s=sum(x['sp'] for x in rows); return sum(x['rv'] for x in rows)/s if s else 0

# destino final: ROAS acumulado da campanha inteira
print(f"\n{'sigla':>6} {'dias':>4} {'R$k':>6} {'ROASfin':>7} | {'CPA d1-3':>8} {'ROASd1-3':>8} {'CPA d1-5':>8} {'ROASd1-5':>8}")
data=[]
for sig,rows in sorted(lans.items(), key=lambda kv:-sum(x['sp'] for x in kv[1])):
    rf=roas(rows); e3=rows[:3]; e5=rows[:5]
    d={'sig':sig,'roas_fin':rf,'cpa3':cpa(e3),'roas3':roas(e3),'cpa5':cpa(e5),'roas5':roas(e5),
       'spend':sum(x['sp'] for x in rows),'n':len(rows)}
    data.append(d)
    print(f"{sig:>6} {d['n']:>4} {d['spend']/1000:>6.0f} {rf:>7.2f} | {d['cpa3']:>8.0f} {d['roas3']:>8.2f} {d['cpa5']:>8.0f} {d['roas5']:>8.2f}")

# poder preditivo: early ROAS vs final. Correlação de Spearman + matriz de decisão
def spearman(xs,ys):
    def rk(v):
        s=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v)
        for p,i in enumerate(s): r[i]=p
        return r
    rx,ry=rk(xs),rk(ys); n=len(xs); mx,my=mean(rx),mean(ry)
    num=sum((rx[i]-mx)*(ry[i]-my) for i in range(n))
    den=(sum((v-mx)**2 for v in rx)*sum((v-my)**2 for v in ry))**.5
    return num/den if den else 0

for k in ['roas3','roas5','cpa3','cpa5']:
    print(f"Spearman({k}, ROAS_final) = {spearman([d[k] for d in data],[d['roas_fin'] for d in data]):+.2f}")

print("\n\n=== CURVA DE DECISÃO STOP-LOSS ===")
print("perdedora = ROAS_final < 1.0 | vencedora = >= 1.0")
losers=[d for d in data if d['roas_fin']<1.0]
winners=[d for d in data if d['roas_fin']>=1.0]
print(f"perdedoras: {len(losers)} | vencedoras: {len(winners)}")

# recomputa ROAS acumulado até dia K por sigla
def roas_upto(sig,K):
    rows=lans[sig][:K]; s=sum(x['sp'] for x in rows)
    return sum(x['rv'] for x in rows)/s if s else 0
def spend_upto(sig,K):
    return sum(x['sp'] for x in lans[sig][:K])

for K in [3,5,7,10]:
    print(f"\n-- corte no dia {K} (ROAS acumulado d1-{K}) --")
    print(f"{'thr':>5} {'recall':>7} {'precis':>7} {'mata vencedoras':>28}")
    for thr in [0.7,0.8,0.9,1.0]:
        flagged=[d['sig'] for d in data if roas_upto(d['sig'],K)<thr]
        tp=[s for s in flagged if any(d['sig']==s and d['roas_fin']<1.0 for d in data)]
        fp=[s for s in flagged if any(d['sig']==s and d['roas_fin']>=1.0 for d in data)]
        rec=len(tp)/len(losers) if losers else 0
        prec=len(tp)/len(flagged) if flagged else 0
        fp_names=[f"{s}({[d['roas_fin'] for d in data if d['sig']==s][0]:.2f})" for s in fp]
        print(f"{thr:>5.1f} {rec:>7.0%} {prec:>7.0%}   {', '.join(fp_names) if fp_names else '—':>28}")

# quanto se economiza: gasto pós-dia-K nas perdedoras (o que o stop-loss pouparia)
print("\n=== POTENCIAL DE ECONOMIA (regra: ROAS_d5 < 0.8 → pivotar) ===")
K=5; thr=0.8
economia=0; perdido=0
for d in data:
    r5=roas_upto(d['sig'],K)
    if r5<thr:
        pos_spend=d['spend']-spend_upto(d['sig'],K)
        if d['roas_fin']<1.0:
            economia+=pos_spend  # gasto que teria sido cortado numa perdedora
        else:
            perdido+=pos_spend   # gasto de vencedora que cortaríamos por engano
print(f"Gasto pós-d{K} em perdedoras flagadas (economia potencial): R${economia/1000:.0f}k")
print(f"Gasto pós-d{K} em vencedoras flagadas (custo do falso positivo): R${perdido/1000:.0f}k")
