#!/usr/bin/env python3
"""
Mecenas — regressão logística multivariada com validação out-of-time.

Pergunta: quando todas as features competem juntas, quais sobrevivem?
Em especial: pc_similaridade>=0.95, vl_capital_social>=1e6 e qt_empresas sobrevivem
ao controle por cd_income_decile + nm_credit_card_level_max + vl_total_outras?

Fonte : bp-staging.dbt_abe.tb_mecenas_qualificacao_base (1 linha por e-mail)
Treino: label = virou mecenas até 2026-06-30
Teste : quem NÃO era mecenas em 2026-06-30; label = virou mecenas em jul-ago/2026
Amostra: todos os positivos + 200k negativos aleatórios (peso corrige o intercepto)

Uso: python3 logistica_multivariada.py
"""
import os, warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.preprocessing import StandardScaler
from google.cloud import bigquery

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200, "display.max_columns", 40, "display.max_rows", 300)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")
os.makedirs(OUT, exist_ok=True)

CUT = "2026-06-30 23:59:59"
NEG_SAMPLE = 200_000

SQL = f"""
WITH b AS (
  SELECT *,
    -- classe de painel
    CASE WHEN bl_is_mecenas AND dt_primeiro_mecenas <= DATETIME '{CUT}' THEN 'pos_ate_jun'
         WHEN bl_is_mecenas AND dt_primeiro_mecenas >  DATETIME '{CUT}' THEN 'pos_jul_ago'
         ELSE 'neg' END AS classe
  FROM `bp-staging.dbt_abe.tb_mecenas_qualificacao_base`
)
SELECT email, classe, bl_is_mecenas, dt_primeiro_mecenas,
       qt_tx_outras, vl_total_outras, vl_maior_tx_outras,
       bl_black, bl_vitalicio, bl_certificacao, bl_cdl, bl_teller, bl_ja_comprou_comercial,
       nm_gender_inferred, qt_idade, cd_income_decile, nm_credit_card_level_max,
       pc_similaridade, qt_empresas, vl_capital_social,
       arr_porte[SAFE_OFFSET(0)] AS nm_porte,
       arr_cnae_section[SAFE_OFFSET(0)] AS nm_cnae_section,
       bl_membro_ativo, qt_dias_casa
FROM b
WHERE classe <> 'neg'
   OR RAND() < {NEG_SAMPLE} / 1595520.0
"""

print("baixando…")
df = bigquery.Client(project="bp-datawarehouse").query(SQL).to_dataframe()
print(df.classe.value_counts().to_string())

# ---------------------------------------------------------------- features
CARD = {"0_debit": 0, "1_business": 1, "2_standard": 2, "3_gold": 3,
        "4_platinum": 4, "5_amex": 5, "6_black": 6}

d = df.copy()
d["card_ord"] = d.nm_credit_card_level_max.map(CARD)
d["renda_dec"] = pd.to_numeric(d.cd_income_decile, errors="coerce")
d.loc[d.renda_dec <= 0, "renda_dec"] = np.nan          # -1 / 0 = CEP não identificado
for c in ["vl_total_outras", "vl_maior_tx_outras", "qt_tx_outras", "qt_dias_casa",
          "vl_capital_social", "qt_empresas", "pc_similaridade", "qt_idade"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")

d["log_gasto"]   = np.log1p(d.vl_total_outras.fillna(0).clip(lower=0))
d["log_maior_tx"] = np.log1p(d.vl_maior_tx_outras.fillna(0).clip(lower=0))
d["qt_tx_outras"] = d.qt_tx_outras.fillna(0)
d["anos_casa"]   = d.qt_dias_casa.fillna(0) / 365.25
d["socio_95"]    = (d.pc_similaridade >= 0.95).astype(int)
d["socio_90"]    = (d.pc_similaridade >= 0.90).astype(int)
d["capital_1M"]  = (d.vl_capital_social >= 1e6).astype(int)
d["log_capital"] = np.log1p(d.vl_capital_social.fillna(0).clip(lower=0))
d["qt_empresas"] = d.qt_empresas.fillna(0)
d["fem"]         = (d.nm_gender_inferred == "Feminino").astype(int)
for c in ["bl_black", "bl_vitalicio", "bl_certificacao", "bl_cdl", "bl_teller",
          "bl_ja_comprou_comercial", "bl_membro_ativo"]:
    d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)

# imputação + flag de missing (renda e cartão têm cobertura parcial)
d["renda_na"] = d.renda_dec.isna().astype(int)
d["card_na"]  = d.card_ord.isna().astype(int)
d["renda_dec"] = d.renda_dec.fillna(d.renda_dec.median())
d["card_ord"]  = d.card_ord.fillna(d.card_ord.median())
d["idade_na"]  = d.qt_idade.isna().astype(int)
d["qt_idade"]  = d.qt_idade.fillna(d.qt_idade.median()).clip(15, 95)

FEATS = ["log_gasto", "log_maior_tx", "qt_tx_outras", "anos_casa",
         "bl_black", "bl_vitalicio", "bl_certificacao", "bl_cdl", "bl_teller",
         "bl_ja_comprou_comercial", "bl_membro_ativo",
         "renda_dec", "renda_na", "card_ord", "card_na",
         "socio_95", "capital_1M", "log_capital", "qt_empresas",
         "fem", "qt_idade", "idade_na"]

# ---------------------------------------------------------------- painéis
# TREINO: população inteira amostrada, label = converteu até 30/06/2026
tr = d.copy()
tr["y"] = (tr.classe == "pos_ate_jun").astype(int)
# peso amostral: negativos foram subamostrados
w_neg = 1595520.0 / (d.classe == "neg").sum()
tr["w"] = np.where(tr.classe == "neg", w_neg, 1.0)

# TESTE: quem NÃO era mecenas em 30/06 → label = converteu em jul-ago/2026
te = d[d.classe != "pos_ate_jun"].copy()
te["y"] = (te.classe == "pos_jul_ago").astype(int)

print(f"\nTREINO N={len(tr)} pos={tr.y.sum()}   TESTE N={len(te)} pos={te.y.sum()} "
      f"(base amostrada={te.y.mean():.4%}; base real≈{248/1595520:.5%})")

# ---------------------------------------------------------------- modelo
Xtr = tr[FEATS].astype(float).values
Xte = te[FEATS].astype(float).values
sc = StandardScaler().fit(Xtr)

lr = LogisticRegression(max_iter=5000, C=1.0, class_weight="balanced")
lr.fit(sc.transform(Xtr), tr.y, sample_weight=tr.w)
p_te = lr.predict_proba(sc.transform(Xte))[:, 1]
p_tr = lr.predict_proba(sc.transform(Xtr))[:, 1]

auc_te = roc_auc_score(te.y, p_te)
n1, n0 = te.y.sum(), (1 - te.y).sum()
se = np.sqrt(auc_te * (1 - auc_te) / min(n1, n0))     # aprox. conservadora
print(f"\n>>> AUC treino (in-sample) = {roc_auc_score(tr.y, p_tr):.4f}")
print(f">>> AUC OUT-OF-TIME (teste jul-ago/26) = {auc_te:.4f}  (±{1.96*se:.3f} IC95 aprox.)")
print(f">>> PR-AUC teste = {average_precision_score(te.y, p_te):.5f} vs base {te.y.mean():.5f}")

# ---------------------------------------------------------------- coeficientes + p-valores
Xsm = sm.add_constant(pd.DataFrame(sc.transform(Xtr), columns=FEATS))
res = sm.GLM(tr.y.values, Xsm, family=sm.families.Binomial(),
             freq_weights=tr.w.values).fit()
co = pd.DataFrame({"var": Xsm.columns, "coef_padr": res.params.values,
                   "p_valor": res.pvalues.values,
                   "OR_por_1sd": np.exp(res.params.values)})
co["signif"] = np.where(co.p_valor < 0.001, "***",
                np.where(co.p_valor < 0.01, "**",
                np.where(co.p_valor < 0.05, "*", "n.s.")))
co = co[co["var"] != "const"].sort_values("coef_padr", ascending=False)
print("\n=== COEFICIENTES MULTIVARIADOS (padronizados, ordenados) ===")
print(co.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
co.to_csv(f"{OUT}/coeficientes_multivariado.csv", index=False)

# ---------------------------------------------------------------- univariado vs multivariado
print("\n=== UNIVARIADO -> MULTIVARIADO (o que sobra quando tudo compete) ===")
rows = []
for f in FEATS:
    Xu = sm.add_constant(pd.DataFrame(sc.transform(Xtr), columns=FEATS)[[f]])
    r = sm.GLM(tr.y.values, Xu, family=sm.families.Binomial(),
               freq_weights=tr.w.values).fit()
    rows.append({"var": f, "coef_uni": r.params[f], "p_uni": r.pvalues[f],
                 "coef_multi": float(co.loc[co["var"] == f, "coef_padr"].iloc[0]),
                 "p_multi": float(co.loc[co["var"] == f, "p_valor"].iloc[0])})
cmp = pd.DataFrame(rows)
cmp["retencao_%"] = 100 * cmp.coef_multi / cmp.coef_uni.replace(0, np.nan)
cmp["veredito"] = np.where(cmp.p_multi >= 0.05, "PERDE significância",
                   np.where(np.sign(cmp.coef_multi) != np.sign(cmp.coef_uni), "INVERTE sinal",
                   np.where(cmp["retencao_%"] < 40, "sobrevive fraco (<40%)", "sobrevive")))
cmp = cmp.sort_values("coef_multi", ascending=False)
print(cmp.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
cmp.to_csv(f"{OUT}/uni_vs_multi.csv", index=False)

# ---------------------------------------------------------------- teste focal CNPJ
print("\n=== TESTE FOCAL: CNPJ sobrevive a renda + cartão + gasto? ===")
BLOCOS = {
  "M0 só CNPJ                     ": ["socio_95", "capital_1M", "qt_empresas", "log_capital"],
  "M1 + renda + cartão            ": ["socio_95", "capital_1M", "qt_empresas", "log_capital",
                                      "renda_dec", "renda_na", "card_ord", "card_na"],
  "M2 + gasto prévio (vl_tot_outr)": ["socio_95", "capital_1M", "qt_empresas", "log_capital",
                                      "renda_dec", "renda_na", "card_ord", "card_na", "log_gasto"],
  "M3 modelo completo             ": FEATS,
}
foco = []
for nome, cols in BLOCOS.items():
    Xb = sm.add_constant(pd.DataFrame(sc.transform(Xtr), columns=FEATS)[cols])
    r = sm.GLM(tr.y.values, Xb, family=sm.families.Binomial(),
               freq_weights=tr.w.values).fit()
    for v in ["socio_95", "capital_1M", "qt_empresas", "log_capital"]:
        foco.append({"modelo": nome.strip(), "var": v, "coef": r.params[v],
                     "OR_1sd": np.exp(r.params[v]), "p": r.pvalues[v]})
foco = pd.DataFrame(foco).pivot(index="var", columns="modelo", values=["coef", "p"])
print(foco.to_string(float_format=lambda x: f"{x:,.4f}"))
foco.to_csv(f"{OUT}/cnpj_controle_multivariado.csv")

# ---------------------------------------------------------------- decis out-of-time
dd = pd.DataFrame({"y": te.y.values, "p": p_te})
dd["dec"] = pd.qcut(dd.p.rank(method="first"), 10, labels=[f"D{i}" for i in range(1, 11)])
t = dd.groupby("dec")["y"].agg(n="size", conv="sum")
t["taxa"] = t.conv / t.n
t["lift"] = t.taxa / dd.y.mean()
t["captura_%"] = 100 * t.conv / dd.y.sum()
print("\n=== DECIS DO SCORE — OUT-OF-TIME (jul-ago/26) ===")
print(t.to_string(float_format=lambda x: f"{x:,.4f}"))
t.to_csv(f"{OUT}/decis_out_of_time.csv")
print("\nsaída em", OUT)

# ---------------------------------------------------------------- topo do score (comparável a regras)
print("\n=== TOPO DO SCORE — bolsões comparáveis a regras de segmento ===")
rows = []
for pct in [0.1, 0.25, 0.5, 1, 2, 5, 10, 20]:
    k = max(1, int(len(dd) * pct / 100))
    s = dd.nlargest(k, "p")
    rows.append({"topo_%": pct, "N_amostra": k,
                 "N_real_estimado": int(k * 1595520 / len(dd)),
                 "conv": int(s.y.sum()), "taxa": s.y.mean(),
                 "lift": s.y.mean() / dd.y.mean(), "captura_%": 100 * s.y.sum() / dd.y.sum()})
topo = pd.DataFrame(rows)
print(topo.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
topo.to_csv(f"{OUT}/topo_score_out_of_time.csv", index=False)

# ---------------------------------------------------------------- robustez a vazamento
# vl_total_outras / qt_tx_outras / bl_* são snapshot all-time: para os positivos de jul-ago
# incluem compras POSTERIORES à conversão. Modelo só com features estruturais/estáticas:
EST = ["renda_dec", "renda_na", "card_ord", "card_na", "socio_95", "capital_1M",
       "log_capital", "qt_empresas", "fem", "qt_idade", "idade_na", "anos_casa",
       "bl_membro_ativo"]
i = [FEATS.index(f) for f in EST]
sc2 = StandardScaler().fit(Xtr[:, i])
lr2 = LogisticRegression(max_iter=5000, class_weight="balanced")
lr2.fit(sc2.transform(Xtr[:, i]), tr.y, sample_weight=tr.w)
p2 = lr2.predict_proba(sc2.transform(Xte[:, i]))[:, 1]
print(f"\nAUC out-of-time SÓ com features estruturais (sem histórico de gasto) = "
      f"{roc_auc_score(te.y, p2):.4f}")
c2 = pd.DataFrame({"var": EST, "coef": lr2.coef_[0]}).sort_values("coef", ascending=False)
print(c2.to_string(index=False, float_format=lambda x: f"{x:,.4f}"))
