import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SC = '/private/tmp/claude-503/-Users-andre-abe-meu-projeto-BigQuery/ea33b6eb-bc28-4984-b504-46e6eb424fae/scratchpad'
np.random.seed(42)

df = pd.read_csv(f'{SC}/evg_bp10.csv')
df['dt'] = pd.to_datetime(df['dt_registered_at_br'], format='ISO8601')
df['week'] = df['dt'].dt.to_period('W').astype(str)

# ---- Features INTRÍNSECAS: status + pesquisa. SEM nm_tag, SEM utm, SEM canal ----
status_cols = ['st_member_status_at_registration', 'bl_is_new_registration']
survey_cols = ['renda', 'relacao_bp', 'tempo_conhece_bp', 'fonte_confianca',
               'qtd_streaming', 'streaming', 'midia_tradicional', 'religiao']
feat_cols = status_cols + survey_cols

X = df[feat_cols].copy()
# NULO como categoria própria '__NA__'
for c in feat_cols:
    X[c] = X[c].astype(str).where(df[c].notna(), '__NA__')
y = df['conv'].values

pre = ColumnTransformer([
    ('oh', OneHotEncoder(handle_unknown='ignore'), feat_cols)
])
clf = Pipeline([
    ('pre', pre),
    ('lr', LogisticRegression(max_iter=2000, class_weight='balanced', C=1.0))
])

# ---- Predições OUT-OF-FOLD (5-fold estratificado) ----
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
oof = cross_val_predict(clf, X, y, cv=cv, method='predict_proba')[:, 1]
df['pscore'] = oof

auc = roc_auc_score(y, oof)
ap = average_precision_score(y, oof)
print(f'=== MODELO INTRÍNSECO (out-of-fold) ===')
print(f'AUC (OOF): {auc:.4f}   AP (OOF): {ap:.4f}   base rate: {y.mean():.4f}')
print(f'score médio previsto: {oof.mean():.4f}  (nota: class_weight=balanced infla o nível absoluto)')
print()

# =========================================================
# GRAIN (a): EVG vs BP10
# =========================================================
print('=== GRAIN (a): EVG vs BP10 ===')
ga = df.groupby('nm_tag').agg(n=('conv','size'), conv_real=('conv','mean'), score_prev=('pscore','mean'))
print(ga)
print()

# =========================================================
# GRAIN (b): por utm_content (adset/criativo) n>=500
# =========================================================
print('=== GRAIN (b): utm_content (n>=500) ===')
gb = df.groupby('utm_content').agg(n=('conv','size'), conv_real=('conv','mean'),
                                   score_prev=('pscore','mean'),
                                   ticket_conv=('ticket','mean'))
gb = gb[gb['n'] >= 500].copy()
print(f'adsets com n>=500: {len(gb)}  (cobrem {gb.n.sum()} leads = {100*gb.n.sum()/len(df):.0f}%)')
rho_b, p_b = spearmanr(gb['score_prev'], gb['conv_real'])
print(f'Spearman(score_prev, conv_real) = {rho_b:.3f}  (p={p_b:.4g}, n={len(gb)} pontos)')
print()
print(gb.sort_values('conv_real', ascending=False).head(15).to_string())
print()

# =========================================================
# GRAIN (c): por semana de cadastro
# =========================================================
print('=== GRAIN (c): por semana ===')
gc = df.groupby('week').agg(n=('conv','size'), conv_real=('conv','mean'), score_prev=('pscore','mean'))
print(gc)
rho_c, p_c = spearmanr(gc['score_prev'], gc['conv_real'])
print(f'Spearman(score_prev, conv_real) = {rho_c:.3f}  (p={p_c:.4g}, n={len(gc)} pontos)')
print()

# =========================================================
# eRPL por adset = P(conv) * ticket_médio_do_segmento
# ticket_médio: usar ticket médio dos convertidos daquele adset; fallback global se sem conv
# =========================================================
print('=== eRPL por adset (n>=500) ===')
global_ticket = df.loc[df.conv==1, 'ticket'].mean()
gb['ticket_seg'] = gb['ticket_conv'].fillna(global_ticket)
gb['eRPL'] = gb['score_prev'] * gb['ticket_seg']
# receita real por lead para comparar
rev_real = df[df.utm_content.isin(gb.index)].groupby('utm_content').apply(
    lambda g: g.loc[g.conv==1,'ticket'].sum() / len(g), include_groups=False)
gb['rev_real_per_lead'] = rev_real

rank_erpl = gb.sort_values('eRPL', ascending=False).reset_index()
rank_vol = gb.sort_values('n', ascending=False).reset_index()
rank_erpl['rank_erpl'] = range(1, len(rank_erpl)+1)
rank_vol['rank_vol'] = range(1, len(rank_vol)+1)

merged = rank_erpl[['utm_content','rank_erpl','eRPL','n','score_prev','ticket_seg','rev_real_per_lead']].merge(
    rank_vol[['utm_content','rank_vol']], on='utm_content')
rho_rank, _ = spearmanr(merged['rank_erpl'], merged['rank_vol'])
print(f'Spearman(rank_eRPL, rank_volume) = {rho_rank:.3f}  (0=ordem independente, 1=idêntica)')
print(f'ticket global convertidos: R$ {global_ticket:.2f}')
print()
print('TOP 10 por eRPL:')
print(merged.sort_values('rank_erpl').head(10)[['utm_content','rank_erpl','rank_vol','eRPL','n','score_prev','ticket_seg','rev_real_per_lead']].to_string(index=False))
print()
print('TOP 10 por VOLUME:')
print(merged.sort_values('rank_vol').head(10)[['utm_content','rank_vol','rank_erpl','eRPL','n','score_prev','ticket_seg','rev_real_per_lead']].to_string(index=False))
print()

# eRPL vs receita real: correlação
rho_erpl_real, p_er = spearmanr(gb['eRPL'], gb['rev_real_per_lead'])
print(f'Spearman(eRPL previsto, receita real/lead) = {rho_erpl_real:.3f} (p={p_er:.4g})')
print()

# =========================================================
# ESTABILIDADE: com quantos leads o read estabiliza?
# Correlação score-real por bucket de tamanho de adset
# =========================================================
print('=== ESTABILIDADE do read por n de leads ===')
for thr in [200, 500, 1000, 2000, 5000]:
    sub = df.groupby('utm_content').agg(n=('conv','size'), cr=('conv','mean'), ps=('pscore','mean'))
    sub = sub[sub.n >= thr]
    if len(sub) >= 4:
        r,_ = spearmanr(sub.ps, sub.cr)
        # erro absoluto médio do read: |conv_real - score reescalado|. Reescala score p/ base rate.
        print(f'  n>={thr}: {len(sub):3d} adsets, Spearman={r:.3f}')
print()

# Simulação: erro do read vs n (bootstrap dentro de adsets grandes)
print('=== Erro do read (conv observada) vs n por bootstrap ===')
# Pega um adset grande e reamostra sub-amostras de tamanho n, mede desvio da conv real vs conv do adset
big = df[df.utm_content.isin(gb[gb.n>=5000].index)]
base_cr = {}
for uc, g in big.groupby('utm_content'):
    base_cr[uc] = g['conv'].mean()
sizes = [100, 250, 500, 1000, 2000, 5000]
print('n_amostra | CV do read (std/mean da conv observada em subamostras)')
for n in sizes:
    cvs = []
    for uc, g in big.groupby('utm_content'):
        if len(g) >= n:
            samp_means = [g.sample(n, replace=False, random_state=s)['conv'].mean() for s in range(50)]
            m = np.mean(samp_means)
            if m > 0:
                cvs.append(np.std(samp_means)/m)
    if cvs:
        print(f'  {n:5d}   | {np.mean(cvs):.2f}')
print()

# =========================================================
# SCATTER
# =========================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# (a) EVG vs BP10
ax = axes[0]
ax.scatter(ga['score_prev'], ga['conv_real'], s=ga['n']/50, alpha=0.7, color='#c0392b')
for tag, row in ga.iterrows():
    ax.annotate(f'{tag} (n={int(row.n)})', (row.score_prev, row.conv_real),
                fontsize=9, ha='center', va='bottom')
ax.set_xlabel('Score médio previsto (OOF)')
ax.set_ylabel('Conversão real')
ax.set_title('(a) Campanha: EVG vs BP10')
ax.grid(alpha=0.3)

# (b) utm_content
ax = axes[1]
ax.scatter(gb['score_prev'], gb['conv_real'], s=np.sqrt(gb['n']), alpha=0.5, color='#2980b9')
# linha de tendência
z = np.polyfit(gb['score_prev'], gb['conv_real'], 1)
xs = np.linspace(gb['score_prev'].min(), gb['score_prev'].max(), 50)
ax.plot(xs, np.polyval(z, xs), '--', color='gray', lw=1)
ax.set_xlabel('Score médio previsto (OOF)')
ax.set_ylabel('Conversão real')
ax.set_title(f'(b) Adsets utm_content n>=500 (N={len(gb)})\nSpearman={rho_b:.2f}')
ax.grid(alpha=0.3)

# (c) semana
ax = axes[2]
gc_s = gc.reset_index()
ax.scatter(gc_s['score_prev'], gc_s['conv_real'], s=gc_s['n']/50, alpha=0.7, color='#27ae60')
for _, row in gc_s.iterrows():
    ax.annotate(row['week'][5:10], (row.score_prev, row.conv_real), fontsize=7, ha='left', va='bottom')
ax.set_xlabel('Score médio previsto (OOF)')
ax.set_ylabel('Conversão real')
ax.set_title(f'(c) Semana de cadastro (N={len(gc)})\nSpearman={rho_c:.2f}')
ax.grid(alpha=0.3)

plt.suptitle('Score intrínseco previsto vs conversão real — termômetro de qualidade', fontsize=13)
plt.tight_layout()
plt.savefig(f'{SC}/campanha_score_vs_real.png', dpi=110, bbox_inches='tight')
print('SCATTER salvo em campanha_score_vs_real.png')
