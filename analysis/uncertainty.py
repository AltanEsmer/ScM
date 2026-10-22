"""Illustrative two-sided 95% Clopper-Pearson intervals, without dependencies."""
import json
import math

SOURCE = 'https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm'


def _tail(k, n, p):
    if p == 0:
        return 0.0
    if p == 1:
        return 1.0
    return math.fsum(math.exp(math.lgamma(n + 1) - math.lgamma(i + 1)
                             - math.lgamma(n - i + 1) + i * math.log(p)
                             + (n - i) * math.log1p(-p)) for i in range(k, n + 1))


def _invert_tail(k, n, target):
    low, high = 0.0, 1.0
    for _ in range(80):
        middle = (low + high) / 2
        if _tail(k, n, middle) < target:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def clopper_pearson(k, n):
    """Invert binomial tails at .025 and .975 per NIST's exact definition."""
    if type(k) is not int or type(n) is not int or n <= 0 or not 0 <= k <= n:
        raise ValueError('counts must be integers with n > 0 and 0 <= k <= n')
    return (0.0 if k == 0 else _invert_tail(k, n, 0.025),
            1.0 if k == n else _invert_tail(k + 1, n, 0.975))


if __name__ == '__main__':
    print(json.dumps({
        'method': 'Two-sided 95% Clopper-Pearson exact binomial intervals',
        'source': SOURCE,
        'assumptions': 'Illustrative iid Bernoulli trials with a common fixed success probability.',
        'limitations': 'No adjustment for selection or shared-task correlation. No pooled CI for the 90 pilot responses.',
        'illustrations': [dict(k=k, n=n, lower=clopper_pearson(k, n)[0],
                               upper=clopper_pearson(k, n)[1])
                          for k, n in [(0, 3), (1, 3), (2, 3), (3, 3), (5, 5)]]
    }, indent=2))
