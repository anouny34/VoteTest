# -*- coding: utf-8 -*-
"""과거 대선 그래프: 권역별 동일쌍(fig_hist_bloc) + 전국 관측 vs 우연기대(fig_hist_national)
입력: data/hist_pres_parsed.json (parse_hist_pres.py), data/hist_mc2_result.json (hist_mc2.py)"""
import json, sys, numpy as np
from collections import Counter, defaultdict
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.stdout.reconfigure(encoding='utf-8')
plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 110

D = json.load(open('data/hist_pres_parsed.json', encoding='utf-8'))
def C2(n): return n*(n-1)//2
def p12(us):
    c = Counter(tuple(sorted(u['votes'], reverse=True)[:2]) for u in us)
    return sum(C2(v) for v in c.values() if v >= 2)

labels = list(D.keys())
short = {'제17대 (이명박·2007)': '17대\n이명박(보수)', '제18대 (박근혜·2012)': '18대\n박근혜(보수)',
         '제19대 (문재인·2017)': '19대\n문재인(진보)', '제20대 (윤석열·2022)': '20대\n윤석열(보수)',
         '제21대 (이재명·2025)': '21대\n이재명(진보)'}
x = np.arange(len(labels))

# ---- fig_hist_bloc: 권역별 동일쌍 ----
BLOC = {'호남(진보 텃밭)': ['광주광역시', '전라남도', '전라북도', '전북특별자치도'],
        '영남(보수 텃밭)': ['대구광역시', '경상북도', '부산광역시', '경상남도', '울산광역시'],
        '수도권(경합)': ['서울특별시', '경기도', '인천광역시']}
colors = {'호남(진보 텃밭)': '#3b6fb6', '영남(보수 텃밭)': '#c0392b', '수도권(경합)': '#7f8c8d'}
counts = {bn: [] for bn in BLOC}
for label in labels:
    by = defaultdict(list)
    for u in D[label]['units']: by[u['sido']].append(u)
    for bn, sidos in BLOC.items():
        counts[bn].append(p12([u for s in sidos for u in by.get(s, [])]))
w = 0.26
fig, ax = plt.subplots(figsize=(9, 4.6))
for i, bn in enumerate(BLOC):
    bars = ax.bar(x + (i-1)*w, counts[bn], w, label=bn, color=colors[bn])
    for b, val in zip(bars, counts[bn]):
        ax.text(b.get_x()+b.get_width()/2, val, str(val), ha='center', va='bottom', fontsize=8)
ax.set_xticks(x); ax.set_xticklabels([short[l] for l in labels])
ax.set_title('과거 대선 동일 득표쌍은 진보·보수 텃밭 양쪽에서 모두 나온다\n(보수 텃밭 영남에 진보 텃밭 호남만큼·또는 더 많이)')
ax.set_ylabel('1·2위 동일 득표쌍 수'); ax.legend()
plt.tight_layout(); plt.savefig('figures/fig_hist_bloc.png'); plt.close()
print('saved figures/fig_hist_bloc.png')

# ---- fig_hist_national: 전국 관측 vs 우연기대 (전국 풀링, hist_mc2) ----
R = json.load(open('data/hist_mc2_result.json', encoding='utf-8'))
obs = [R[l]['obs'] for l in labels]; exp = [R[l]['exp'] for l in labels]
lo = [R[l]['exp']-R[l]['lo'] for l in labels]; hi = [R[l]['hi']-R[l]['exp'] for l in labels]
w = 0.38
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.bar(x-w/2, obs, w, label='실제 관측', color='#C44E52')
ax.bar(x+w/2, exp, w, yerr=[lo, hi], capsize=4, label='우연 기대(시뮬레이션)', color='#55A868')
for i, (o, e) in enumerate(zip(obs, exp)):
    ax.text(i-w/2, o, str(o), ha='center', va='bottom', fontsize=9)
    ax.text(i+w/2, e, f'{e:.0f}', ha='center', va='bottom', fontsize=9)
ax.set_xticks(x); ax.set_xticklabels([short[l] for l in labels])
ax.set_title('과거 대선 전국 동일쌍(전국 풀링): 관측치는 우연 기대값 이하\n(보수·진보 승리 가리지 않고 모두)')
ax.set_ylabel('1·2위 동일 득표쌍 수'); ax.legend()
plt.tight_layout(); plt.savefig('figures/fig_hist_national.png'); plt.close()
print('saved figures/fig_hist_national.png')
