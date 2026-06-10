# -*- coding: utf-8 -*-
"""보고서 수치 전수 검증: 데이터에서 재계산 → 보고서 주장값과 대조"""
import json, sys, numpy as np
from collections import Counter, defaultdict
from math import comb
sys.stdout.reconfigure(encoding='utf-8')

def chk(label, got, claim, tol=0):
    ok = (abs(got - claim) <= tol) if isinstance(claim, (int, float)) else (got == claim)
    print(f"[{'OK ' if ok else 'FAIL'}] {label}: 계산={got} / 보고서={claim}")
    return ok

recs = json.load(open('data/data_raw.json', encoding='utf-8'))
sa = [r for r in recs if r['gubun'] == '관내사전투표']
bn = [r for r in recs if r['gubun'] == '선거일투표']

print('===== §2 데이터 규모 =====')
chk('사전 단위수', len(sa), 3731)
chk(' 시도지사 사전', len([r for r in sa if r['ec'] == '3']), 3558)
chk(' 국회의원 사전', len([r for r in sa if r['ec'] == '2']), 173)
chk('본투표 단위수', len(bn), 3758)
chk('총 레코드', len(recs), 7489)
tot = sum(sum(r['votes']) for r in sa)
chk('사전 총표수', tot, 7557544)
chk('사전 평균(반올림)', round(np.mean([sum(r['votes']) for r in sa])), 2026)
chk('사전 최소 총득표', min(sum(r['votes']) for r in sa), 46)
chk('사전 최대 총득표', max(sum(r['votes']) for r in sa), 10080)
ncand = set(len(r['cands']) for r in sa if r['ec'] == '3')
chk('시도지사 후보수 최소', min(ncand), 2); chk('시도지사 후보수 최대', max(ncand), 5)

print('\n===== §4-1 관측 동일쌍 =====')
def C2(n): return n*(n-1)//2
def pc(vals): c = Counter(vals); return sum(C2(v) for v in c.values() if v >= 2)
def topk(v, rp): sv = sorted(v, reverse=True); return tuple(sv[r] for r in rp) if len(sv) > max(rp) else None
def grp(recset):
    g = defaultdict(list)
    for r in recset: g[r['contest']].append(r['votes'])
    return g
def collisions(recset, rp):
    g = grp(recset); within = 0; pool = []
    for c, vl in g.items():
        vals = [topk(v, rp) for v in vl]; vals = [x for x in vals if x]
        within += pc(vals); pool += vals
    return within, pc(pool)
claims = {(0,1): (4,9,2,4), (1,2): (12,30,14,24), (2,3): (232,593,119,259)}
for rp, (sw, sp, bw, bp) in claims.items():
    w,p = collisions(sa, rp); chk(f'사전{tuple(r+1 for r in rp)} 시도내', w, sw); chk(f'사전{tuple(r+1 for r in rp)} 풀링', p, sp)
    w,p = collisions(bn, rp); chk(f'본투표{tuple(r+1 for r in rp)} 시도내', w, bw); chk(f'본투표{tuple(r+1 for r in rp)} 풀링', p, bp)
# 전체벡터 완전일치
def fullvec(recset):
    g = defaultdict(list)
    for r in recset: g[(r['contest'], tuple(r['votes']))].append(1)
    return sum(C2(len(v)) for v in g.values() if len(v) >= 2)
chk('사전 전체벡터일치', fullvec(sa), 0); chk('본투표 전체벡터일치', fullvec(bn), 2)

print('\n===== §4-4 간이 경우의수 =====')
A = [sorted(r['votes'], reverse=True)[0] for r in sa]
B = [sorted(r['votes'], reverse=True)[1] for r in sa]
N = len(A); chk('N', N, 3731)
chk('C(N,2) 만단위', round(C2(N)/1e4), 696)  # 695.8만
R = max(A); chk('R(최대1위)', R, 7460)
chk('M1=R^2/2 만단위', round(R*R/2/1e4), 2780, tol=5)
chk('E1', round(C2(N)/(R*R/2), 2), 0.25, tol=0.01)
def eff(x): c = Counter(x); n = len(x); return 1/sum((v/n)**2 for v in c.values())
Ma, Mb = eff(A), eff(B)
chk('Ma', round(Ma), 1562, tol=1); chk('Mb', round(Mb), 922, tol=1)
chk('M2 만단위', round(Ma*Mb/1e4), 144, tol=1)
chk('E2', round(C2(N)/(Ma*Mb), 2), 4.83, tol=0.02)
chk('배율 M1/M2', round((R*R/2)/(Ma*Mb)), 19, tol=2)  # 약 20배
chk('median 1위', int(np.median(A)), 1094)
chk('1위값<median 개수', sum(1 for v in [3030,1401,606,506,356,309,281,182,87] if v < 1094), 7)

print('\n===== §6 생일 비유 =====')
chk('C(23,2)', C2(23), 253)
chk('696만/144만 반올림', round(C2(N)/(Ma*Mb)), 5, tol=0)

print('\n===== §5 2025 대선 =====')
pres = json.load(open('data/hist_2025_pres.json', encoding='utf-8'))
psa = [r for r in pres if r['gubun'] == '관내사전투표']
chk('대선 사전 단위수', len(psa), 3554)
chk('대선 사전 총표수 만단위', round(sum(sum(r['votes']) for r in psa)/1e4), 1106, tol=30)
mc = json.load(open('data/compare_mc_result.json', encoding='utf-8'))
print('  compare_mc 저장값:', {k: v[:3] for k, v in mc.items()})
