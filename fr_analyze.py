# -*- coding: utf-8 -*-
"""프랑스 대선 1차투표(투표소별) 1·2위 동일쌍 분석 (2022·2017). 내무부 공식 burvot 파일."""
import sys, json, numpy as np
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(20220410)

def C2(n): return n * (n - 1) // 2
def pc(vals):
    c = Counter(vals); return sum(C2(n) for n in c.values() if n >= 2)
def t2(v): sv = sorted(v, reverse=True); return (sv[0], sv[1])

# 공식 1차 득표율(검증용)
REAL = {'2022': {'MACRON': 27.85, 'LE PEN': 23.15, 'MÉLENCHON': 21.95},
        '2017': {'MACRON': 24.01, 'LE PEN': 21.30, 'FILLON': 20.01, 'MÉLENCHON': 19.58}}
ELECTIONS = [('2022', 'data/fr_presid2022_t1.txt', 12), ('2017', 'data/fr_presid2017_t1.txt', 11)]
out = {}
for yr, fn, NC in ELECTIONS:
    txt = open(fn, encoding='cp1252').read().splitlines()
    V = []; names = None
    for line in txt[1:]:
        p = line.split(';')
        if len(p) < 25 + 7 * (NC - 1) + 1: continue
        try: v = [int(p[25 + 7 * i]) for i in range(NC)]
        except ValueError: continue
        V.append(v)
        if names is None: names = [p[23 + 7 * i] for i in range(NC)]
    N = len(V); arr = np.array(V); tot = arr.sum(); sh = dict(zip(names, arr.sum(0) / tot * 100))
    # 검증
    okv = all(abs(sh[k] - val) < 0.05 for k, val in REAL[yr].items())
    print(f'\n=== 프랑스 {yr} 1차 ===  투표소 {N:,}개, 후보 {NC}명, 득표율검증 {"OK" if okv else "FAIL"}')
    for k, val in REAL[yr].items(): print(f'   {k}: 파싱 {sh[k]:.2f}% / 실제 {val}%')
    # 동일쌍
    tuples = [t2(v) for v in V]; obs = pc(tuples)
    ngroups = sum(1 for n in Counter(tuples).values() if n >= 2)
    sizes = arr.sum(1); p = arr.sum(0) / tot; sizemap = Counter(int(s) for s in sizes)
    B = 200; sims = np.zeros(B, int)
    for b in range(B):
        pool = []
        for n, cnt in sizemap.items():
            if n <= 0: continue
            draws = rng.multinomial(n, p, size=cnt)
            s2 = np.sort(draws, axis=1)[:, ::-1][:, :2]
            pool.extend(map(tuple, s2.tolist()))
        sims[b] = pc(pool)
    e = sims.mean()
    print(f'   1·2위 동일쌍: 관측 {obs:,}쌍 (그룹 {ngroups:,}) | 우연기대 {e:,.0f} (95% {np.percentile(sims,2.5):,.0f}~{np.percentile(sims,97.5):,.0f}) | 관측{"≤" if obs<=e else ">"}기대, p={(np.sum(sims>=obs)+1)/(B+1):.3f}')
    out[yr] = {'N': N, 'candidates': NC, 'observed': obs, 'groups': ngroups,
               'expected': float(e), 'exp_lo': float(np.percentile(sims, 2.5)), 'exp_hi': float(np.percentile(sims, 97.5))}
json.dump(out, open('data/fr_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('\nsaved data/fr_result.json')
