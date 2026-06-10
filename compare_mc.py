# -*- coding: utf-8 -*-
"""선거별 몬테카를로(상관 반영) 기대값 vs 관측 — 교차선거 비교"""
import json, sys, numpy as np
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(20260603)

def load(f, ec=None):
    d = json.load(open(f, encoding='utf-8'))
    return [r for r in d if (ec is None or r['ec'] == ec)]

def C2(n): return n * (n - 1) // 2
def pair_count(vals):
    c = Counter(vals); return sum(C2(v) for v in c.values() if v >= 2)
def top2(v):
    sv = sorted(v, reverse=True); return (sv[0], sv[1]) if len(sv) >= 2 else None

def mc(recs, gubun, B=2000):
    by_contest = defaultdict(list)
    for r in recs:
        if r['gubun'] == gubun:
            by_contest[r['contest']].append(r['votes'])
    # observed
    pooled_obs = []
    for c, vl in by_contest.items():
        pooled_obs += [top2(v) for v in vl if top2(v)]
    observed = pair_count(pooled_obs)
    # contest params
    units = []
    for c, vl in by_contest.items():
        arr = np.array(vl, float); Ts = arr.sum(1).astype(int)
        agg = arr.sum(0); p = agg / agg.sum() if agg.sum() > 0 else None
        if p is not None: units.append((Ts, p))
    sims = np.zeros(B, int)
    for b in range(B):
        pool = []
        for Ts, p in units:
            for T in Ts:
                if T <= 0: continue
                sv = np.sort(rng.multinomial(T, p))[::-1]
                if len(sv) >= 2: pool.append((int(sv[0]), int(sv[1])))
        sims[b] = pair_count(pool)
    N = len(pooled_obs)
    pval = (np.sum(sims >= observed) + 1) / (B + 1)
    return N, observed, sims.mean(), np.percentile(sims, 2.5), np.percentile(sims, 97.5), pval

DATASETS = [
    ('2026 지방선거(시도지사)', load('data/data_raw.json', '3')),
    ('2025 대통령선거', load('data/hist_2025_pres.json')),
]
print(f"{'선거':<24}{'구분':<10}{'단위수':>7}{'관측':>6}{'기대(MC)':>9}{'95%구간':>14}{'p값':>7}")
print('-' * 80)
out = {}
for label, recs in DATASETS:
    for gubun in ['관내사전투표', '선거일투표']:
        N, obs, mean, lo, hi, pv = mc(recs, gubun)
        out[(label, gubun)] = (N, obs, mean, lo, hi, pv)
        print(f"{label:<24}{gubun:<10}{N:>7}{obs:>6}{mean:>9.1f}{('%d~%d'%(lo,hi)):>14}{pv:>7.3f}")
json.dump({f'{k[0]}|{k[1]}': v for k, v in out.items()}, open('data/compare_mc_result.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('\nsaved data/compare_mc_result.json')
