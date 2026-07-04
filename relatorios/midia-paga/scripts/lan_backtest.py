"""
Backtest de 3 abordagens para sinalizar aumentar/manter/reduzir em campanhas LAN:

A) PPT-style: curva polinomial + G* (CPA marg = R$180)
B) Tendência local: slope do CPA marginal dos últimos 5 dias
C) CPA recente vs baseline: CPA_3d / CPA_acumulado

Simula em LAN completas (>=15 dias, terminadas). Para cada dia D:
  1. Aplica abordagem com dados até D-1
  2. Compara sinal com ROAS realizado nos próximos 3 dias (D+1 a D+3)
  3. Avalia se sinal discrimina

Resultado documentado (jun/2026): Aborda C é a única que funciona pra LAN.
- Ordem correta: aumentar (1.45) > manter (1.15) > reduzir (0.75)
- Discrimina bem no meio e fim do lançamento
- Não requer ajuste de curva (evita confundir trajetória com resposta)

Uso: python lan_backtest.py
"""
import csv, re, sys, os
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, median

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curve_fits import fit_poly, derivative, find_spend_for_cpa

ALL_CAMPS_PATH = '/tmp/all_camps.csv'  # gerar antes com queries/all_camps.sql
CPA_LIMITE = 180


def slope(vals):
    n = len(vals)
    if n < 2:
        return 0
    xs = list(range(n))
    mx, my = sum(xs) / n, sum(vals) / n
    num = sum((xs[i] - mx) * (vals[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    return num / den if den > 0 else 0


def signal_A(rows_until_d):
    """Polinomial + G*. Recomenda por ratio spend/G*."""
    if len(rows_until_d) < 6:
        return None
    sp = [r['spend'] for r in rows_until_d]
    sa = [r['sales'] for r in rows_until_d]
    fit = fit_poly(sp, sa, 3)
    if not fit or fit['r2'] < 0.3:
        return None
    smin = max(min(s for s in sp if s > 0), 100)
    smax = max(sp)
    g_star = find_spend_for_cpa(fit, CPA_LIMITE, smin, smax * 1.5)
    if g_star is None or g_star <= 0:
        return None
    ratio = rows_until_d[-1]['spend'] / g_star
    if ratio < 0.7:
        return 'aumentar'
    elif ratio < 1.15:
        return 'manter'
    return 'reduzir'


def signal_B(rows_until_d):
    """Slope local do CPA marginal últimos 5 dias."""
    if len(rows_until_d) < 5:
        return None
    last5 = rows_until_d[-5:]
    margs = []
    for i in range(1, len(last5)):
        ds = last5[i]['sales'] - last5[i - 1]['sales']
        dsp = last5[i]['spend'] - last5[i - 1]['spend']
        if dsp != 0 and ds > 0:
            margs.append(dsp / ds)
    if len(margs) < 3:
        return None
    sl = slope(margs)
    m = mean(margs)
    if m > 250 and sl > 30:
        return 'reduzir'
    elif m < 150 and sl < 0:
        return 'aumentar'
    elif sl > 50:
        return 'reduzir'
    return 'manter'


def signal_C(rows_until_d):
    """CPA últimos 3 dias vs CPA acumulado. Melhor abordagem para LAN."""
    if len(rows_until_d) < 5:
        return None
    last3 = rows_until_d[-3:]
    sp_recent = sum(r['spend'] for r in last3)
    sl_recent = sum(r['sales'] for r in last3)
    if sl_recent == 0:
        return None
    cpa_recent = sp_recent / sl_recent
    sp_base = sum(r['spend'] for r in rows_until_d[:-3])
    sl_base = sum(r['sales'] for r in rows_until_d[:-3])
    if sl_base == 0:
        return None
    ratio = cpa_recent / (sp_base / sl_base)
    if ratio > 1.30:
        return 'reduzir'
    elif ratio < 0.85:
        return 'aumentar'
    return 'manter'


def load_camps():
    camps = defaultdict(list)
    with open(ALL_CAMPS_PATH) as f:
        for r in csv.DictReader(f):
            try:
                d = datetime.strptime(r['reference_date'], '%Y-%m-%d').date()
                if 'VENDA' not in r['nm_campaign_name'].upper():
                    continue
                spend = float(r['daily_spend'])
                if spend <= 0:
                    continue
                camps[r['nm_campaign_name']].append({
                    'date': d, 'spend': spend,
                    'sales': float(r['daily_sales']),
                    'revenue': float(r['daily_revenue']),
                })
            except (ValueError, KeyError):
                pass
    for n in camps:
        camps[n].sort(key=lambda x: x['date'])
    return camps


def run_backtest():
    camps = load_camps()
    last_date = max(max(r['date'] for r in rows) for rows in camps.values())
    cutoff = last_date - timedelta(days=7)

    lan_completas = {
        name: rows for name, rows in camps.items()
        if name.startswith('[LAN]')
        and len([r for r in rows if r['spend'] > 0]) >= 15
        and max(r['date'] for r in rows if r['spend'] > 0) < cutoff
    }
    print(f'LAN completas: {len(lan_completas)}\n')

    results = defaultdict(list)
    for name, rows in lan_completas.items():
        if len(rows) < 10:
            continue
        for i in range(7, len(rows) - 1):
            rows_until = rows[:i + 1]
            future = rows[i + 1:i + 4]
            if not future:
                continue
            sp_f = sum(r['spend'] for r in future)
            rv_f = sum(r['revenue'] for r in future)
            sl_f = sum(r['sales'] for r in future)
            if sp_f == 0 or sl_f == 0:
                continue
            roas_f = rv_f / sp_f
            if roas_f > 10 or roas_f < 0.1:  # filtra outliers
                continue

            for label, fn in [('A', signal_A), ('B', signal_B), ('C', signal_C)]:
                sig = fn(rows_until)
                if sig:
                    results[label].append({'action': sig, 'roas_future': roas_f})

    print('Abordagem | Sinal    |   n | ROAS med')
    print('-' * 45)
    for label in ['A', 'B', 'C']:
        r = results[label]
        if not r:
            continue
        print()
        for action in ['aumentar', 'manter', 'reduzir']:
            f = [x['roas_future'] for x in r if x['action'] == action]
            if f:
                print(f'    {label}      | {action:>8} | {len(f):>3} | {median(f):>6.2f}')


if __name__ == '__main__':
    run_backtest()
