# -*- coding: utf-8 -*-
"""
경우의 수 기반 동일쌍 기대값 (몬테카를로 불필요, 생일 문제 닫힌 공식)
  E[동일쌍] = C(N,2) / M
  N = 투표소 수,  M = (1위,2위) 득표수가 가질 수 있는 '경우의 수'
모형:
  ① 전범위 균등:  M = (1위 최대득표 R)² / 2      (b<=a 삼각형 영역)
  ② 유효 경우의수: M = Ma * Mb,  Ma=1/Σp_a², Mb=1/Σp_b²  (실제 분포 집중도 반영)
"""
import json, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
recs = json.load(open('data/data_raw.json', encoding='utf-8'))

def C2(n):
    return n * (n - 1) // 2

def eff_cases(vals):
    c = Counter(vals); n = len(vals)
    return 1.0 / sum((v / n) ** 2 for v in c.values())

def observed_pairs(pairs):
    c = Counter(pairs)
    return sum(C2(v) for v in c.values() if v >= 2)

for gubun in ['관내사전투표', '선거일투표']:
    sa = [r for r in recs if r['gubun'] == gubun]
    A, B, P = [], [], []
    for r in sa:
        sv = sorted(r['votes'], reverse=True)
        if len(sv) >= 2:
            A.append(sv[0]); B.append(sv[1]); P.append((sv[0], sv[1]))
    N = len(A)
    R = max(A)
    pairs_total = C2(N)
    # 모형①
    M1 = R * R / 2
    E1 = pairs_total / M1
    # 모형②
    Ma, Mb = eff_cases(A), eff_cases(B)
    M2 = Ma * Mb
    E2 = pairs_total / M2
    obs = observed_pairs(P)
    print('=' * 64)
    print(f'[{gubun}]  투표소 N={N},  비교 가능한 쌍 C(N,2)={pairs_total:,}')
    print(f'  관측 (1위,2위) 동일쌍 = {obs}')
    print(f'  ① 전범위 균등:  M=R²/2={M1:,.0f}  (R={R})  ->  기대 E={E1:.2f}')
    print(f'  ② 유효경우의수: M=Ma·Mb={Ma:.0f}×{Mb:.0f}={M2:,.0f}  ->  기대 E={E2:.2f}')
