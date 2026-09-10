import csv, re, math
from collections import defaultdict
from statistics import mean, median

# ---- séries LAN por sigla (histórico completo) ----
raw=defaultdict(lambda: defaultdict(lambda:[0.0,0.0,0.0]))
with open('camp_daily_full.csv') as f:
    for r in csv.DictReader(f):
        if not r['nm_campaign_name'].startswith('[LAN]'): continue
        m=re.findall(r'\[([^\]]+)\]', r['nm_campaign_name'])
        sig=m[1] if len(m)>1 else '?'
        try: sp=float(r['daily_spend']); sa=float(r['daily_sales']); rv=float(r['daily_revenue'])
        except: continue
        c=raw[sig][r['reference_date']]; c[0]+=sp;c[1]+=sa;c[2]+=rv
lans={}
for sig,dd in raw.items():
    rows=[{'sp':v[0],'rv':v[2]} for d,v in sorted(dd.items()) if v[0]>0]
    if len(rows)>=20 and sum(x['sp'] for x in rows)>=100000: lans[sig]=rows

def fit_power(rows):
    v=[(x['sp'],x['rv']) for x in rows if x['sp']>0 and x['rv']>0]
    if len(v)<5: return None
    n=len(v); lx=[math.log(a) for a,_ in v]; ly=[math.log(b) for _,b in v]
    mx,my=mean(lx),mean(ly)
    den=sum((lx[i]-mx)**2 for i in range(n))
    if den==0: return None
    b=sum((lx[i]-mx)*(ly[i]-my) for i in range(n))/den
    a=math.exp(my-b*mx)
    return (a,b)
def ev(fit,s): a,b=fit; return a*(s**b) if s>0 else 0

# modelos preditivos de retorno_t (out-of-sample, dados até t-1)
def predict(rows, t):
    H=rows[:t]; sp_t=rows[t]['sp']
    if sp_t<=0 or len(H)<8: return None
    out={}
    # M_persist: retorno_t = spend_t * (retorno/spend médio dos últimos 3 dias)  [linear, eficiência recente]
    l3=H[-3:]; eff=sum(x['rv'] for x in l3)/sum(x['sp'] for x in l3) if sum(x['sp'] for x in l3)>0 else None
    if eff: out['persist']=sp_t*eff
    # M_curva_own: curva de potência na própria história (formato + nível fixos)
    f=fit_power(H)
    if f: out['curva_own']=ev(f,sp_t)
    # M_curva_nivel: MESMO formato, nível recalibrado pelos últimos 3 dias (a ideia do André)
    if f:
        betas=[x['rv']/ev(f,x['sp']) for x in l3 if ev(f,x['sp'])>0]
        if betas: out['curva_nivel']=median(betas)*ev(f,sp_t)
    # M_curva_movel: refit da curva só nos últimos 10 dias
    fm=fit_power(H[-10:])
    if fm: out['curva_movel']=ev(fm,sp_t)
    return out, rows[t]['rv']

MODELS=['persist','curva_own','curva_nivel','curva_movel']
err=defaultdict(list)
for sig,rows in lans.items():
    for t in range(8,len(rows)):
        r=predict(rows,t)
        if not r: continue
        preds,actual=r
        if actual<=0: continue
        for m in MODELS:
            if m in preds and preds[m]>0:
                err[m].append(abs(preds[m]-actual)/actual)  # APE

print(f"LANs testadas: {len(lans)} | previsões out-of-sample por modelo")
print(f"\n{'modelo':<14}{'MAPE mediano':>14}{'n':>7}   interpretação")
desc={'persist':'eficiência recente (linear, sem curva)',
      'curva_own':'curva na própria história (formato+nível fixos)',
      'curva_nivel':'curva fixa + nível recalibrado (ideia do André)',
      'curva_movel':'refit da curva nos últimos 10 dias'}
for m in MODELS:
    e=err[m]
    print(f"{m:<14}{median(e):>13.0%}{len(e):>7}   {desc[m]}")

# ===== TESTE DECISIVO: só nos dias em que o INVESTIMENTO muda muito =====
# A curva (concavidade) só se diferencia da reta quando spend_t difere do recente.
print("\n\n=== Só dias com salto de investimento |Δ vs média 3d| >= 25% ===")
err2=defaultdict(list); n_jump=0
for sig,rows in lans.items():
    for t in range(8,len(rows)):
        sp_t=rows[t]['sp']; recent=mean(x['sp'] for x in rows[t-3:t])
        if recent<=0 or abs(sp_t/recent-1)<0.25: continue
        r=predict(rows,t)
        if not r: continue
        preds,actual=r
        if actual<=0: continue
        n_jump+=1
        for m in MODELS:
            if m in preds and preds[m]>0: err2[m].append(abs(preds[m]-actual)/actual)
print(f"dias de salto: {n_jump}")
print(f"{'modelo':<14}{'MAPE mediano':>14}{'n':>7}")
for m in MODELS:
    e=err2[m]
    if e: print(f"{m:<14}{median(e):>13.0%}{len(e):>7}")

# separar saltos pra CIMA (onde concavidade = retorno marginal decrescente deveria ajudar)
print("\n=== Só saltos pra CIMA (>= +25%) — onde a saturação morde ===")
err3=defaultdict(list); nu=0
for sig,rows in lans.items():
    for t in range(8,len(rows)):
        sp_t=rows[t]['sp']; recent=mean(x['sp'] for x in rows[t-3:t])
        if recent<=0 or sp_t/recent-1<0.25: continue
        r=predict(rows,t)
        if not r: continue
        preds,actual=r
        if actual<=0: continue
        nu+=1
        for m in MODELS:
            if m in preds and preds[m]>0: err3[m].append(abs(preds[m]-actual)/actual)
print(f"saltos pra cima: {nu}")
for m in MODELS:
    e=err3[m]
    if e: print(f"{m:<14}{median(e):>13.0%}{len(e):>7}")

# viés: nos saltos pra cima, persist super-prevê retorno? (não desconta saturação)
print("\n=== Viés nos saltos pra cima (previsto/real - 1; +=superestima) ===")
for m in MODELS:
    b=[]
    for sig,rows in lans.items():
        for t in range(8,len(rows)):
            sp_t=rows[t]['sp']; recent=mean(x['sp'] for x in rows[t-3:t])
            if recent<=0 or sp_t/recent-1<0.25: continue
            r=predict(rows,t)
            if not r: continue
            preds,actual=r
            if actual>0 and m in preds and preds[m]>0: b.append(preds[m]/actual-1)
    if b: print(f"{m:<14}{'viés mediano':>0} {median(b):>+7.0%}")
