"""
H1 — Validação do pooling de saltos naturais com controles do mesmo dia.

Estimador por evento (campanha c, dia t com salto de spend >=|25%| e base 3d estável):
  controles = campanhas do MESMO TIPO (PPT/LAN), ativas em t, spend estável (<10% de var)
  ratio_controle = mediana( vendas_pos / vendas_pre ) dos controles  [demanda comum do dia]
  Δvendas_adj = vendas_pos(c) − vendas_pre(c) × ratio_controle
  mCAC_evento = Δspend / Δvendas_adj          [janela pré = 3d, pós = 2d, médias diárias]

Pooling: mediana + IC bootstrap 90% por segmento (PPT/LAN × direção do salto).

Placebo: pseudo-eventos (dias com |Δspend|<10% e base estável) passam pelo MESMO
estimador. Critério: Δvendas_adj do placebo centrado em ~0 (~50% positivo).
"""
import csv, math, os, random
from collections import defaultdict
from statistics import mean, median, stdev

random.seed(42)
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'camp_daily_cpm.csv')
TETO = 180

camps = defaultdict(list)
with open(PATH) as f:
    for r in csv.DictReader(f):
        try:
            sp = float(r['daily_spend']); sa = float(r['daily_sales'])
        except (ValueError, TypeError):
            continue
        if sp <= 0:
            continue
        camps[r['nm_campaign_name']].append(
            {'date': r['reference_date'], 'spend': sp, 'sales': sa})
for c in camps:
    camps[c].sort(key=lambda x: x['date'])

def ctype(name):
    return 'LAN' if name.startswith('[LAN]') else ('PPT' if name.startswith('[PPT]') else 'OUT')

# índice por (campanha) -> {date: (spend, sales)} e lista de datas
by_date = defaultdict(dict)
for c, rows in camps.items():
    for i, r in enumerate(rows):
        by_date[c][r['date']] = i  # índice na lista

all_dates = sorted({r['date'] for rows in camps.values() for r in rows})
date_idx = {d: i for i, d in enumerate(all_dates)}

def window(c, t_i, lo, hi):
    """Média diária de spend e sales da campanha c nos offsets [lo,hi] a partir do índice t_i (na lista da campanha), exigindo datas de calendário consecutivas presentes."""
    rows = camps[c]
    seg = rows[t_i + lo: t_i + hi + 1]
    if len(seg) != hi - lo + 1:
        return None
    # exige datas contíguas no calendário (sem gaps)
    d0, d1 = date_idx[seg[0]['date']], date_idx[seg[-1]['date']]
    if d1 - d0 != hi - lo:
        return None
    return mean(r['spend'] for r in seg), mean(r['sales'] for r in seg)

def find_events(jump_min, jump_max):
    """Eventos com |Δ| entre jump_min e jump_max (usar (0.0,0.10) p/ placebo)."""
    evs = []
    for c, rows in camps.items():
        if len(rows) < 12 or ctype(c) == 'OUT':
            continue
        for t in range(6, len(rows) - 2):
            pre = window(c, t, -3, -1)
            post = window(c, t, 0, 1)
            if not pre or not post:
                continue
            sp_pre, sa_pre = pre
            sp_post, sa_post = post
            if sp_pre <= 0:
                continue
            seg = rows[t-3:t]
            if stdev(r['spend'] for r in seg) / sp_pre > 0.25:
                continue
            jump = sp_post / sp_pre - 1
            if not (jump_min <= abs(jump) < jump_max):
                continue
            evs.append({'camp': c, 'type': ctype(c), 't': t, 'date': rows[t]['date'],
                        'jump': jump, 'sp_pre': sp_pre, 'sa_pre': sa_pre,
                        'sp_post': sp_post, 'sa_post': sa_post})
    return evs

def add_control_adjustment(evs):
    out = []
    for e in evs:
        ratios = []
        for c2, rows2 in camps.items():
            if c2 == e['camp'] or ctype(c2) != e['type']:
                continue
            if e['date'] not in by_date[c2]:
                continue
            t2 = by_date[c2][e['date']]
            pre2 = window(c2, t2, -3, -1)
            post2 = window(c2, t2, 0, 1)
            if not pre2 or not post2:
                continue
            sp_pre2, sa_pre2 = pre2
            sp_post2, sa_post2 = post2
            if sp_pre2 <= 0 or sa_pre2 <= 0:
                continue
            if abs(sp_post2 / sp_pre2 - 1) > 0.10:   # controle deve estar estável
                continue
            ratios.append(sa_post2 / sa_pre2)
        if len(ratios) < 3:
            continue
        ctrl = median(ratios)
        d_sales_adj = e['sa_post'] - e['sa_pre'] * ctrl
        d_spend = e['sp_post'] - e['sp_pre']
        e2 = dict(e)
        e2['n_ctrl'] = len(ratios)
        e2['ctrl_ratio'] = ctrl
        e2['d_sales_adj'] = d_sales_adj
        e2['d_spend'] = d_spend
        e2['mcac'] = d_spend / d_sales_adj if d_sales_adj != 0 else None
        out.append(e2)
    return out

def boot_ci(vals, stat=median, B=2000, alpha=0.10):
    if len(vals) < 5:
        return None
    ss = []
    for _ in range(B):
        s = [random.choice(vals) for _ in vals]
        ss.append(stat(s))
    ss.sort()
    return ss[int(B * alpha / 2)], ss[int(B * (1 - alpha / 2))]

# ---------- eventos reais ----------
real = add_control_adjustment(find_events(0.25, 10.0))
plac = add_control_adjustment(find_events(0.0, 0.08))

print(f'Eventos reais com >=3 controles: {len(real)} | placebo: {len(plac)}')
print(f'Nº mediano de controles por evento: {median(e["n_ctrl"] for e in real)}')

# ---------- placebo ----------
print('\n== PLACEBO (pseudo-eventos, |Δspend|<8%) ==')
dsp = [e['d_sales_adj'] for e in plac]
pos = sum(1 for v in dsp if v > 0) / len(dsp)
# normalizar por vendas pré pra comparar escalas
rel = [e['d_sales_adj'] / e['sa_pre'] for e in plac if e['sa_pre'] > 0]
ci = boot_ci(rel)
print(f'Δvendas_adj relativo: mediana {median(rel):+.3f} (IC90 {ci[0]:+.3f}..{ci[1]:+.3f}) | % positivo {pos:.0%}')

# ---------- eventos reais por segmento ----------
print('\n== EVENTOS REAIS ==')
segs = defaultdict(list)
for e in real:
    d = 'up' if e['jump'] > 0 else 'down'
    segs[(e['type'], d)].append(e)

print(f'{"segmento":<10} {"n":>4} {"%Δv_adj>0":>10} {"Δv rel med":>11} {"mCAC med":>9} {"IC90 mCAC":>18}')
for k in sorted(segs):
    es = segs[k]
    rel_s = [e['d_sales_adj'] / e['sa_pre'] for e in es if e['sa_pre'] > 0]
    pos_s = sum(1 for e in es if (e['d_sales_adj'] > 0) == (e['jump'] > 0)) / len(es)
    # mCAC só faz sentido com sinal consistente; filtra extremos
    mc = [e['mcac'] for e in es if e['mcac'] is not None and 0 < e['mcac'] < 3000]
    ci_m = boot_ci(mc) if len(mc) >= 5 else None
    ci_s = f'{ci_m[0]:.0f}..{ci_m[1]:.0f}' if ci_m else '—'
    print(f'{k[0]+"-"+k[1]:<10} {len(es):>4} {pos_s:>9.0%} {median(rel_s):>+11.3f} '
          f'{median(mc) if mc else float("nan"):>9.0f} {ci_s:>18}')

# separação vs placebo (para saltos up: % com Δv_adj>0 deve superar % do placebo)
up = [e for e in real if e['jump'] > 0]
up_pos = sum(1 for e in up if e['d_sales_adj'] > 0) / len(up)
print(f'\nSeparação: saltos UP com Δvendas_adj>0: {up_pos:.0%} vs placebo positivo {pos:.0%}')

# eficiência marginal declinante? comparar mCAC em saltos pequenos vs grandes (up)
small = [e['mcac'] for e in up if 0.25 <= e['jump'] < 0.5 and e['mcac'] and 0 < e['mcac'] < 3000]
big = [e['mcac'] for e in up if e['jump'] >= 0.5 and e['mcac'] and 0 < e['mcac'] < 3000]
if len(small) >= 5 and len(big) >= 5:
    print(f'mCAC saltos up moderados (25-50%): mediana R${median(small):.0f} (n={len(small)}) | '
          f'grandes (>=50%): R${median(big):.0f} (n={len(big)})')
