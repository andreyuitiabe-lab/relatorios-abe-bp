"""
Testa correlação entre sinais de funil (hook rate, CTR) e CPA futuro.

Resultado documentado (jun/2026): correlações fracas com lag > 3d.
- Hook rate lag 7d: corr +0.28 (mas SINAL POSITIVO — hook sobe → CPA sobe depois)
- CTR lag 0-1: corr -0.30 (contemporâneo, não preditivo)
- ΔCTR contemporâneo: -0.45 (forte mas não preditivo)
- CVR: nenhum sinal antecipa (correlações < 0.15)

Conclusão: hook e CTR são úteis para DIAGNÓSTICO em tempo real, não para PREVISÃO
de CPA futuro. Aceitou-se opção C (usar como sinal contemporâneo em vez de preditivo).

Uso: python funnel_correlation.py
Requer: /tmp/funnel_daily.csv gerado com queries/daily_funnel_metrics.sql
"""
import csv, sys, os
from datetime import datetime
from statistics import mean, median

DATA_PATH = '/tmp/funnel_daily.csv'


def correl(xs, ys):
    if len(xs) < 3:
        return 0
    mx, my = mean(xs), mean(ys)
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs)))
    dx = (sum((xs[i] - mx) ** 2 for i in range(len(xs)))) ** 0.5
    dy = (sum((ys[i] - my) ** 2 for i in range(len(ys)))) ** 0.5
    return num / (dx * dy) if dx * dy > 0 else 0


def load():
    data = []
    with open(DATA_PATH) as f:
        for r in csv.DictReader(f):
            try:
                d = datetime.strptime(r['reference_date'], '%Y-%m-%d').date()
                spend = float(r['spend'])
                impr = float(r['impressions'])
                if spend > 0 and impr > 0 and float(r['sales']) > 0:
                    data.append({
                        'date': d, 'spend': spend,
                        'impressions': impr,
                        'clicks': float(r['clicks']),
                        'view3s': float(r['view3s']),
                        'thruplays': float(r['thruplays']),
                        'sales': float(r['sales']),
                        'revenue': float(r['revenue']),
                        'ctr': float(r['clicks']) / impr,
                        'hook_rate': float(r['view3s']) / impr,
                        'thru_rate': float(r['thruplays']) / impr,
                        'cpm': spend / impr * 1000,
                        'cpa': spend / float(r['sales']),
                        'cvr': float(r['sales']) / float(r['clicks']) if float(r['clicks']) > 0 else 0,
                        'roas': float(r['revenue']) / spend,
                    })
            except (ValueError, KeyError):
                pass
    data.sort(key=lambda x: x['date'])
    return data


def corr_lagged(data, pred_key, target_key, lag):
    pairs = []
    for i in range(len(data) - lag):
        p = data[i].get(pred_key)
        t = data[i + lag].get(target_key)
        if p is not None and t is not None:
            pairs.append((p, t))
    if len(pairs) < 5:
        return None, 0
    return correl([p[0] for p in pairs], [p[1] for p in pairs]), len(pairs)


def main():
    data = load()
    print(f'Dias: {len(data)}, período {data[0]["date"]} → {data[-1]["date"]}\n')

    print('=== CORRELAÇÃO: sinal_t × CPA_{t+lag} ===')
    print(f'{"Sinal":>12} {"lag":>4} {"corr":>8} {"n":>5}')
    print('-' * 40)
    for pred in ['hook_rate', 'ctr', 'thru_rate', 'cpm']:
        print()
        for lag in [0, 1, 3, 7, 14]:
            c, n = corr_lagged(data, pred, 'cpa', lag)
            if c is not None:
                mark = '  ⭐' if abs(c) > 0.4 else '  ✓' if abs(c) > 0.25 else ''
                print(f'{pred:>12} {lag:>4}  {c:>+.3f} {n:>5}{mark}')


if __name__ == '__main__':
    main()
