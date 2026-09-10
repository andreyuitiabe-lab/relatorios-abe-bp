"""
Teste da implicação de Dew et al. 2024: as curvas observacionais estão identificadas?

1. Autocorrelação lag-1 do log(spend) within-campanha (spend autocorrelacionado
   = variação insuficiente pra separar saturação de efeito temporal)
2. Densidade de saltos de budget (|Δ| >= 25% vs média dos 3 dias anteriores,
   com 3 dias estáveis antes) — quasi-experimentos naturais disponíveis
3. Teste-chave: mCAC local medido no salto (Δvendas/Δspend, 2 dias) vs mCAC
   previsto pela curva de potência ajustada com dados ATÉ a véspera.
   Concordância de direção (acima/abaixo do teto R$180) e correlação de ranks.

Resultado (23/jul/2026): autocorr baixa (0,36) e 316 saltos naturais — variação existe;
mas curva falha evento a evento (58% vs 60% chute; Spearman 0,14). Ver REFERENCIAS.md.

Input: /tmp/camp_daily_cpm.csv (mesma extração de cpm_decomposition.py).
"""
import csv, math, os
from collections import defaultdict
from statistics import mean, median, stdev

import sys
sys.path.insert(0, '/Users/andre.abe/meu_projeto/relatorios-abe-bp/relatorios/midia-paga/scripts')
from curve_fits import fit_power, derivative

PATH = '/tmp/camp_daily_cpm.csv'
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

# ---------- 1. Autocorrelação lag-1 do log spend ----------
acs = []
for c, rows in camps.items():
    if len(rows) < 20:
        continue
    ls = [math.log(r['spend']) for r in rows]
    n = len(ls)
    m = mean(ls)
    den = sum((v - m) ** 2 for v in ls)
    if den == 0:
        continue
    ac = sum((ls[i] - m) * (ls[i + 1] - m) for i in range(n - 1)) / den
    acs.append((c, ac, n))
print(f'== 1. Autocorrelação lag-1 log(spend) within-campanha (≥20 dias, n={len(acs)}) ==')
vals = sorted(a[1] for a in acs)
print(f'mediana {median(vals):.3f} | p25 {vals[len(vals)//4]:.3f} | p75 {vals[3*len(vals)//4]:.3f} | '
      f'% campanhas >0.8: {sum(1 for v in vals if v > 0.8)/len(vals):.0%}')

# ---------- 2 e 3. Saltos como quasi-experimentos ----------
events = []
n_days_total = 0
for c, rows in camps.items():
    if len(rows) < 12:
        continue
    n_days_total += len(rows)
    for t in range(6, len(rows) - 2):
        prev = rows[t - 3:t]
        sp_prev = [r['spend'] for r in prev]
        m_prev = mean(sp_prev)
        if m_prev <= 0:
            continue
        # estabilidade antes: CV dos 3 dias < 0.25
        if stdev(sp_prev) / m_prev > 0.25:
            continue
        jump = rows[t]['spend'] / m_prev - 1
        if abs(jump) < 0.25:
            continue
        # resposta: média de vendas nos 2 dias a partir do salto (mantendo o nível)
        post = rows[t:t + 2]
        if abs(mean(p['spend'] for p in post) / m_prev - 1) < 0.15:
            continue  # nível não se sustentou na direção do salto? exige desvio real
        d_spend = mean(p['spend'] for p in post) - m_prev
        d_sales = mean(p['sales'] for p in post) - mean(r['sales'] for r in prev)
        # curva até a véspera
        hist = rows[:t]
        f = fit_power([r['spend'] for r in hist], [r['sales'] for r in hist])
        mcac_curve = None
        if f and f['r2'] > 0.2:
            d = derivative(f, rows[t]['spend'])
            if d and d > 0:
                mcac_curve = 1 / d
        mcac_jump = d_spend / d_sales if (d_sales != 0 and d_spend != 0) else None
        events.append({'camp': c, 'date': rows[t]['date'], 'jump': jump,
                       'mcac_jump': mcac_jump, 'mcac_curve': mcac_curve,
                       'd_spend': d_spend, 'd_sales': d_sales})

n_valid = len(events)
print(f'\n== 2. Quasi-experimentos naturais ==')
print(f'saltos |Δ|≥25% com base estável: {n_valid} em {n_days_total} campanha-dias '
      f'({n_valid/n_days_total:.1%}) | pra cima: {sum(1 for e in events if e["jump"]>0)} | '
      f'pra baixo: {sum(1 for e in events if e["jump"]<0)}')

# ---------- 3. Concordância curva × salto ----------
pairs = [e for e in events
         if e['mcac_curve'] is not None and e['mcac_jump'] is not None
         and 0 < e['mcac_jump'] < 5000 and 0 < e['mcac_curve'] < 5000
         and e['jump'] > 0]  # saltos pra cima: interpretação limpa de mCAC
print(f'\n== 3. mCAC curva (até véspera) vs mCAC medido no salto (pra cima, n={len(pairs)}) ==')
if len(pairs) >= 10:
    agree = sum(1 for p in pairs
                if (p['mcac_curve'] > TETO) == (p['mcac_jump'] > TETO))
    print(f'concordância de direção vs teto R${TETO}: {agree}/{len(pairs)} ({agree/len(pairs):.0%})')
    # correlação de ranks (Spearman manual)
    def ranks(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        for pos, i in enumerate(s):
            rk[i] = pos
        return rk
    rc = ranks([p['mcac_curve'] for p in pairs])
    rj = ranks([p['mcac_jump'] for p in pairs])
    n = len(pairs)
    mc, mj = mean(rc), mean(rj)
    num = sum((rc[i]-mc)*(rj[i]-mj) for i in range(n))
    den = math.sqrt(sum((v-mc)**2 for v in rc) * sum((v-mj)**2 for v in rj))
    print(f'Spearman rank corr: {num/den:.2f}')
    print(f'mCAC salto: mediana R${median(p["mcac_jump"] for p in pairs):.0f} | '
          f'mCAC curva: mediana R${median(p["mcac_curve"] for p in pairs):.0f}')
    ratios = sorted(p['mcac_jump']/p['mcac_curve'] for p in pairs)
    print(f'ratio salto/curva: p25 {ratios[len(ratios)//4]:.2f} | mediana {median(ratios):.2f} | '
          f'p75 {ratios[3*len(ratios)//4]:.2f}')
    # baseline: sempre chutar "abaixo do teto"
    base = max(sum(1 for p in pairs if p['mcac_jump'] > TETO),
               sum(1 for p in pairs if p['mcac_jump'] <= TETO))
    print(f'baseline (chute majoritário): {base}/{len(pairs)} ({base/len(pairs):.0%})')
    # casos onde d_sales < 0 em salto pra cima (gastou mais, vendeu menos) — fora dos pairs
    neg = [e for e in events if e['jump'] > 0 and e['mcac_jump'] is not None and e['mcac_jump'] < 0]
    all_up = [e for e in events if e['jump'] > 0 and e['d_sales'] is not None and e['d_spend'] > 0]
    print(f'\nsaltos pra cima com Δvendas NEGATIVO (gastou +25%, vendeu menos): '
          f'{len(neg)}/{len(all_up)} ({len(neg)/len(all_up):.0%}) — mCAC efetivamente infinito, '
          f'a curva nunca prevê isso')
else:
    print('pares insuficientes')
