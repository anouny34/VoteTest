# -*- coding: utf-8 -*-
"""과거 대선 전국 풀링 동일쌍: 관측 vs 우연기대
귀무모형: 각 투표소 votes ~ Multinomial(T_i, p_시도) (지역 편차 보존), 전국 풀로 모아 충돌 계수."""
import json, sys, numpy as np
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(20260603)
D = json.load(open('data/hist_pres_parsed.json', encoding='utf-8'))
def C2(n): return n*(n-1)//2
def pc(vals):
    c = Counter(vals); return sum(C2(v) for v in c.values() if v >= 2)
def t2(v): sv = sorted(v, reverse=True); return (sv[0], sv[1])
B = 500
out = {}
for label, v in D.items():
    units = v['units']
    obs = pc([t2(u['votes']) for u in units])      # 전국 풀링 관측
    by = defaultdict(list)
    for u in units: by[u['sido']].append(u['votes'])
    cu = []
    for s, vl in by.items():
        arr = np.array(vl, float); Ts = arr.sum(1).astype(int)
        p = arr.sum(0) / arr.sum(); cu.append((Ts, p))
    sims = np.zeros(B, int)
    for b in range(B):
        pool = []
        for Ts, p in cu:
            for T in Ts:
                if T <= 0: continue
                sv = np.sort(rng.multinomial(T, p))[::-1]
                pool.append((int(sv[0]), int(sv[1])))
        sims[b] = pc(pool)
    pv = (np.sum(sims >= obs) + 1) / (B + 1)
    out[label] = dict(camp=v['camp'], obs=int(obs), exp=float(sims.mean()),
                      lo=float(np.percentile(sims, 2.5)), hi=float(np.percentile(sims, 97.5)), p=float(pv))
    print(f"{label} 관측 {obs} | 기대(전국풀링) {sims.mean():.0f} ({np.percentile(sims,2.5):.0f}~{np.percentile(sims,97.5):.0f}) p={pv:.3f}", flush=True)
json.dump(out, open('data/hist_mc2_result.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('saved data/hist_mc2_result.json')
