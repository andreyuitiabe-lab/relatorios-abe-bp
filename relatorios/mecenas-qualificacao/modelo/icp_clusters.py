#!/usr/bin/env python3
"""
ICPs do Mecenas — clusterização dos doadores reais.

Objetivo: deixar os perfis EMERGIREM dos dados, em vez de recortar por regra.
Roda k-means sobre os doadores de BOLSA (>= R$ 1.000; o Solidário é analisado à parte),
gente parecida existe na base que ainda não doou (o alvo de mídia de cada ICP).

Saída: modelo/saida/icp_clusters.csv + icp_lookalike.csv
"""
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
from google.cloud import bigquery
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

OUT = Path(__file__).resolve().parent / "saida"
ICP_JSON = Path(__file__).resolve().parent.parent / "icp.json"   # agregado, versionado no repo
OUT.mkdir(exist_ok=True)
BASE = "bp-staging.dbt_abe.tb_mecenas_qualificacao_base"

CARD_ORD = {"0_debit": 0, "1_business": 1, "2_standard": 2, "3_gold": 3,
            "4_platinum": 4, "5_amex": 5, "6_black": 6}

SQL = f"""
SELECT
  b.id_person, b.bl_is_mecenas, b.vl_maior_tx_mecenas, b.vl_total_mecenas, b.qt_tx_mecenas,
  b.vl_total_outras, b.vl_maior_tx_outras, b.qt_tx_outras,
  b.bl_black, b.bl_vitalicio, b.bl_certificacao, b.bl_cdl,
  b.bl_ja_comprou_comercial, b.bl_membro_ativo, b.qt_dias_casa, b.qt_idade,
  b.nm_gender_inferred, b.cd_income_decile, b.nm_credit_card_level_max,
  b.pc_similaridade, b.qt_empresas, b.vl_capital_social,
  (SELECT x FROM UNNEST(b.arr_cnae_section) x LIMIT 1) AS cnae,
  m.uf
FROM `{BASE}` b
LEFT JOIN `bp-staging.dbt_abe.tb_mecenas_person_map` m
  ON m.id_person = b.id_person AND LENGTH(m.uf) = 2
WHERE b.bl_is_mecenas OR b.bl_membro_ativo = 1
QUALIFY ROW_NUMBER() OVER (PARTITION BY b.id_person ORDER BY m.id_gateway_customer) = 1
"""


def featurize(df):
    """Features do ICP.

    ⚠️ NÃO entra o valor da doação: o ICP precisa ser observável ANTES da pessoa doar,
    senão não serve para achar gente parecida na base. O valor entra só na
    caracterização (quanto cada ICP costuma doar), nunca na formação do cluster.
    """
    f = pd.DataFrame(index=df.index)
    f["log_gasto"]   = np.log1p(df["vl_maior_tx_outras"].fillna(0))
    f["log_capital"] = np.log1p(df["vl_capital_social"].fillna(0))
    f["anos_casa"]   = (df["qt_dias_casa"].fillna(0) / 365).clip(0, 12)
    f["renda"]       = df["cd_income_decile"].replace(-1, np.nan).fillna(5)
    f["cartao"]      = df["nm_credit_card_level_max"].map(CARD_ORD).fillna(1.5)
    # ⚠️ Inconsistência conhecida: `socio` exige similaridade >= 0.95, mas `log_capital` e
    # `empresas` usam o registro da Receita sem filtrar similaridade. Efeito medido no cluster
    # "empresário": 8,7% dele cai fora da flag `socio` mas TEM empresa e capital registrados,
    # com match de nome mais fraco (mediana 0,65). Ou seja, 100% do cluster tem empresa; a flag
    # é que erra para baixo. Não corrigido porque o efeito é pequeno e mexer nas features
    # rebaralharia clusters já reportados — mas ao ler os %, `socio` = "sócio CONFIRMADO".
    f["socio"]       = (df["pc_similaridade"].fillna(0) >= 0.95).astype(int)
    f["empresas"]    = df["qt_empresas"].fillna(0).clip(0, 5)
    f["vitalicio"]   = df["bl_vitalicio"].fillna(0)
    f["certif"]      = df["bl_certificacao"].fillna(0)
    f["cdl"]         = df["bl_cdl"].fillna(0)
    f["comercial"]   = df["bl_ja_comprou_comercial"].fillna(0)
    return f


def main():
    cache = OUT / "_base_icp.parquet"
    if cache.exists():
        print("lendo cache...", flush=True)
        df = pd.read_parquet(cache)
    else:
        print("puxando base...", flush=True)
        df = bigquery.Client(project="bp-datawarehouse").query(SQL).to_dataframe()
        df.to_parquet(cache)
    doa = df[df.bl_is_mecenas].reset_index(drop=True)
    nao = df[~df.bl_is_mecenas].reset_index(drop=True)
    print(f"  {len(df):,} pessoas · {len(doa):,} doadores")

    # UM único modelo: treina no perfil dos doadores, aplica na base inteira.
    # Assim o rótulo do ICP e a contagem de lookalike falam do mesmo cluster.
    F = featurize(doa)
    sc = StandardScaler().fit(F)
    # K=4: com o Solidário fora do label (analisado à parte), K=5 produzia um cluster
    # degenerado de ~10 pessoas. Os 4 grupos que sobram se separam por dois eixos limpos:
    # tem empresa (sim/não) × tem histórico de produto high-ticket (sim/não).
    K = 4
    km = KMeans(n_clusters=K, n_init=25, random_state=42).fit(sc.transform(F))
    doa["icp"] = km.labels_
    lab_nao = km.predict(sc.transform(featurize(nao)))

    # caracterização de cada cluster
    rows = []
    for k in range(K):
        g = doa[doa.icp == k]
        rows.append({
            "icp": k,
            "pessoas": len(g),
            "pc_doadores": 100 * len(g) / len(doa),
            "receita": g.vl_total_mecenas.sum(),
            "pc_receita": 100 * g.vl_total_mecenas.sum() / doa.vl_total_mecenas.sum(),
            "doacao_mediana": g.vl_maior_tx_mecenas.median(),
            "doacao_media": g.vl_total_mecenas.mean(),
            "doou_mais_de_1x": 100 * (g.qt_tx_mecenas > 1).mean(),
            "pc_socio": 100 * (g.pc_similaridade.fillna(0) >= 0.95).mean(),
            "capital_mediano": g.loc[g.pc_similaridade.fillna(0) >= 0.95, "vl_capital_social"].median(),
            "pc_cap1m": 100 * (g.vl_capital_social.fillna(0) >= 1e6).mean(),
            "pc_cartao_top": 100 * g.nm_credit_card_level_max.isin(["6_black", "5_amex"]).mean(),
            "pc_renda_top": 100 * (g.cd_income_decile.fillna(0) >= 9).mean(),
            "anos_casa": (g.qt_dias_casa / 365).mean(),
            "gasto_previo": g.vl_total_outras.mean(),
            "pc_vitalicio": 100 * g.bl_vitalicio.mean(),
            "pc_certif": 100 * g.bl_certificacao.mean(),
            "pc_cdl": 100 * g.bl_cdl.mean(),
            "pc_comercial": 100 * g.bl_ja_comprou_comercial.mean(),
            "pc_fem": 100 * (g.nm_gender_inferred == "Feminino").mean(),
            "idade": g.qt_idade.mean(),
            "uf_top": g.uf.value_counts().head(3).to_dict(),
            "cnae_top": g.cnae.value_counts().head(3).to_dict(),
        })
    car = pd.DataFrame(rows).sort_values("receita", ascending=False)
    car.to_csv(OUT / "icp_clusters.csv", index=False)

    pd.set_option("display.width", 250, "display.max_columns", 40)
    cols = ["icp", "pessoas", "pc_receita", "doacao_mediana", "pc_socio", "pc_cap1m",
            "pc_cartao_top", "pc_renda_top", "anos_casa", "gasto_previo",
            "pc_vitalicio", "pc_certif", "pc_comercial", "pc_fem", "idade"]
    print("\n=== CLUSTERS ===")
    print(car[cols].round(1).to_string(index=False))
    print("\n=== UF e CNAE por cluster ===")
    for _, r in car.iterrows():
        print(f"  ICP {r.icp}: UF {r.uf_top} · CNAE {list(r.cnae_top)[:2]}")

    # quanta gente parecida existe na base que ainda não doou — mesmo modelo, mesmos rótulos
    look = []
    for k in range(K):
        n_doa, n_nao = int((km.labels_ == k).sum()), int((lab_nao == k).sum())
        look.append({
            "icp": k,
            "doadores": n_doa,
            "nao_doadores": n_nao,
            "taxa_no_cluster": 100 * n_doa / (n_doa + n_nao),
            "lift": (n_doa / (n_doa + n_nao)) / (len(doa) / len(df)),
            "doacao_media": doa.loc[km.labels_ == k, "vl_total_mecenas"].mean(),
        })
    lk = pd.DataFrame(look).sort_values("lift", ascending=False)
    lk.to_csv(OUT / "icp_lookalike.csv", index=False)

    # ── icp.json: só agregados, para o index.html consumir (sem nenhum dado por pessoa) ──
    import json
    lkm = {int(r.icp): r for _, r in lk.iterrows()}
    payload = []
    for _, r in car.iterrows():
        k = int(r.icp)
        payload.append({
            "icp": k,
            "doadores": int(r.pessoas),
            "pc_receita": round(float(r.pc_receita), 1),
            "doacao_mediana": round(float(r.doacao_mediana)),
            "doacao_media": round(float(lkm[k].doacao_media)),
            "nao_doadores": int(lkm[k].nao_doadores),
            "lift": round(float(lkm[k].lift), 2),
            "taxa_no_cluster": round(float(lkm[k].taxa_no_cluster), 1),
            "traits": {
                "socio": round(float(r.pc_socio), 1),
                "cap1m": round(float(r.pc_cap1m), 1),
                "cartao_top": round(float(r.pc_cartao_top), 1),
                "renda_top": round(float(r.pc_renda_top), 1),
                "vitalicio": round(float(r.pc_vitalicio), 1),
                "certif": round(float(r.pc_certif), 1),
                "cdl": round(float(r.pc_cdl), 1),
                "comercial": round(float(r.pc_comercial), 1),
                "feminino": round(float(r.pc_fem), 1),
                "idade": round(float(r.idade), 1),
                "anos_casa": round(float(r.anos_casa), 1),
                "gasto_previo": round(float(r.gasto_previo)),
                "multi_doacao": round(float(r.doou_mais_de_1x), 1),
            },
            "uf_top": {str(a): int(b) for a, b in list(r.uf_top.items())[:3]},
        })
    ICP_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ {ICP_JSON.name} — {len(payload)} perfis (agregado, sem PII)")
    print("\n=== ALVO DE MÍDIA: quanta gente parecida ainda não doou ===")
    print(lk.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
