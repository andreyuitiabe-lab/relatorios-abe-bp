import csv, re, math
from collections import defaultdict
from statistics import mean, median

# séries por (sigla,tipo) — LAN e PPT (PPT vira controle p/ demanda também)
raw=defaultdict(lambda: defaultdict(lambda:[0.0,0.0]))
tipo_of={}
with open('camp_daily_full.csv') as f:
    for r in csv.DictReader(f):
        nm=r['nm_campaign_name']
        tp='LAN' if nm.startswith('[LAN]') else 'PPT' if nm.startswith('[PPT]') else None
        if not tp: continue
        m=re.findall(r'\[([^\]]+)\]', nm); sig=m[1] if len(m)>1 else '?'
        try: sp=float(r['daily_spend']); rv=float(r['daily_revenue'])
        except: continue
        key=(sig,tp); tipo_of[key]=tp
        c=raw[key][r['reference_date']]; c[0]+=sp; c[1]+=rv

series={}
for key,dd in raw.items():
    rows=[(d,v[0],v[1]) for d,v in sorted(dd.items()) if v[0]>0]
    if len(rows)>=10: series[key]=rows
# índice por data->{key: (sp,rv)} p/ controles
bydate=defaultdict(dict)
for key,rows in series.items():
    for d,sp,rv in rows: bydate[d][key]=(sp,rv)

# ---- 1. elasticidade LIMPA dos saltos (demanda controlada por campanhas estáveis do mesmo dia) ----
def stable_ratio_same_day(key, d):
    """mediana do ratio rv_post/rv_pre de campanhas do mesmo tipo estáveis nesse dia — proxy de demanda."""
    tp=tipo_of[key]; ratios=[]
    for k2,rows2 in series.items():
        if k2==key or tipo_of[k2]!=tp: continue
        idx={dd:i for i,(dd,_,_) in enumerate(rows2)}
        if d not in idx: continue
        i=idx[d]
        if i<3 or i+1>=len(rows2): continue
        pre=rows2[i-3:i]; post=rows2[i:i+2]
        sp_pre=mean(x[1] for x in pre); sp_post=mean(x[1] for x in post)
        rv_pre=mean(x[2] for x in pre); rv_post=mean(x[2] for x in post)
        if sp_pre<=0 or rv_pre<=0: continue
        if abs(sp_post/sp_pre-1)>0.10: continue  # controle estável
        ratios.append(rv_post/rv_pre)
    return median(ratios) if len(ratios)>=3 else None

elas_clean=[]; elas_raw=[]
for key,rows in series.items():
    for i in range(3,len(rows)-1):
        pre=rows[i-3:i]; post=rows[i:i+2]
        sp_pre=mean(x[1] for x in pre); sp_post=mean(x[1] for x in post)
        rv_pre=mean(x[2] for x in pre); rv_post=mean(x[2] for x in post)
        if sp_pre<=0 or rv_pre<=0 or rv_post<=0: continue
        jump=sp_post/sp_pre-1
        if abs(jump)<0.25: continue
        # estabilidade base
        if (max(x[1] for x in pre)-min(x[1] for x in pre))/sp_pre>0.5: continue
        e_raw=math.log(rv_post/rv_pre)/math.log(sp_post/sp_pre)
        elas_raw.append(e_raw)
        ctrl=stable_ratio_same_day(key, rows[i][0])
        if ctrl and ctrl>0:
            rv_post_adj=rv_post/ctrl
            if rv_post_adj>0:
                elas_clean.append(math.log(rv_post_adj/rv_pre)/math.log(sp_post/sp_pre))

b_clean=median(elas_clean); b_raw=median(elas_raw)
print(f"Elasticidade (formato da curva, b em retorno=β·invest^b):")
print(f"  b_pooling_LIMPO (saltos, demanda controlada): {b_clean:.2f}  (n={len(elas_clean)})")
print(f"  b_saltos_bruto (sem controle demanda):        {b_raw:.2f}  (n={len(elas_raw)})")

# confundido: fit na trajetória de cada LAN, média
def fit_b(rows):
    v=[(sp,rv) for _,sp,rv in rows if sp>0 and rv>0]
    if len(v)<5: return None
    n=len(v); lx=[math.log(a) for a,_ in v]; ly=[math.log(b) for _,b in v]
    mx,my=mean(lx),mean(ly); den=sum((z-mx)**2 for z in lx)
    return sum((lx[i]-mx)*(ly[i]-my) for i in range(n))/den if den else None
bconf=[fit_b(rows) for key,rows in series.items() if tipo_of[key]=='LAN']
bconf=[b for b in bconf if b is not None]
b_conf=median(bconf)
print(f"  b_confundido (trajetória própria, LANs):      {b_conf:.2f}  (n={len(bconf)})  ← perto de 1 = parece linear")

# ---- 2. teste out-of-sample: retorno_t = β_t · spend_t^b ----
lans={k:v for k,v in series.items() if tipo_of[k]=='LAN' and len(v)>=20 and sum(x[1] for x in v)>=100000}
def test_b(b):
    ape_all=[]; ape_up=[]; bias_up=[]
    for key,rows in lans.items():
        for t in range(8,len(rows)):
            sp_t=rows[t][1]; rv_t=rows[t][2]
            if sp_t<=0 or rv_t<=0: continue
            l3=rows[t-3:t]
            betas=[x[2]/(x[1]**b) for x in l3 if x[1]>0]
            if not betas: continue
            beta=median(betas)
            pred=beta*(sp_t**b)
            if pred<=0: continue
            ape=abs(pred-rv_t)/rv_t; ape_all.append(ape)
            recent=mean(x[1] for x in l3)
            if recent>0 and sp_t/recent-1>=0.25:
                ape_up.append(ape); bias_up.append(pred/rv_t-1)
    return median(ape_all), median(ape_up), median(bias_up), len(ape_up)

print(f"\nTeste out-of-sample (retorno_t = β_t·invest_t^b, β_t=mediana 3d):")
print(f"{'b (formato)':<34}{'MAPE todos':>11}{'MAPE ↑':>9}{'viés ↑':>9}{'n↑':>6}")
for nome,b in [('b=1 (reta/persist)',1.0),(f'b_confundido={b_conf:.2f}',b_conf),
               (f'b_pooling_limpo={b_clean:.2f}',b_clean)]:
    a,u,bi,n=test_b(b)
    print(f"{nome:<34}{a:>10.0%}{u:>9.0%}{bi:>+9.0%}{n:>6}")

print("\n=== Varredura de b: qual concavidade zera o viés de escalar? ===")
print(f"{'b':>6}{'MAPE todos':>12}{'MAPE ↑':>9}{'viés ↑':>9}{'MAPE ↓':>9}{'viés ↓':>9}")
def test_full(b):
    aa=[]; au=[]; bu=[]; ad=[]; bd=[]
    for key,rows in lans.items():
        for t in range(8,len(rows)):
            sp_t=rows[t][1]; rv_t=rows[t][2]
            if sp_t<=0 or rv_t<=0: continue
            l3=rows[t-3:t]; betas=[x[2]/(x[1]**b) for x in l3 if x[1]>0]
            if not betas: continue
            pred=median(betas)*(sp_t**b)
            if pred<=0: continue
            ape=abs(pred-rv_t)/rv_t; aa.append(ape)
            recent=mean(x[1] for x in l3); ch=sp_t/recent-1 if recent>0 else 0
            if ch>=0.25: au.append(ape); bu.append(pred/rv_t-1)
            elif ch<=-0.25: ad.append(ape); bd.append(pred/rv_t-1)
    return (median(aa),median(au),median(bu),median(ad),median(bd))
for b in [0.55,0.60,0.65,0.70,0.75,0.80,0.90,1.0]:
    a,u,bu,d,bd=test_full(b)
    print(f"{b:>6.2f}{a:>11.0%}{u:>9.0%}{bu:>+9.0%}{d:>9.0%}{bd:>+9.0%}")
