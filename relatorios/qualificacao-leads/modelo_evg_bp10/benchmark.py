import pandas as pd, numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler

RNG = 42
df = pd.read_csv("evg_bp10.csv")
y = df['conv'].astype(int).values

# ---- Feature blocks ----
STATUS   = ['st_member_status_at_registration', 'bl_is_new_registration']
SURVEY   = ['renda','relacao_bp','tempo_conhece_bp','fonte_confianca',
            'qtd_streaming','streaming','midia_tradicional','religiao']
CANAL    = ['nm_lead_channel','utm_source','utm_content']
CAMPANHA = ['nm_tag']

# NULO -> categoria '__NA__' (informativo). bl_is_new_registration tratado como categórico tb.
def prep(cols):
    X = df[cols].copy()
    for c in X.columns:
        X[c] = X[c].astype('object').where(X[c].notna(), '__NA__').astype(str)
    return X

blocks = {
    '(i) status'          : STATUS,
    '(ii) survey'         : SURVEY,
    '(iii) status+survey' : STATUS + SURVEY,
    '(iv) tudo'           : STATUS + SURVEY + CANAL + CAMPANHA,
}

def make_model(name):
    if name == 'LogReg':
        return LogisticRegression(max_iter=2000, class_weight='balanced', C=1.0, solver='lbfgs')
    if name == 'RandomForest':
        return RandomForestClassifier(n_estimators=300, max_depth=None, min_samples_leaf=20,
                                      class_weight='balanced', n_jobs=-1, random_state=RNG)
    if name == 'HistGBT':
        # HGBT nao aceita class_weight direto -> usa sample_weight no fit via cross_validate (params)
        return HistGradientBoostingClassifier(random_state=RNG, learning_rate=0.05,
                                              max_iter=400, l2_regularization=1.0)

def build_pipe(cols, model_name):
    # HistGBT exige denso; demais aceitam denso tb. min_frequency=20 controla dimensionalidade.
    dense = (model_name == 'HistGBT')
    ohe = OneHotEncoder(handle_unknown='ignore', min_frequency=20, sparse_output=not dense)
    ct = ColumnTransformer([('cat', ohe, list(range(len(cols))))])
    steps = [('ohe', ct)]
    if model_name == 'LogReg':  # escala p/ estabilizar lbfgs (evita overflow em matmul)
        steps.append(('sc', StandardScaler(with_mean=False)))
    steps.append(('clf', make_model(model_name)))
    return Pipeline(steps)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RNG)
scoring = {'auc':'roc_auc', 'prauc':'average_precision'}

rows = []
for mname in ['LogReg','RandomForest','HistGBT']:
    for bname, cols in blocks.items():
        Xb = prep(cols).values
        pipe = build_pipe(cols, mname)
        fit_params = {}
        if mname == 'HistGBT':
            # sample_weight balanceado manual
            w = np.where(y==1, (len(y)/(2*y.sum())), (len(y)/(2*(len(y)-y.sum()))))
            fit_params = {'clf__sample_weight': w}
        res = cross_validate(pipe, Xb, y, cv=cv, scoring=scoring, n_jobs=-1,
                             params=fit_params if fit_params else None)
        rows.append({
            'modelo': mname, 'bloco': bname,
            'AUC': res['test_auc'].mean(), 'AUC_dp': res['test_auc'].std(),
            'PRAUC': res['test_prauc'].mean(), 'PRAUC_dp': res['test_prauc'].std(),
        })
        print(f"{mname:14s} {bname:22s} AUC={res['test_auc'].mean():.4f}±{res['test_auc'].std():.4f}"
              f"  PR-AUC={res['test_prauc'].mean():.4f}±{res['test_prauc'].std():.4f}")

benchmark = pd.DataFrame(rows)
benchmark.to_csv("benchmark.csv", index=False)
print("\n== salvo benchmark.csv ==")

# ===================== TAREFA A.2: SÓ NÃO MEMBROS, SÓ PESQUISA =====================
print("\n\n===== A.2  NÃO MEMBROS  (só pesquisa) =====")
mask_nm = df['st_member_status_at_registration'].eq('Não Membro').values
y_nm = y[mask_nm]
base_nm = y_nm.mean()
print(f"Não Membros: n={mask_nm.sum()}  taxa base conv={base_nm:.4%}  positivos={y_nm.sum()}")

nm_rows = []
for mname in ['LogReg','RandomForest','HistGBT']:
    Xs = prep(SURVEY).values[mask_nm]
    pipe = build_pipe(SURVEY, mname)
    fit_params = {}
    if mname == 'HistGBT':
        w = np.where(y_nm==1, (len(y_nm)/(2*y_nm.sum())), (len(y_nm)/(2*(len(y_nm)-y_nm.sum()))))
        fit_params = {'clf__sample_weight': w}
    res = cross_validate(pipe, Xs, y_nm, cv=cv, scoring=scoring, n_jobs=-1,
                         params=fit_params if fit_params else None)
    nm_rows.append({'modelo':mname,'bloco':'survey (só Não Membro)',
                    'AUC':res['test_auc'].mean(),'AUC_dp':res['test_auc'].std(),
                    'PRAUC':res['test_prauc'].mean(),'PRAUC_dp':res['test_prauc'].std()})
    print(f"{mname:14s} AUC={res['test_auc'].mean():.4f}±{res['test_auc'].std():.4f}"
          f"  PR-AUC={res['test_prauc'].mean():.4f}±{res['test_prauc'].std():.4f}  (base={base_nm:.4%})")

pd.DataFrame(nm_rows).to_csv("benchmark_naomembros.csv", index=False)

# ===================== TAREFA A.3: LIFT TABLE (melhor modelo SEM nm_tag) =====================
print("\n\n===== A.3  LIFT TABLE (melhor modelo sem nm_tag) =====")
# melhor bloco sem campanha = (iii) status+survey. Escolhe melhor modelo por AUC nesse bloco.
sub = benchmark[benchmark['bloco']=='(iii) status+survey'].sort_values('AUC', ascending=False)
best_model = sub.iloc[0]['modelo']
print(f"Melhor modelo em (iii) status+survey por AUC: {best_model}")

cols = STATUS + SURVEY
Xb = prep(cols).values
# gera scores out-of-fold
from sklearn.model_selection import cross_val_predict
pipe = build_pipe(cols, best_model)
if best_model == 'HistGBT':
    # cross_val_predict nao passa sample_weight facilmente -> refaz manual por fold
    oof = np.zeros(len(y))
    for tr, te in cv.split(Xb, y):
        p = build_pipe(cols, best_model)
        w = np.where(y[tr]==1,(len(y[tr])/(2*y[tr].sum())),(len(y[tr])/(2*(len(y[tr])-y[tr].sum()))))
        p.fit(Xb[tr], y[tr], clf__sample_weight=w)
        oof[te] = p.predict_proba(Xb[te])[:,1]
    scores = oof
else:
    scores = cross_val_predict(pipe, Xb, y, cv=cv, method='predict_proba', n_jobs=-1)[:,1]

lt = pd.DataFrame({'score':scores, 'conv':y})
lt['decil'] = pd.qcut(lt['score'].rank(method='first'), 10, labels=list(range(10,0,-1))).astype(int)
tot_conv = lt['conv'].sum()
g = lt.groupby('decil').agg(n=('conv','size'), vendas=('conv','sum'),
                            conv_real=('conv','mean'),
                            score_min=('score','min'), score_max=('score','max'))
g['pct_das_vendas'] = g['vendas']/tot_conv
g['lift_vs_base'] = g['conv_real']/lt['conv'].mean()
g = g.sort_index()  # decil 1 = melhor
print(g.to_string(formatters={'conv_real':'{:.4%}'.format,'pct_das_vendas':'{:.2%}'.format,'lift_vs_base':'{:.2f}x'.format}))
g.to_csv("lift_table.csv")
print(f"\nTopo 10% (decil 1) concentra {g.loc[1,'pct_das_vendas']*100:.1f}% das vendas")
print(f"Topo 30% (decis 1-3) concentra {g.loc[[1,2,3],'pct_das_vendas'].sum()*100:.1f}% das vendas")
print(f"Metade inferior (decis 6-10) concentra {g.loc[[6,7,8,9,10],'pct_das_vendas'].sum()*100:.1f}% das vendas")
