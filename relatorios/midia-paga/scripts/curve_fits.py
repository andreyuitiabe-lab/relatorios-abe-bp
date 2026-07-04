"""
Biblioteca de ajuste de curvas usada em toda a análise de mídia paga.

Curvas suportadas:
- Lei de potência: sales = a * spend^b (log-log OLS)
- Logística: sales = V * (1 - exp(-k*spend))
- Polinomial grau 2 e 3

Todas retornam dict com 'kind', parâmetros, 'r2'.
"""
import math
from statistics import mean


def solve_linear(A, b):
    """Resolve sistema linear A @ x = b via eliminação gaussiana com pivot."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        mr = i
        for k in range(i + 1, n):
            if abs(M[k][i]) > abs(M[mr][i]):
                mr = k
        M[i], M[mr] = M[mr], M[i]
        if abs(M[i][i]) < 1e-15:
            return None
        for k in range(i + 1, n):
            f = M[k][i] / M[i][i]
            for j in range(i, n + 1):
                M[k][j] -= f * M[i][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


def fit_power(spends, sales):
    """Ajuste log-log OLS: sales = a * spend^b"""
    valid = [(s, v) for s, v in zip(spends, sales) if s > 0 and v > 0]
    n = len(valid)
    if n < 3:
        return None
    lx = [math.log(p[0]) for p in valid]
    ly = [math.log(p[1]) for p in valid]
    mx, my = sum(lx) / n, sum(ly) / n
    num = sum((lx[i] - mx) * (ly[i] - my) for i in range(n))
    den = sum((lx[i] - mx) ** 2 for i in range(n))
    if den == 0:
        return None
    b = num / den
    a = math.exp(my - b * mx)
    pred = [math.log(a) + b * lx[i] for i in range(n)]
    ss_res = sum((ly[i] - pred[i]) ** 2 for i in range(n))
    ss_tot = sum((ly[i] - my) ** 2 for i in range(n))
    return {'kind': 'power', 'a': a, 'b': b,
            'r2': 1 - ss_res / ss_tot if ss_tot > 0 else 0}


def fit_logistic(spends, sales):
    """Ajuste V * (1 - exp(-k*spend)) via busca em grid de k, V por OLS condicional."""
    valid = [(s, v) for s, v in zip(spends, sales) if s > 0 and v > 0]
    n = len(valid)
    if n < 5:
        return None
    sp = [p[0] for p in valid]
    sv = [p[1] for p in valid]
    smax = max(sp)
    my = sum(sv) / n
    ss_tot = sum((sv[j] - my) ** 2 for j in range(n))
    best = None
    for i in range(300):
        k = (0.01 + i * 0.03) / smax * 5
        try:
            f = [1 - math.exp(-k * s) for s in sp]
        except OverflowError:
            continue
        num = sum(sv[j] * f[j] for j in range(n))
        den = sum(f[j] ** 2 for j in range(n))
        if den == 0:
            continue
        V = num / den
        if V <= 0:
            continue
        pred = [V * f[j] for j in range(n)]
        ss = sum((sv[j] - pred[j]) ** 2 for j in range(n))
        r2 = 1 - ss / ss_tot if ss_tot > 0 else 0
        if best is None or r2 > best['r2']:
            best = {'kind': 'logistic', 'V': V, 'k': k, 'r2': r2}
    return best


def fit_poly(spends, sales, degree=3):
    """Ajuste polinomial via normal equations, normalizado."""
    valid = [(s, v) for s, v in zip(spends, sales) if s > 0 and v > 0]
    n = len(valid)
    if n < degree + 2:
        return None
    sp = [p[0] for p in valid]
    sv = [p[1] for p in valid]
    smax = max(sp)
    sp_n = [s / smax for s in sp]
    XtX = [[0.0] * (degree + 1) for _ in range(degree + 1)]
    Xty = [0.0] * (degree + 1)
    for i in range(n):
        for r in range(degree + 1):
            Xty[r] += (sp_n[i] ** r) * sv[i]
            for c in range(degree + 1):
                XtX[r][c] += sp_n[i] ** (r + c)
    coefs_n = solve_linear(XtX, Xty)
    if coefs_n is None:
        return None
    coefs = [coefs_n[r] / (smax ** r) for r in range(degree + 1)]
    pred = [sum(coefs[r] * (sp[i] ** r) for r in range(degree + 1)) for i in range(n)]
    my = sum(sv) / n
    ss_tot = sum((sv[i] - my) ** 2 for i in range(n))
    ss_res = sum((sv[i] - pred[i]) ** 2 for i in range(n))
    return {'kind': f'poly{degree}', 'coefs': coefs,
            'r2': 1 - ss_res / ss_tot if ss_tot > 0 else 0}


def evaluate(fit, s):
    """Retorna vendas previstas pelo fit no gasto s."""
    if fit['kind'] == 'power':
        return fit['a'] * (s ** fit['b']) if s > 0 else 0
    elif fit['kind'] == 'logistic':
        return fit['V'] * (1 - math.exp(-fit['k'] * s))
    elif fit['kind'].startswith('poly'):
        return sum(fit['coefs'][r] * (s ** r) for r in range(len(fit['coefs'])))


def derivative(fit, s):
    """Derivada d(sales)/d(spend) — reciproco = CPA marginal."""
    if fit['kind'] == 'power':
        return fit['a'] * fit['b'] * (s ** (fit['b'] - 1)) if s > 0 else None
    elif fit['kind'] == 'logistic':
        return fit['V'] * fit['k'] * math.exp(-fit['k'] * s) if s > 0 else None
    elif fit['kind'].startswith('poly'):
        c = fit['coefs']
        return sum(r * c[r] * (s ** (r - 1)) for r in range(1, len(c)))


def find_spend_for_cpa(fit, cpa_target, smin, smax):
    """Encontra gasto onde CPA marginal = cpa_target dentro do range [smin, smax]."""
    best_s = None
    best_diff = float('inf')
    step = max(100, (smax - smin) / 200)
    s = smin
    while s <= smax:
        d = derivative(fit, s)
        if d and d > 0:
            cur = 1 / d
            diff = abs(cur - cpa_target)
            if diff < best_diff:
                best_diff = diff
                best_s = s
        s += step
    return best_s


def adstock_geometric(x, alpha=0.50, l_max=14, normalize=True):
    """
    Adstock geométrico com janela finita (replica MMM da casa).
    Parâmetros default: meta_ads_vendas (alpha=0.50, l_max=14d).
    """
    weights = [alpha ** k for k in range(l_max + 1)]
    if normalize:
        s = sum(weights)
        weights = [w / s for w in weights]
    T = len(x)
    out = [0.0] * T
    for t in range(T):
        for lag in range(min(l_max + 1, t + 1)):
            out[t] += weights[lag] * x[t - lag]
    return out


def choose_fit(spends, sales, n_pts=None):
    """
    Escolhe modelo pelo nº de pontos:
      >=30 → polinomial grau 3
      >=15 → logística
      >=5  → lei de potência
      <5   → None
    """
    n = n_pts or sum(1 for s in spends if s > 0)
    if n >= 30:
        return fit_poly(spends, sales, 3) or fit_logistic(spends, sales) or fit_power(spends, sales)
    elif n >= 15:
        return fit_logistic(spends, sales) or fit_power(spends, sales)
    elif n >= 5:
        return fit_power(spends, sales)
    return None
