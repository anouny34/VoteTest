# -*- coding: utf-8 -*-
"""선거구(시·도) 내부에서의 동일쌍: 같은 후보군·같은 조건 투표소끼리 관측 vs 우연기대"""
import json, sys, numpy as np
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(20260603)
recs = [r for r in json.load(open('data/data_raw.json', encoding='utf-8'))
        if r['gubun'] == '관내사전투표' and r['ec'] == '3']  # 시도지사 사전투표

def C2(n): return n*(n-1)//2
def pc(vals): c = Counter(vals); return sum(C2(v) for v in c.values() if v >= 2)
def top2(v): sv = sorted(v, reverse=True); return (sv[0], sv[1])

by = defaultdict(list)
for r in recs:
    by[r['sido']].append(r['votes'])

print(f"{'시·도':<12}{'투표소':>6}{'관측쌍':>7}{'기대(MC)':>9}{'95%구간':>12}{'p값':>7}")
print('-'*60)
B = 3000
tot_obs = tot_exp = 0
for sido, vl in by.items():
    obs = pc([top2(v) for v in vl])
    arr = np.array(vl, float); Ts = arr.sum(1).astype(int)
    agg = arr.sum(0); p = agg/agg.sum()
    sims = np.zeros(B, int)
    for b in range(B):
        pool = []
        for T in Ts:
            if T <= 0: continue
            sv = np.sort(rng.multinomial(T, p))[::-1]
            pool.append((int(sv[0]), int(sv[1])))
        sims[b] = pc(pool)
    pv = (np.sum(sims >= obs)+1)/(B+1)
    tot_obs += obs; tot_exp += sims.mean()
    flag = '  <-- 관측>기대' if obs > np.percentile(sims, 97.5) else ''
    print(f"{sido:<12}{len(vl):>6}{obs:>7}{sims.mean():>9.2f}{('%d~%d'%(np.percentile(sims,2.5),np.percentile(sims,97.5))):>12}{pv:>7.3f}{flag}")
print('-'*60)
print(f"{'합계':<12}{sum(len(v) for v in by.values()):>6}{tot_obs:>7}{tot_exp:>9.2f}")
