#!/usr/bin/env python3
"""Share of Search da BP com denominador de categoria (Fase 1 do PLANO.md).

Três denominadores (decisão do André, 25/08): MÍDIAS, STREAMINGS e TODOS.

Gotcha do Trends: normaliza 0–100 pelo máximo do grupo e aceita 5 termos/payload.
Contra a Netflix a BP arredondaria para 0 → coleta em payloads encadeados por âncora
(BP↔Globoplay↔Netflix) e re-escala multiplicativa para uma escala comum.
"""
import time, sys
import pandas as pd
from pathlib import Path
from pytrends.request import TrendReq

BASE = Path(__file__).resolve().parent.parent / "data"
TIMEFRAME = "2021-09-01 2026-08-20"   # 5 anos → granularidade semanal
GEO = "BR"

MIDIAS = ["jovem pan", "revista oeste", "gazeta do povo", "o antagonista"]
STREAMINGS = ["netflix", "prime video", "globoplay", "disney plus"]
BP = "brasil paralelo"

def payload(pt, kws, tentativas=4):
    for i in range(tentativas):
        try:
            pt.build_payload(kws, timeframe=TIMEFRAME, geo=GEO)
            df = pt.interest_over_time()
            if df.empty:
                raise RuntimeError("retorno vazio")
            return df.drop(columns=["isPartial"], errors="ignore")
        except Exception as e:
            espera = 15 * (i + 1)
            print(f"  retry {i+1} ({type(e).__name__}: {str(e)[:80]}) — aguardando {espera}s", file=sys.stderr)
            time.sleep(espera)
    raise RuntimeError(f"payload falhou: {kws}")

def main():
    pt = TrendReq(hl="pt-BR", tz=180)

    # payload 1: BP + mídias (mesma ordem de grandeza — payload único)
    print("coletando mídias…", file=sys.stderr)
    p_mid = payload(pt, [BP] + MIDIAS); time.sleep(10)

    # payload 2: BP + globoplay (âncora pequena→média)
    print("coletando âncora BP↔globoplay…", file=sys.stderr)
    p_anc = payload(pt, [BP, "globoplay"]); time.sleep(10)

    # payload 3: os 4 streamings grandes (max = netflix)
    print("coletando streamings…", file=sys.stderr)
    p_str = payload(pt, STREAMINGS)

    # re-escala: leva tudo à escala do payload de streamings via globoplay
    fator = p_str["globoplay"].mean() / max(p_anc["globoplay"].mean(), 1e-9)
    bp_escala_str = p_anc[BP] * fator                      # BP na escala dos streamings
    fator_mid = bp_escala_str.mean() / max(p_mid[BP].mean(), 1e-9)
    midias_escala = p_mid[MIDIAS] * fator_mid              # mídias na mesma escala

    out = pd.DataFrame(index=p_str.index)
    out["bp"] = bp_escala_str
    for c in MIDIAS: out[c] = midias_escala[c]
    for c in STREAMINGS: out[c] = p_str[c]
    out = out.reset_index().rename(columns={"date": "semana"})

    out["sos_midias"]     = 100 * out.bp / (out.bp + out[MIDIAS].sum(axis=1))
    out["sos_streamings"] = 100 * out.bp / (out.bp + out[STREAMINGS].sum(axis=1))
    out["sos_todos"]      = 100 * out.bp / (out.bp + out[MIDIAS + STREAMINGS].sum(axis=1))

    out.to_csv(BASE / "share_of_search.csv", index=False)
    print(f"\nOK — {len(out)} semanas → data/share_of_search.csv")
    for c in ["sos_midias", "sos_streamings", "sos_todos"]:
        s = out[c]
        print(f"  {c:16s} média {s.mean():6.2f}%  min {s.min():5.2f}%  max {s.max():5.2f}%  último(4sem) {s.tail(4).mean():5.2f}%")

if __name__ == "__main__":
    main()
