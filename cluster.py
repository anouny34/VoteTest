# -*- coding: utf-8 -*-
"""'동일쌍이 한 선거구에 몰릴 확률' — clustering 검정
각 시뮬레이션마다 17개 시도지사 선거를 동시에 모의, 선거구별 동일쌍 수를 집계해
 (1) 전남에 3쌍 이상 나올 확률  (2) 17곳 중 '어느 한 곳이라도' 3쌍 이상일 확률
 (3) 한 선거구 최대 동일쌍 수의 분포  를 구한다."""
import json, sys, numpy as np
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(20260603)
recs = [r for r in json.load(open('data/data_raw.json', encoding='utf-8'))
        if r['gubun'] == '관내사전투표' and r['ec'] == '3']

def C2(n): return n*(n-1)//2
def pc(vals): c = Counter(vals); return sum(C2(v) for v in c.values() if v >= 2)

by = defaultdict(list)
for r in recs:
    by[r['sido']].append(r['votes'])
contests = []
for sido, vl in by.items():
    arr = np.array(vl, float); Ts = arr.sum(1).astype(int)
    p = arr.sum(0) / arr.sum()
    contests.append((sido, Ts, p))

# 관측: 선거구별 동일쌍
obs = {}
for sido, vl in by.items():
    obs[sido] = pc([tuple(sorted(v, reverse=True)[:2]) for v in vl])
obs_max = max(obs.values()); obs_jeonnam = obs['전라남도']

B = 4000
max_per_run = np.zeros(B, int)
jeonnam_run = np.zeros(B, int)
any_ge3 = 0
for b in range(B):
    counts = []
    for sido, Ts, p in contests:
        pool = []
        for T in Ts:
            if T <= 0: continue
            sv = np.sort(rng.multinomial(T, p))[::-1]
            pool.append((int(sv[0]), int(sv[1])))
        c = pc(pool)
        counts.append(c)
        if sido == '전라남도':
            jeonnam_run[b] = c
    max_per_run[b] = max(counts)
    if max(counts) >= 3:
        any_ge3 += 1

print(f'관측: 전남 {obs_jeonnam}쌍, 17개 시·도 중 최대 {obs_max}쌍 (전남)')
print()
print(f'(1) 전남에서 우연히 3쌍 이상 나올 확률      P = {np.mean(jeonnam_run>=3):.3f}  (기대 {jeonnam_run.mean():.2f}쌍)')
print(f'(2) 17곳 중 "어디든" 3쌍 이상 몰릴 확률      P = {any_ge3/B:.3f}   <-- look-elsewhere 보정')
print(f'(3) 한 선거구 최대 동일쌍 수 분포:')
for k in range(0, 7):
    pctge = np.mean(max_per_run >= k)
    print(f'      최대 >= {k}쌍 : {pctge:.3f}')
print(f'    관측 최대(3쌍)은 시뮬레이션의 {np.mean(max_per_run>=3)*100:.1f}% 에서 재현됨')
