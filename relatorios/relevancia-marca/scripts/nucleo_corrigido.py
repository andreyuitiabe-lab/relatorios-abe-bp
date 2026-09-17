#!/usr/bin/env python3
"""NÚCLEO CORRIGIDO (17/09/2026) — o único resultado que sobreviveu à revisão independente.

Correções aplicadas vs rodadas 9b–9e:
  (1) série de origem COMPLETA (410 dias; antes 313 — os 95 faltantes tinham MAIS audiência);
  (2) moving-block bootstrap (blocos de dias consecutivos) — o iid subestimava o IC em 1,6–1,9×;
  (3) controle negativo de renovações (cobrança automática, não pode ser causada pelo vídeo);
  (4) CAC e transações reportados como UM fato (identidade verificada), não dois.
Substitui os números de ANALISE.md §9b–§9e para o efeito principal.
"""
import sys, numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from event_study import carregar_painel, BASE
from teste_pareado_sem_lancamento import janelas
PD = BASE.parent.parent/"performance-diaria"/"data"; rng = np.random.default_rng(2609); OUT=[]
def say(s=""): print(s); OUT.append(s)

p = carregar_painel()[["dia","tx_total","receita_total","tx_ads","spend_total"]]
v = pd.read_csv(PD/"vendas_diarias_canal_campanha.csv", parse_dates=["dia"])
g = v.groupby(["dia","canal"]).tx.sum().unstack(fill_value=0)
tv = v.groupby("dia").agg(tx_total=("tx","sum"), receita_total=("receita","sum")).reset_index()
tv["tx_ads"] = g.get("Ads Meta",0)+g.get("Ads Google",0)
sp = pd.read_csv(PD/"spend_vendas_campanha_fonte.csv", parse_dates=["dia"]).fillna(0).groupby("dia").spend.sum().rename("spend_total").reset_index()
ext = tv.merge(sp,on="dia",how="left"); ext = ext[ext.dia>p.dia.max()]
df = pd.concat([p,ext]).sort_values("dia")
o = pd.read_csv(BASE/"yt_diario_origem.csv", parse_dates=["dia"])
w = o.pivot_table(index="dia", columns="origem", values="views", aggfunc="sum").fillna(0)
w["yt"] = w.sum(axis=1) - w.get("ADVERTISING",0) - w.get("SHORTS",0)
rn = pd.read_csv(BASE/"renovacoes_diarias.csv", parse_dates=["dia"])
df = df.merge(w[["yt"]].reset_index(), on="dia", how="left").merge(rn, on="dia", how="left")
df = df[(df.dia>="2025-08-01")&(df.dia<="2026-09-12")].dropna(subset=["yt"]).sort_values("dia").reset_index(drop=True)
em, lanc, fech, _, _ = janelas(df); df["em_venda"]=em; df["lanc"]=lanc; df["fech"]=fech
df["cac_ads"] = df.spend_total/df.tx_ads.replace(0,np.nan)
say(f"série: {len(df)} dias ({df.dia.min():%d/%m/%y}→{df.dia.max():%d/%m/%y}) — COMPLETA (antes 313)")

def estratos(d):
    d = d.copy()
    d["bs"] = pd.qcut(d.spend_total, 5, labels=False, duplicates="drop")
    d["bd"] = d.dia.dt.dayofweek.isin([5,6]).astype(int).astype(str)+"_"+d.em_venda.astype(int).astype(str)
    return d

def efeito(d, x, y):
    difs, pes = [], []
    for _, gq in d.groupby(["bs","bd"]):
        gq = gq.dropna(subset=[x,y])
        if len(gq) < 10: continue
        m = gq[x].median(); a, b = gq[gq[x]>m][y], gq[gq[x]<=m][y]
        if len(a)<4 or len(b)<4 or b.mean()==0: continue
        difs.append(a.mean()/b.mean()); pes.append(len(gq))
    if not difs: return np.nan
    return np.average(difs, weights=np.array(pes, float))

def block_boot(d, x, y, L=14, nb=2000):
    """Moving-block bootstrap: reamostra blocos de L dias consecutivos, reconstrói estratos."""
    obs = efeito(estratos(d), x, y); n = len(d); nblocos = int(np.ceil(n/L)); reps = []
    arr = d.reset_index(drop=True)
    for _ in range(nb):
        ini = rng.integers(0, max(n-L,1), nblocos)
        idx = np.concatenate([np.arange(i, min(i+L, n)) for i in ini])[:n]
        rep = arr.iloc[idx].copy(); rep["dia"] = arr.dia.values[:len(rep)]
        e = efeito(estratos(rep), x, y)
        if np.isfinite(e): reps.append(e)
    reps = np.array(reps); lo, hi = np.percentile(reps, [2.5, 97.5])
    pv = 2*min((reps<=1).mean(), (reps>=1).mean())
    return obs, lo, hi, pv

d = df[~df.lanc & ~df.fech]
say(f"recorte principal (sem abertura ±3d nem fechamento −2..0): {len(d)} dias\n")
say("EFEITO DE DIAS DE AUDIÊNCIA ORGÂNICA ALTA (pareado por quintil de spend × fds × fase)")
say(f"{'desfecho':<36}{'efeito':>9}{'IC95 (bloco L=14)':>24}{'p':>8}")
res = {}
for nome, col in [("Transações não-renovação","tx_total"), ("Receita","receita_total"),
                  ("CAC de ads (= o mesmo fato)","cac_ads"), ("Spend [checagem do pareamento]","spend_total"),
                  ("⊗ Renovações (controle negativo)","tx_renov"), ("⊗ Receita de renovação","rec_renov")]:
    obs, lo, hi, pv = block_boot(d, "yt", col)
    res[col] = (obs, lo, hi, pv)
    say(f"{nome:<36}{100*(obs-1):>+8.1f}%  [{100*(lo-1):>+6.1f}, {100*(hi-1):>+6.1f}]{pv:>8.3f}")
say("\nRobustez do bootstrap ao tamanho do bloco (transações):")
for L in (7, 14, 21, 28):
    obs, lo, hi, pv = block_boot(d, "yt", "tx_total", L=L, nb=1200)
    say(f"   L={L:>2} dias:  {100*(obs-1):+.1f}%  IC [{100*(lo-1):+.1f}, {100*(hi-1):+.1f}]  p={pv:.3f}")
say("\nComparação com a série incompleta (313 dias) que gerou os números publicados:")
ant = df[df.dia.isin(pd.read_csv(BASE/"yt_diario_origem.csv", parse_dates=["dia"]).dia.unique()[:313])]
obs_c, _, _, _ = block_boot(d, "yt", "tx_total", nb=800)
say(f"   série completa (410 dias): {100*(obs_c-1):+.1f}% · publicado com 313 dias: +15,8%")
(BASE/"nucleo_corrigido.txt").write_text("\n".join(OUT)); print("\nsalvo em", BASE/"nucleo_corrigido.txt")
