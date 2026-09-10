import csv, re, math, json
from collections import defaultdict
from statistics import mean, median
B=0.75
raw=defaultdict(lambda: defaultdict(lambda:[0.0,0.0]))
with open('camp_daily_full.csv') as f:
    for r in csv.DictReader(f):
        if not r['nm_campaign_name'].startswith('[LAN]'): continue
        m=re.findall(r'\[([^\]]+)\]', r['nm_campaign_name']); sig=m[1] if len(m)>1 else '?'
        try: sp=float(r['daily_spend']); rv=float(r['daily_revenue'])
        except: continue
        c=raw[sig][r['reference_date']]; c[0]+=sp; c[1]+=rv
lans={}
for sig,dd in raw.items():
    rows=[(d,sp,rv) for d,(sp,rv) in sorted(dd.items()) if sp>0 and rv>0]
    if len(rows)>=20 and sum(x[1] for x in rows)>=100000: lans[sig]=rows

def betas(rows): return [rv/(sp**B) for _,sp,rv in rows]
out={}
# séries ilustrativas de β_t (normalizado à média p/ comparar formatos)
ex={}
for sig in ['DOM','ELS','TLR']:
    if sig in lans:
        b=betas(lans[sig]); mb=mean(b)
        ex[sig]={'beta':[round(v/mb,2) for v in b],'roas':[round(rv/sp,2) for _,sp,rv in lans[sig]],
                 'n':len(b)}
out['exemplos']=ex

# autocorr
def autocorr(x,lag):
    n=len(x)-lag; m=mean(x)
    if n<4: return None
    num=sum((x[i]-m)*(x[i+lag]-m) for i in range(n)); den=sum((v-m)**2 for v in x)
    return num/den if den else None
acs={}
for lag in [1,2,3,4,5,6,7]:
    vs=[autocorr([math.log(v) for v in betas(r) if v>0],lag) for r in lans.values()]
    vs=[v for v in vs if v is not None]
    acs[lag]=round(median(vs),2)
out['autocorr']=acs

# lifecycle peak dist
fr=[]
for rows in lans.values():
    b=betas(rows); sm=[mean(b[max(0,i-1):i+2]) for i in range(len(b))]
    pk=max(range(len(sm)),key=lambda i:sm[i]); fr.append(pk/(len(b)-1))
out['ciclo']={'terco1':round(sum(1 for x in fr if x<0.33)/len(fr),2),
              'terco2':round(sum(1 for x in fr if 0.33<=x<0.67)/len(fr),2),
              'terco3':round(sum(1 for x in fr if x>=0.67)/len(fr),2),
              'pico_mediano':round(median(fr),2)}

# forecast diário e acumulado
def fit_lq(ys):
    n=len(ys); ly=[math.log(max(y,1e-9)) for y in ys]
    X=[[1,t,t*t] for t in range(n)]
    XtX=[[sum(X[i][a]*X[i][b2] for i in range(n)) for b2 in range(3)] for a in range(3)]
    Xty=[sum(X[i][a]*ly[i] for i in range(n)) for a in range(3)]
    M=[row[:]+[Xty[a]] for a,row in enumerate(XtX)]
    for i in range(3):
        p=max(range(i,3),key=lambda r:abs(M[r][i])); M[i],M[p]=M[p],M[i]
        if abs(M[i][i])<1e-12: return None
        for r in range(i+1,3):
            f=M[r][i]/M[i][i]
            for cc in range(i,4): M[r][cc]-=f*M[i][cc]
    co=[0,0,0]
    for i in range(2,-1,-1): co[i]=(M[i][3]-sum(M[i][j]*co[j] for j in range(i+1,3)))/M[i][i]
    return co
errD=defaultdict(lambda:defaultdict(list)); errC=defaultdict(lambda:defaultdict(list))
for rows in lans.values():
    b=betas(rows); n=len(rows)
    for k in range(6,n-1):
        rw=b[k]; alpha=1-0.5**(1/5); e=b[0]
        for v in b[1:k+1]: e=alpha*v+(1-alpha)*e
        lq=fit_lq(b[:k+1])
        for h in range(1,11):
            j=k+h
            if j>=n: break
            sp_j,rv_j=rows[j][1],rows[j][2]
            for nm,bh in [('rw',rw),('ewma',e),('lifecycle',math.exp(lq[0]+lq[1]*j+lq[2]*j*j) if lq else None)]:
                if bh and bh>0:
                    p=bh*(sp_j**B)
                    if p>0: errD[nm][h].append(abs(p-rv_j)/rv_j)
        for H in [3,5,7,10,14]:
            if k+H>=n: continue
            real=sum(rows[k+h][2] for h in range(1,H+1))
            prw=sum(rw*(rows[k+h][1]**B) for h in range(1,H+1))
            pew=sum(e*(rows[k+h][1]**B) for h in range(1,H+1))
            if real>0:
                errC['rw'][H].append(abs(prw-real)/real); errC['ewma'][H].append(abs(pew-real)/real)
out['diario']={m:{h:round(median(errD[m][h]),2) for h in range(1,11) if errD[m][h]} for m in ['rw','ewma','lifecycle']}
out['acum']={m:{H:round(median(errC[m][H]),2) for H in [3,5,7,10,14]} for m in ['rw','ewma']}
out['n_lans']=len(lans)
json.dump(out,open('forecast_data.json','w'),ensure_ascii=False)
print('n_lans',len(lans),'| exemplos',list(ex.keys()))
print('diario rw:',out['diario']['rw']); print('acum ewma:',out['acum']['ewma'])
