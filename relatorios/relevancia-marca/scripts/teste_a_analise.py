#!/usr/bin/env python3
"""Teste A — Formato vs pauta. Lift por sabatina/episódio com controle pareado por calendário.

Para cada conteúdo tratado: controle = CONTROLE_top8 restrito aos MESMOS dias em que o
conteúdo teve pessoa-dias (pareamento por calendário). Lift = taxa tratada ÷ taxa controle.
IC95 e p: Fisher exato (pooled) + bootstrap por dia (2000 reps) para o lift e diferenças.
"""
import numpy as np
import pandas as pd
from scipy import stats

rng = np.random.default_rng(42)
BASE = "/Users/andre.abe/meu_projeto/relatorios-abe-bp/relatorios/relevancia-marca/data"
D14_CUTOFF = "2026-08-18"  # último dia com janela D+14 completa (compras até 01/09)
NBOOT = 2000

def load(path):
    df = pd.read_csv(path)
    df["dia"] = pd.to_datetime(df["dia"]).dt.strftime("%Y-%m-%d")
    return df

def analisa(df, grupo, outcome):  # outcome: 'd7' ou 'd14'
    xcol, rcol = f"com_compra_{outcome}", f"receita_{outcome}"
    t = df[df.grupo == grupo].copy()
    if outcome == "d14":
        t = t[t.dia <= D14_CUTOFF]
    if len(t) == 0 or t.pessoa_dias.sum() == 0:
        return None
    dias = set(t.dia)
    c = df[(df.grupo == "CONTROLE_top8") & (df.dia.isin(dias))].copy()
    # merge por dia para o bootstrap
    m = t[["dia", "pessoa_dias", xcol, rcol]].merge(
        c[["dia", "pessoa_dias", xcol, rcol]], on="dia", how="left", suffixes=("_t", "_c")).fillna(0)
    nt, xt, rt = m.pessoa_dias_t.sum(), m[xcol + "_t"].sum(), m[rcol + "_t"].sum()
    nc, xc, rc = m.pessoa_dias_c.sum(), m[xcol + "_c"].sum(), m[rcol + "_c"].sum()
    taxa_t, taxa_c = xt / nt, xc / nc if nc else np.nan
    lift = taxa_t / taxa_c if taxa_c else np.nan
    # taxa de controle padronizada pelo mix de dias do tratado (checagem)
    w = m.pessoa_dias_t / nt
    taxa_c_std = float((w * (m[xcol + "_c"] / m.pessoa_dias_c.replace(0, np.nan))).sum())
    _, p = stats.fisher_exact([[xt, nt - xt], [xc, nc - xc]])
    # bootstrap por dia
    lifts, rpp_ratios = [], []
    idx = np.arange(len(m))
    for _ in range(NBOOT):
        s = m.iloc[rng.choice(idx, size=len(m), replace=True)]
        bnt, bxt = s.pessoa_dias_t.sum(), s[xcol + "_t"].sum()
        bnc, bxc = s.pessoa_dias_c.sum(), s[xcol + "_c"].sum()
        if bnt and bnc and bxc:
            lifts.append((bxt / bnt) / (bxc / bnc))
        if bnt and bnc and s[rcol + "_c"].sum():
            rpp_ratios.append((s[rcol + "_t"].sum() / bnt) / (s[rcol + "_c"].sum() / bnc))
    lo, hi = (np.percentile(lifts, [2.5, 97.5]) if lifts else (np.nan, np.nan))
    rpp_t = rt / nt
    rpp_c = rc / nc if nc else np.nan
    return dict(grupo=grupo, outcome=outcome, n_dias=len(m), n_t=int(nt), x_t=int(xt),
                taxa_t=100 * taxa_t, n_c=int(nc), x_c=int(xc), taxa_c=100 * taxa_c,
                taxa_c_std=100 * taxa_c_std, lift=lift, lift_lo=lo, lift_hi=hi, p_fisher=p,
                rpp_t=rpp_t, rpp_c=rpp_c, rpp_ratio=rpp_t / rpp_c if rpp_c else np.nan,
                m=m, xcol=xcol)

def pool_grupo(resultados):
    """SMR pooled: observados ÷ esperados (esperado = n_t × taxa controle pareada de cada sabatina)."""
    obs = sum(r["x_t"] for r in resultados)
    n = sum(r["n_t"] for r in resultados)
    exp = sum(r["n_t"] * r["taxa_c"] / 100 for r in resultados)
    return obs, n, exp, obs / exp if exp else np.nan

def boot_pool_diff(res_alta, res_baixa, nboot=NBOOT):
    """Bootstrap por dia da diferença de lift pooled ALTA − BAIXA."""
    def one_pool(rs):
        obs = exp = 0.0
        for r in rs:
            m = r["m"]; xcol = r["xcol"]
            s = m.iloc[rng.choice(len(m), size=len(m), replace=True)]
            bnt, bxt = s.pessoa_dias_t.sum(), s[xcol + "_t"].sum()
            bnc, bxc = s.pessoa_dias_c.sum(), s[xcol + "_c"].sum()
            if bnt and bnc:
                obs += bxt
                exp += bnt * (bxc / bnc)
        return obs / exp if exp else np.nan
    diffs, la, lb = [], [], []
    for _ in range(nboot):
        a, b = one_pool(res_alta), one_pool(res_baixa)
        if np.isfinite(a) and np.isfinite(b):
            diffs.append(a - b); la.append(a); lb.append(b)
    diffs = np.array(diffs)
    pval = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
    return (np.percentile(la, [2.5, 97.5]), np.percentile(lb, [2.5, 97.5]),
            np.percentile(diffs, [2.5, 97.5]), pval)

sab = load(f"{BASE}/teste_a_lift_por_sabatina.csv")
ent = load(f"{BASE}/teste_a_lift_bp_entrevista.csv")
inv = pd.read_csv(f"{BASE}/teste_a_inventario_sabatinas.csv")

sabatinas = [g for g in sab.grupo.unique() if g != "CONTROLE_top8"]
episodios = [g for g in ent.grupo.unique() if g != "CONTROLE_top8"]

print("=" * 100)
print("POR SABATINA — D+14 (janela completa, dias <= 18/08) e D+7 (dias <= 25/08)")
print("=" * 100)
rows, res_by = [], {}
for g in sorted(sabatinas):
    for oc in ["d14", "d7"]:
        r = analisa(sab, g, oc)
        if r:
            res_by[(g, oc)] = r
            rows.append({k: v for k, v in r.items() if k not in ("m", "xcol")})
tab = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(tab.round(3).to_string(index=False))

print()
print("=" * 100)
print("BP ENTREVISTA — top-5 episódios, D+14 (01/03–18/08)")
print("=" * 100)
rows_e, res_e = [], {}
for g in sorted(episodios):
    r = analisa(ent, g, "d14")
    if r:
        res_e[g] = r
        rows_e.append({k: v for k, v in r.items() if k not in ("m", "xcol")})
print(pd.DataFrame(rows_e).round(3).to_string(index=False))

# ---- grupos de notoriedade ----
ALTA_BASE = ["Pablo Marçal", "Renan Santos"]
BAIXA_BASE = ["Guilherme Derrite", "Caroline de Toni", "Aldo Rebelo", "Augusto Cury", "Ronaldo Caiado"]
FRONTEIRA = ["Romeu Zema", "Ricardo Salles"]

def grupo_report(nome, membros, oc):
    rs = [res_by[(g, oc)] for g in membros if (g, oc) in res_by and res_by[(g, oc)]["n_t"] > 0]
    if not rs:
        print(f"{nome} ({oc}): sem dados"); return None
    obs, n, exp, smr = pool_grupo(rs)
    print(f"{nome} ({oc}): n={n:,} pessoa-dias, obs={obs}, esperado={exp:.1f}, lift pooled={smr:.3f} | membros: {membros}")
    return rs

print()
print("=" * 100)
print("GRUPOS ALTA vs BAIXA — lift pooled (obs/esperado, controle pareado por dia), D+7 (inclui Renan/Marçal)")
print("=" * 100)
cenarios = {
    "principal (fronteira na BAIXA)": (ALTA_BASE, BAIXA_BASE + FRONTEIRA),
    "sens.: Zema+Salles na ALTA": (ALTA_BASE + FRONTEIRA, BAIXA_BASE),
    "sens.: só nacionais puros vs locais puros": (ALTA_BASE, ["Guilherme Derrite", "Caroline de Toni", "Aldo Rebelo"]),
}
for oc in ["d7", "d14"]:
    print(f"\n--- Outcome {oc} ---")
    for nome, (alta, baixa) in cenarios.items():
        ra = grupo_report(f"  ALTA [{nome}]", alta, oc)
        rb = grupo_report(f"  BAIXA [{nome}]", baixa, oc)
        if ra and rb:
            ci_a, ci_b, ci_d, p = boot_pool_diff(ra, rb)
            print(f"  -> IC95 lift ALTA [{ci_a[0]:.2f},{ci_a[1]:.2f}] | BAIXA [{ci_b[0]:.2f},{ci_b[1]:.2f}] | diff [{ci_d[0]:.2f},{ci_d[1]:.2f}] p_boot={p:.3f}")

# ---- proxy contínua: lift × audiência ----
print()
print("=" * 100)
print("PROXY CONTÍNUA — lift D+7 × pessoa-dias de audiência da sabatina (Spearman, n=9)")
print("=" * 100)
aud = inv.set_index("nm_media")["pessoa_dias"].to_dict()
pts = [(g, aud.get(g, np.nan), res_by[(g, "d7")]["lift"]) for g in sabatinas if (g, "d7") in res_by]
dfp = pd.DataFrame(pts, columns=["sabatina", "audiencia_pd", "lift_d7"]).dropna()
print(dfp.round(3).to_string(index=False))
rho, prho = stats.spearmanr(dfp.audiencia_pd, dfp.lift_d7)
print(f"Spearman rho={rho:.3f}, p={prho:.3f} (n={len(dfp)})")
if all((g, "d14") in res_by for g in dfp.sabatina if g not in ("Pablo Marçal", "Renan Santos")):
    d14pts = dfp[~dfp.sabatina.isin(["Pablo Marçal", "Renan Santos"])].copy()
    d14pts["lift_d14"] = [res_by[(g, "d14")]["lift"] for g in d14pts.sabatina]
    rho2, p2 = stats.spearmanr(d14pts.audiencia_pd, d14pts.lift_d14)
    print(f"D+14 (7 sabatinas): rho={rho2:.3f}, p={p2:.3f}")

# ---- régua de formato: pooled sabatinas vs pooled entrevistas (d14) ----
print()
print("=" * 100)
print("RÉGUA DE FORMATO — pooled (D+14): sabatinas jun-jul vs top-5 BP Entrevista")
print("=" * 100)
rs_sab = [res_by[(g, "d14")] for g in sabatinas if (g, "d14") in res_by and res_by[(g, "d14")]["n_t"] > 0]
rs_ent = list(res_e.values())
for nome, rs in [("Sabatinas (7, jun-jul)", rs_sab), ("BP Entrevista (top-5)", rs_ent)]:
    obs, n, exp, smr = pool_grupo(rs)
    print(f"{nome}: n={n:,}, obs={obs}, esp={exp:.1f}, lift pooled={smr:.3f}")
ci_a, ci_b, ci_d, p = boot_pool_diff(rs_sab, rs_ent)
print(f"IC95 sabatinas [{ci_a[0]:.2f},{ci_a[1]:.2f}] | entrevistas [{ci_b[0]:.2f},{ci_b[1]:.2f}] | diff [{ci_d[0]:.2f},{ci_d[1]:.2f}] p_boot={p:.3f}")

# salvar tabelas
tab.to_csv(f"{BASE}/teste_a_resultado_por_sabatina.csv", index=False)
pd.DataFrame(rows_e).to_csv(f"{BASE}/teste_a_resultado_bp_entrevista.csv", index=False)
print("\nCSVs salvos: teste_a_resultado_por_sabatina.csv, teste_a_resultado_bp_entrevista.csv")
