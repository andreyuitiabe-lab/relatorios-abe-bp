import csv, re, math
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
    rows=[(sp,rv) for d,(sp,rv) in sorted(dd.items()) if sp>0 and rv>0]
    if len(rows)>=20 and sum(x[0] for x in rows)>=100000: lans[sig]=rows

# β_t = retorno / spend^b
def betas(rows): return [rv/(sp**B) for sp,rv in rows]

# 1. Persistência: autocorrelação de log β
def autocorr(x,lag):
    n=len(x)-lag
    if n<4: return None
    m=mean(x)
    num=sum((x[i]-m)*(x[i+lag]-m) for i in range(n))
    den=sum((v-m)**2 for v in x)
    return num/den if den else None
acs={1:[],3:[],7:[]}
for sig,rows in lans.items():
    lb=[math.log(b) for b in betas(rows) if b>0]
    for lag in acs:
        a=autocorr(lb,lag)
        if a is not None: acs[lag].append(a)
print(f"β_t (n={len(lans)} LANs). Persistência — autocorrelação de log β_t:")
for lag in [1,3,7]:
    print(f"  lag {lag}d: mediana {median(acs[lag]):+.2f}")

# 2. Ciclo de vida: β sobe e cai? pico do β (suavizado MA3) em que fração da campanha
def ma3(x,i): return mean(x[max(0,i-1):i+2])
fr=[]
for sig,rows in lans.items():
    b=betas(rows); sm=[ma3(b,i) for i in range(len(b))]
    pk=max(range(len(sm)),key=lambda i:sm[i])
    fr.append(pk/(len(b)-1))
print(f"\nCiclo de vida — posição do pico de β (0=início,1=fim): mediana {median(fr):.2f}")
print(f"  % campanhas com pico no 1º terço: {sum(1 for x in fr if x<0.33)/len(fr):.0%} | meio: {sum(1 for x in fr if 0.33<=x<0.67)/len(fr):.0%} | fim: {sum(1 for x in fr if x>=0.67)/len(fr):.0%}")

# 3. Backtest de horizonte: prever retorno_{k+h} com spend REAL conhecido, β̂ por método
def fit_logquad(ys):  # log β ~ a + b*t + c*t^2, extrapola
    n=len(ys); xs=list(range(n)); ly=[math.log(y) for y in ys if y>0]
    if len(ly)<n or n<5: 
        ly=[math.log(max(y,1e-9)) for y in ys]
    # normal equations grau 2
    import itertools
    X=[[1,t,t*t] for t in xs]
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
    for i in range(2,-1,-1):
        co[i]=(M[i][3]-sum(M[i][j]*co[j] for j in range(i+1,3)))/M[i][i]
    return co

err=defaultdict(lambda: defaultdict(list))  # method -> horizon -> APE
for sig,rows in lans.items():
    b=betas(rows); n=len(rows)
    for k in range(6,n-1):  # ponto de decisão: histórico [0,k]
        hist=b[:k+1]
        rw=hist[-1]; ew=None
        # EWMA half-life 5d
        alpha=1-0.5**(1/5); e=hist[0]
        for v in hist[1:]: e=alpha*v+(1-alpha)*e
        ew=e
        lq=fit_logquad(hist) if k>=6 else None
        for h in range(1,8):
            j=k+h
            if j>=n: break
            sp_j,rv_j=rows[j]
            for name,bhat in [('rw',rw),('ewma',ew),
                              ('lifecycle',(math.exp(lq[0]+lq[1]*j+lq[2]*j*j) if lq else None))]:
                if bhat and bhat>0:
                    pred=bhat*(sp_j**B)
                    if pred>0: err[name][h].append(abs(pred-rv_j)/rv_j)
print(f"\nForecast de retorno (spend real conhecido) — MAPE mediano por horizonte:")
print(f"{'horizonte':>10}{'random walk':>13}{'EWMA-5d':>10}{'ciclo de vida':>15}")
for h in range(1,8):
    row=f"{h:>8}d "
    for m in ['rw','ewma','lifecycle']:
        e=err[m][h]; row+=f"{(median(e) if e else float('nan')):>{13 if m=='rw' else 10 if m=='ewma' else 15}.0%}"
    print(row)

# 4. Forecast ACUMULADO: da decisão em k, prever SOMA do retorno dos próximos H dias
#    (spend real conhecido, β̂ = último valor / random walk). Erros diários se cancelam?
print("\n=== Forecast ACUMULADO (soma do retorno dos próximos H dias, spend real) ===")
print("   RW: β constante no último valor. Métrica: |previsto-real|/real do TOTAL do bloco")
err_cum=defaultdict(list); err_cum_ew=defaultdict(list)
for sig,rows in lans.items():
    b=betas(rows); n=len(rows)
    for k in range(6,n-1):
        rw=b[k]
        alpha=1-0.5**(1/5); e=b[0]
        for v in b[1:k+1]: e=alpha*v+(1-alpha)*e
        for H in [3,5,7,10,14]:
            if k+H>=n: continue
            real=sum(rows[k+h][1] for h in range(1,H+1))
            pr_rw=sum(rw*(rows[k+h][0]**B) for h in range(1,H+1))
            pr_ew=sum(e*(rows[k+h][0]**B) for h in range(1,H+1))
            if real>0:
                err_cum[H].append(abs(pr_rw-real)/real)
                err_cum_ew[H].append(abs(pr_ew-real)/real)
print(f"{'horizonte':>10}{'MAPE acum (RW)':>16}{'MAPE acum (EWMA)':>18}{'n':>7}")
for H in [3,5,7,10,14]:
    e=err_cum[H]; e2=err_cum_ew[H]
    print(f"{H:>8}d {median(e):>15.0%}{median(e2):>18.0%}{len(e):>7}")

# viés do acumulado (sistemático sobre/sub?) — mediana do sinal
print("\nViés do acumulado (previsto/real - 1; +=superestima), RW:")
for H in [3,7,14]:
    bs=[]
    for sig,rows in lans.items():
        b=betas(rows); n=len(rows)
        for k in range(6,n-1):
            if k+H>=n: continue
            real=sum(rows[k+h][1] for h in range(1,H+1))
            pr=sum(b[k]*(rows[k+h][0]**B) for h in range(1,H+1))
            if real>0: bs.append(pr/real-1)
    print(f"  {H:>2}d: {median(bs):+.0%}")
