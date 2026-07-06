#!/usr/bin/env python3
"""
Random Forest — feature importance da qualificação de leads (Não Membros).
Objetivo: ranquear quais campos (pesquisa + enriquecimento) mais predizem conversão.
Método: permutation importance (não a impurity-based, que infla features de alta cardinalidade).
"""
import sys
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score, average_precision_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = sys.argv[1] if len(sys.argv) > 1 else "rf_data.csv"
OUTDIR = sys.argv[2] if len(sys.argv) > 2 else "."

df = pd.read_csv(CSV)
print(f"linhas={len(df)}  conv={df['conv'].sum()} ({100*df['conv'].mean():.2f}%)")

TARGET = "conv"
# ATENÇÃO: features de dim_user (cd_uf, nm_region, nm_city_size, cd_income_decile,
# nm_credit_card_level, vl_idade_interno) VAZAM O ALVO — só são preenchidas após a
# conversão (quem compra vira usuário e ganha geo/cartão/id). Confirmado: UF preenchida
# → 91% conv; UF nula → 0,07%. Removidas. Usamos apenas o que se conhece no registro.
# features numéricas e categóricas
NUM = ["vl_relevancia"]
CAT = ["nm_tag", "nm_lead_channel", "survey_tag", "nm_idade", "nm_genero",
       "nm_estado_civil", "nm_filhos", "nm_ocupacao", "nm_renda",
       "nm_escolaridade", "nm_conhece_bp"]
NUM = [c for c in NUM if c in df.columns]
CAT = [c for c in CAT if c in df.columns]

X = df[NUM + CAT].copy()
y = df[TARGET].astype(int)
# decile -1 = CEP não identificado → tratar como missing
if "cd_income_decile" in X:
    X["cd_income_decile"] = X["cd_income_decile"].replace(-1, np.nan)
for c in CAT:
    X[c] = X[c].fillna("__NA__").astype(str)

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42)

pre = ColumnTransformer([
    ("num", SimpleImputer(strategy="median"), NUM),
    ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), CAT),
])
rf = RandomForestClassifier(
    n_estimators=300, max_depth=None, min_samples_leaf=50,
    class_weight="balanced", n_jobs=-1, random_state=42)
pipe = Pipeline([("pre", pre), ("rf", rf)])
pipe.fit(X_tr, y_tr)

proba = pipe.predict_proba(X_te)[:, 1]
auc = roc_auc_score(y_te, proba)
ap = average_precision_score(y_te, proba)
base_rate = y_te.mean()
print(f"AUC={auc:.4f}  PR-AUC={ap:.4f}  (base rate={base_rate:.4f})")

# Permutation importance no conjunto de teste, AGRUPADA por feature original
# (uma feature categórica vira N colunas one-hot; queremos a importância da feature toda)
print("Calculando permutation importance (por feature original)...")
r = permutation_importance(
    pipe, X_te, y_te, scoring="roc_auc",
    n_repeats=5, random_state=42, n_jobs=-1)

imp = pd.DataFrame({
    "feature": X_te.columns,
    "importance": r.importances_mean,
    "std": r.importances_std,
}).sort_values("importance", ascending=False)

# rótulos legíveis
LABELS = {
    "nm_renda": "Renda declarada (pesquisa)",
    "nm_ocupacao": "Ocupação (pesquisa)",
    "nm_conhece_bp": "Conhece a BP (pesquisa)",
    "vl_relevancia": "Relevância 1-5 (pesquisa)",
    "nm_escolaridade": "Escolaridade (pesquisa)",
    "nm_idade": "Idade faixa (pesquisa)",
    "nm_genero": "Gênero (pesquisa)",
    "nm_estado_civil": "Estado civil (pesquisa)",
    "nm_filhos": "Filhos (pesquisa)",
    "survey_tag": "Campanha da pesquisa",
    "nm_tag": "Campanha do lead",
    "nm_lead_channel": "Canal de captação",
    "cd_uf": "UF (interno/geo)",
    "nm_region": "Região (interno/geo)",
    "nm_city_size": "Tamanho da cidade (interno)",
    "cd_income_decile": "Decil de renda (interno/IBGE)",
    "nm_credit_card_level": "Nível do cartão (interno)",
    "vl_idade_interno": "Idade (interno/dim_user)",
}
imp["label"] = imp["feature"].map(lambda f: LABELS.get(f, f))
imp["origem"] = imp["feature"].map(
    lambda f: "pesquisa" if "(pesquisa)" in LABELS.get(f, "") or f in
    ("nm_renda","nm_ocupacao","nm_conhece_bp","vl_relevancia","nm_escolaridade",
     "nm_idade","nm_genero","nm_estado_civil","nm_filhos") else "interno/campanha")

imp.to_csv(f"{OUTDIR}/rf_importances.csv", index=False)
print(imp[["label", "importance", "std", "origem"]].to_string(index=False))

# ---- gráfico ----
d = imp.sort_values("importance")
colors = ["#2563eb" if o == "pesquisa" else "#94a3b8" for o in d["origem"]]
fig, ax = plt.subplots(figsize=(9, 7))
ax.barh(d["label"], d["importance"], xerr=d["std"],
        color=colors, edgecolor="white", capsize=2)
ax.set_xlabel("Queda no AUC ao embaralhar a variável (permutation importance)")
ax.set_title("O que prediz conversão de Não Membros\nRandom Forest · permutation importance · "
             f"AUC={auc:.3f} · n={len(df):,}".replace(",", "."))
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#2563eb", label="Campo da pesquisa"),
                   Patch(color="#94a3b8", label="Dado interno / campanha")],
          loc="lower right", frameon=False)
ax.axvline(0, color="#333", lw=0.6)
plt.tight_layout()
plt.savefig(f"{OUTDIR}/rf_feature_importance.png", dpi=150, bbox_inches="tight")
print(f"\nSalvo: {OUTDIR}/rf_feature_importance.png")
