import pandas as pd, numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score

RS = 42
df = pd.read_csv('evg_bp10.csv')
base = df['conv'].mean()
print(f'N={len(df)}  base rate conv={base:.5f}')

# --- Features PERMITIDAS (pre-oferta, sem leakage) ---
CAT = ['nm_tag','utm_content','utm_source','nm_lead_channel',
       'st_member_status_at_registration','bl_is_new_registration',
       'renda','relacao_bp','tempo_conhece_bp','fonte_confianca',
       'qtd_streaming','streaming','midia_tradicional','religiao']
# ticket, days_to_purchase, dt_registered_at_br -> EXCLUIDAS
BANNED = ['ticket','days_to_purchase']

def prep(d, cols):
    X = d[cols].copy()
    for c in cols:
        X[c] = X[c].astype('object').where(X[c].notna(), '__NA__').astype(str)
    return X

def build(cols):
    ct = ColumnTransformer([('cat', OneHotEncoder(handle_unknown='ignore'), cols)])
    return Pipeline([('ct', ct),
                     ('clf', LogisticRegression(max_iter=2000, class_weight='balanced', C=1.0))])

y = df['conv'].astype(int)

# ============================================================
print('\n===== PARTE 1: LEAKAGE =====')
# 1a) confirmar ticket/days_to_purchase pos-conversao
for c in BANNED:
    nn0 = df.loc[y==0, c].notna().mean()
    nn1 = df.loc[y==1, c].notna().mean()
    print(f'[1a] {c}: nao-nulo em conv=0 -> {nn0:.4f} | conv=1 -> {nn1:.4f}')

# 1c) responder pesquisa vs conversao
SURVEY = ['renda','relacao_bp','tempo_conhece_bp','fonte_confianca',
          'qtd_streaming','streaming','midia_tradicional','religiao']
respondeu_any = df[SURVEY].notna().any(axis=1)
print(f'\n[1c] cobertura: respondeu >=1 pergunta = {respondeu_any.mean():.4f}')
print(f'[1c] conv | respondeu>=1  = {y[respondeu_any].mean():.5f}  (n={respondeu_any.sum()})')
print(f'[1c] conv | NAO respondeu = {y[~respondeu_any].mean():.5f}  (n={(~respondeu_any).sum()})')
print(f'[1c] lift responder = {y[respondeu_any].mean()/y[~respondeu_any].mean():.2f}x')
# por campanha
for tag in ['EVG','BP10']:
    m = df['nm_tag']==tag
    r = respondeu_any & m
    nr = (~respondeu_any) & m
    print(f'[1c] {tag}: cobertura={respondeu_any[m].mean():.3f} | conv resp={y[r].mean():.5f} vs nao-resp={y[nr].mean():.5f}')

# ============================================================
print('\n===== PARTE 2: AUC melhor modelo SEM nm_tag =====')
cols_no_tag = [c for c in CAT if c != 'nm_tag']
Xtr, Xte, ytr, yte = train_test_split(df, y, test_size=0.30, random_state=RS, stratify=y)
pipe = build(cols_no_tag)
pipe.fit(prep(Xtr, cols_no_tag), ytr)
p = pipe.predict_proba(prep(Xte, cols_no_tag))[:,1]
auc_notag = roc_auc_score(yte, p)
pr_notag = average_precision_score(yte, p)
print(f'[2] AUC (sem nm_tag)   = {auc_notag:.4f}')
print(f'[2] PR-AUC (sem nm_tag)= {pr_notag:.4f}  | base rate teste={yte.mean():.5f}')

# comparacao COM nm_tag
pipe2 = build(CAT); pipe2.fit(prep(Xtr, CAT), ytr)
p2 = pipe2.predict_proba(prep(Xte, CAT))[:,1]
print(f'[2] AUC (com nm_tag)   = {roc_auc_score(yte,p2):.4f}')

# ============================================================
print('\n===== PARTE 3: ROBUSTEZ DESBALANCEADA (PR-AUC vs base) =====')
lift_pr = pr_notag / yte.mean()
print(f'[3] PR-AUC={pr_notag:.4f} vs base={yte.mean():.5f} -> {lift_pr:.1f}x acima do aleatorio')
# lift em ranking: top decis
order = np.argsort(-p)
yte_arr = yte.values[order]
n = len(yte_arr)
for frac in [0.05, 0.10, 0.20]:
    k = int(n*frac)
    cap = yte_arr[:k].sum()/y[yte.index].sum() if False else yte_arr[:k].sum()/yte.sum()
    prec = yte_arr[:k].mean()
    print(f'[3] top {int(frac*100)}%: precisao={prec:.4f} ({prec/yte.mean():.1f}x base) | recall/captura={cap:.3f}')

# ============================================================
print('\n===== PARTE 4: GENERALIZACAO CROSS-CAMPANHA =====')
def cross(train_tag, test_tag):
    tr = df['nm_tag']==train_tag; te = df['nm_tag']==test_tag
    cols = cols_no_tag  # sem nm_tag (constante dentro de cada treino)
    pp = build(cols)
    pp.fit(prep(df[tr], cols), y[tr])
    pd_ = pp.predict_proba(prep(df[te], cols))[:,1]
    auc = roc_auc_score(y[te], pd_)
    pr = average_precision_score(y[te], pd_)
    print(f'[4] treino={train_tag} (n={tr.sum()}, base={y[tr].mean():.4f}) -> teste={test_tag} (n={te.sum()}, base={y[te].mean():.4f}): AUC={auc:.4f} PR-AUC={pr:.4f}')
    return auc
a1 = cross('EVG','BP10')
a2 = cross('BP10','EVG')
# baseline in-campanha (treino/teste mesma campanha, split)
for tag in ['EVG','BP10']:
    m = df['nm_tag']==tag
    dsub = df[m]; ysub = y[m]
    Xtr2,Xte2,ytr2,yte2 = train_test_split(dsub, ysub, test_size=0.3, random_state=RS, stratify=ysub)
    pp = build(cols_no_tag); pp.fit(prep(Xtr2,cols_no_tag), ytr2)
    pin = pp.predict_proba(prep(Xte2,cols_no_tag))[:,1]
    print(f'[4] in-campanha {tag}: AUC={roc_auc_score(yte2,pin):.4f}')
