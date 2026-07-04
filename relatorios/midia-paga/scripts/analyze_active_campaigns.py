"""
Analisa campanhas ativas (gasto nos últimos 7 dias) e produz status:
- aumentar / manter / no_alvo / reduzir / sem_curva

Duas abordagens:
- PPT (perpétuas): polinomial + G* (CPA marg = CPA_LIMITE)
- LAN (lançamentos): CPA_recente(3d) vs CPA_acumulado — mais robusto

Uso:
  python analyze_active_campaigns.py

Requer:
  ../../../BigQuery/dados/midia_paga/scatter_campaign_daily.csv (dados)
  curve_fits.py (biblioteca)

Output: /tmp/active_camps.json
"""
import csv, re, json, sys, os
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from curve_fits import (fit_poly, fit_logistic, fit_power, derivative,
                        find_spend_for_cpa, choose_fit)

DATA_PATH = os.path.expanduser(
    '~/meu_projeto/BigQuery/dados/midia_paga/scatter_campaign_daily.csv'
)
CPA_LIMITE = 180
ACTIVE_WINDOW_DAYS = 7


def load_campaigns(path=DATA_PATH):
    camps = defaultdict(list)
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                d = datetime.strptime(r['reference_date'], '%Y-%m-%d').date()
                camps[r['nm_campaign_name']].append({
                    'date': d,
                    'spend': float(r['daily_spend']),
                    'sales': float(r['daily_sales']),
                    'revenue': float(r['daily_revenue']),
                })
            except (ValueError, KeyError):
                pass
    for n in camps:
        camps[n].sort(key=lambda x: x['date'])
    return camps


def is_lan(name):
    return name.startswith('[LAN]')


def analyze_ppt(rows):
    """PPT: usa curva polinomial. G* = gasto onde CPA marg = R$180."""
    spends = [r['spend'] for r in rows]
    sales = [r['sales'] for r in rows]
    n_pts = sum(1 for s in spends if s > 0)

    fit = choose_fit(spends, sales, n_pts)
    if not fit or fit.get('r2', 0) < 0.3:
        return {'status': 'sem_curva', 'fit_kind': fit['kind'] if fit else None,
                'fit_r2': fit['r2'] if fit else None}

    smin = max(min(s for s in spends if s > 0), 100)
    smax_obs = max(spends)
    smax_extrap = smax_obs * 1.5
    g_star = find_spend_for_cpa(fit, CPA_LIMITE, smin, smax_extrap)

    if g_star is None:
        return {'status': 'sem_curva', 'fit_kind': fit['kind'], 'fit_r2': fit['r2']}

    last_date = rows[-1]['date']
    cutoff = last_date - timedelta(days=ACTIVE_WINDOW_DAYS)
    recent = [r for r in rows if r['date'] >= cutoff and r['spend'] > 0]
    spend_per_day = mean(r['spend'] for r in recent) if recent else 0

    cpa_marg = None
    if spend_per_day > 0:
        d = derivative(fit, spend_per_day)
        if d and d > 0:
            cpa_marg = 1 / d

    ratio = spend_per_day / g_star if g_star > 0 else None
    if ratio is None:
        status = 'sem_curva'
    elif ratio < 0.7:
        status = 'aumentar'
    elif ratio < 0.95:
        status = 'manter'
    elif ratio < 1.15:
        status = 'no_alvo'
    else:
        status = 'reduzir'

    return {'status': status, 'fit_kind': fit['kind'], 'fit_r2': fit['r2'],
            'g_star': g_star, 'spend_per_day_recent': spend_per_day,
            'ratio': ratio, 'cpa_marg_recent': cpa_marg}


def analyze_lan(rows):
    """LAN: CPA_recente(3d) vs CPA_acumulado. Independe de ajuste de curva."""
    if len(rows) < 5:
        return {'status': 'sem_curva'}

    last3 = rows[-3:]
    sp_recent = sum(r['spend'] for r in last3)
    sl_recent = sum(r['sales'] for r in last3)
    if sl_recent == 0:
        return {'status': 'sem_curva'}

    cpa_recent = sp_recent / sl_recent
    sp_base = sum(r['spend'] for r in rows[:-3])
    sl_base = sum(r['sales'] for r in rows[:-3])
    if sl_base == 0:
        return {'status': 'sem_curva'}

    cpa_baseline = sp_base / sl_base
    ratio = cpa_recent / cpa_baseline

    if ratio > 1.30:
        status = 'reduzir'
    elif ratio > 1.15:
        status = 'cautela'
    elif ratio < 0.85:
        status = 'aumentar'
    else:
        status = 'manter'

    return {'status': status, 'method': 'lan_ratio',
            'cpa_recent': cpa_recent, 'cpa_baseline': cpa_baseline,
            'ratio': ratio, 'spend_per_day_recent': sp_recent / 3}


def analyze_all():
    camps = load_campaigns()
    last_date = max(max(r['date'] for r in rows) for rows in camps.values())
    cutoff = last_date - timedelta(days=ACTIVE_WINDOW_DAYS)

    results = []
    for name, rows in camps.items():
        recent = [r for r in rows if r['date'] >= cutoff and r['spend'] > 0]
        if not recent:
            continue

        total_spend = sum(r['spend'] for r in rows)
        total_sales = sum(r['sales'] for r in rows)
        total_rev = sum(r['revenue'] for r in rows)
        spend_recent_7d = sum(r['spend'] for r in recent)

        base = {
            'name': name, 'is_lan': is_lan(name),
            'n_pts': sum(1 for r in rows if r['spend'] > 0),
            'first_date': str(rows[0]['date']), 'last_date': str(rows[-1]['date']),
            'total_spend': total_spend, 'total_sales': total_sales, 'total_revenue': total_rev,
            'roas_total': total_rev / total_spend if total_spend > 0 else 0,
            'cpa_total': total_spend / total_sales if total_sales > 0 else None,
            'spend_recent_7d': spend_recent_7d,
        }

        if is_lan(name):
            analysis = analyze_lan(rows)
        else:
            analysis = analyze_ppt(rows)

        results.append({**base, **analysis})

    results.sort(key=lambda r: -r['spend_recent_7d'])
    return results, last_date


if __name__ == '__main__':
    results, last_date = analyze_all()
    print(f'\nÚltima data: {last_date}')
    print(f'Campanhas ativas (últimos {ACTIVE_WINDOW_DAYS}d): {len(results)}\n')

    from collections import Counter
    status_count = Counter(r['status'] for r in results)
    print(f'Distribuição de status: {dict(status_count)}\n')

    print(f'{"Tipo":>4} {"Status":>10} {"Spend 7d":>10} {"Ratio":>7}  Campanha')
    print('-' * 80)
    for r in results[:30]:
        tipo = 'LAN' if r['is_lan'] else 'PPT'
        ratio = f"{r.get('ratio', 0):.2f}" if r.get('ratio') else '-'
        print(f'{tipo:>4} {r["status"]:>10}  R${r["spend_recent_7d"]/1000:>7.0f}k  {ratio:>6}  {r["name"][:60]}')

    out_path = '/tmp/active_camps.json'
    with open(out_path, 'w') as f:
        json.dump({'analysis': results, 'last_date': str(last_date),
                   'cpa_limite': CPA_LIMITE}, f, default=str)
    print(f'\nSalvo em {out_path}')
