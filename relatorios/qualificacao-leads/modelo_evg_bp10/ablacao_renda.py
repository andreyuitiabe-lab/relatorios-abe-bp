"""Ablação: quanto o modelo perde sem a pergunta de renda (removida jul/2026)."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RNG = 42
DATA = "/Users/andre.abe/meu_projeto/relatorios-abe-bp/relatorios/qualificacao-leads/modelo_evg_bp10/dataset_evg_bp10.csv"
df = pd.read_csv(DATA)
y = df["conv"].astype(int).values

STATUS = ["st_member_status_at_registration", "bl_is_new_registration"]
SURVEY_FULL = ["renda", "relacao_bp", "tempo_conhece_bp", "fonte_confianca",
               "qtd_streaming", "streaming", "midia_tradicional", "religiao"]
SURVEY_SEM_RENDA = [c for c in SURVEY_FULL if c != "renda"]

def prep(cols, frame):
    X = frame[cols].copy()
    for c in X.columns:
        X[c] = X[c].astype("object").where(X[c].notna(), "__NA__").astype(str)
    return X.values

def pipe(n_cols):
    ohe = OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=True)
    ct = ColumnTransformer([("cat", ohe, list(range(n_cols)))])
    # LogReg sem class_weight (decisão da revisão adversarial jul/2026)
    return Pipeline([("ohe", ct), ("sc", StandardScaler(with_mean=False)),
                     ("clf", LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs"))])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RNG)

def avalia(nome, cols, frame, target):
    X = prep(cols, frame)
    res = cross_validate(pipe(len(cols)), X, target, cv=cv,
                         scoring={"auc": "roc_auc", "prauc": "average_precision"}, n_jobs=-1)
    scores = cross_val_predict(pipe(len(cols)), X, target, cv=cv,
                               method="predict_proba", n_jobs=-1)[:, 1]
    lt = pd.DataFrame({"score": scores, "conv": target})
    lt["decil"] = pd.qcut(lt["score"].rank(method="first"), 10, labels=False)  # 9 = topo
    top = lt[lt["decil"] == 9]
    pct_vendas_top = top["conv"].sum() / lt["conv"].sum()
    lift_top = top["conv"].mean() / lt["conv"].mean()
    print(f"{nome:42s} AUC={res['test_auc'].mean():.4f}±{res['test_auc'].std():.4f}  "
          f"PR-AUC={res['test_prauc'].mean():.4f}  top decil: {pct_vendas_top:.1%} das vendas, lift {lift_top:.2f}x")

# cobertura da renda
nm = df["st_member_status_at_registration"].eq("Não Membro")
resp_any = df[SURVEY_FULL].notna().any(axis=1)
print(f"Leads: {len(df):,} | NM: {nm.sum():,} ({nm.mean():.0%})")
print(f"Respondeu algo da pesquisa (NM): {resp_any[nm].mean():.1%} | respondeu renda (NM): {df.loc[nm,'renda'].notna().mean():.1%}")
print(f"Distribuição renda (NM respondentes):")
print(df.loc[nm, "renda"].value_counts(normalize=True).round(3).to_string())
print()

print("=== GERAL (todos os status) ===")
avalia("status+survey COM renda", STATUS + SURVEY_FULL, df, y)
avalia("status+survey SEM renda", STATUS + SURVEY_SEM_RENDA, df, y)
print()
print("=== SÓ NÃO MEMBROS (survey only) ===")
df_nm, y_nm = df[nm].reset_index(drop=True), y[nm.values]
print(f"base conv NM = {y_nm.mean():.4%} (n={len(y_nm):,}, positivos={y_nm.sum()})")
avalia("survey COM renda (NM)", SURVEY_FULL, df_nm, y_nm)
avalia("survey SEM renda (NM)", SURVEY_SEM_RENDA, df_nm, y_nm)
