#!/usr/bin/env python3
"""Detecta dias de atenção anômala (candidatos a eventos de relevância pública).

Resíduo de log1p(série) contra DOW + mês + spend + fases; lista os maiores.
Serve para (a) validar as datas das sabatinas nos dados e (b) montar a régua
histórica de lift "normal vs excepcional".
"""
import numpy as np
import pandas as pd
from event_study import carregar_painel, residuos

df = carregar_painel()
mask = pd.Series(True, index=df.index)

series = {
    "ga4_direct": "Direct",
    "ga4_organic_search": "OrgSearch",
    "ga4_organic_video": "OrgVideo",
    "leads_organicos": "LeadsOrg",
    "receita_organico": "RecOrg",
}

res = pd.DataFrame({nome: residuos(df, col, mask) for col, nome in series.items()})
res["dia"] = df.dia
res["dow"] = df.dia.dt.day_name().str[:3]

# índice composto de atenção = média dos z-scores dos resíduos
z = res[list(series.values())].apply(lambda s: (s - s.mean()) / s.std())
res["IRO"] = z.mean(axis=1)
res["IRO_mm3"] = res["IRO"].rolling(3, center=True).mean()

res.to_csv(carregar_painel.__globals__["BASE"] / "iro_diario.csv", index=False)

print("=== Top 20 dias por IRO (índice de atenção orgânica) ===")
top = res.nlargest(20, "IRO")[["dia", "dow", "IRO", "Direct", "OrgSearch", "OrgVideo", "LeadsOrg", "RecOrg"]]
print(top.to_string(index=False, float_format=lambda x: f"{x:6.2f}"))

print("\n=== Top 12 janelas de 3 dias por IRO médio ===")
w = res.set_index("dia")["IRO"].rolling(3).mean().dropna()
print(w.nlargest(12).to_string(float_format=lambda x: f"{x:6.2f}"))

print("\n=== IRO nas janelas das sabatinas de agosto/2026 ===")
for d in pd.date_range("2026-08-10", "2026-08-20"):
    r = res[res.dia == d]
    if len(r):
        r = r.iloc[0]
        print(f"  {d.date()} ({r.dow}) IRO={r.IRO:6.2f}  Direct={r.Direct:6.2f} OrgVideo={r.OrgVideo:6.2f} LeadsOrg={r.LeadsOrg:6.2f}")
