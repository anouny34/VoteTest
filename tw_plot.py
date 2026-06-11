# -*- coding: utf-8 -*-
"""대만 그래프: fig_taiwan(대만 관측 vs 기대), fig_tw_vs_kr(한국-대만 투표소단위 비교)
입력: data/tw_result.json (tw_analyze.py), data/hist_pres_parsed.json (parse_hist_pres.py)"""
import json, sys, numpy as np
from collections import Counter
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.stdout.reconfigure(encoding='utf-8')
plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 110

TW = json.load(open('data/tw_result.json', encoding='utf-8'))
tw24 = next(v for k, v in TW.items() if '2024' in k)
tw20 = next(v for k, v in TW.items() if '2020' in k)

# ---- fig_taiwan: 대만 관측 vs 기대 ----
x = np.arange(2); w = 0.38
obs = [tw24['obs'], tw20['obs']]; exp = [tw24['exp'], tw20['exp']]
lo = [tw24['exp']-tw24['lo'], tw20['exp']-tw20['lo']]; hi = [tw24['hi']-tw24['exp'], tw20['hi']-tw20['exp']]
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(x-w/2, obs, w, label='실제 관측', color='#C44E52')
ax.bar(x+w/2, exp, w, yerr=[lo, hi], capsize=4, label='우연 기대(시뮬레이션)', color='#55A868')
for i, (o, e) in enumerate(zip(obs, exp)):
    ax.text(i-w/2, o, str(o), ha='center', va='bottom', fontsize=10)
    ax.text(i+w/2, e, f'{e:.0f}', ha='center', va='bottom', fontsize=10)
ax.set_xticks(x); ax.set_xticklabels(['2024 총통\n(라이칭더 승리)', '2020 총통\n(차이잉원 승리)'])
ax.set_title('대만(수기개표·사전투표 없음)도 동일 득표쌍 수천 쌍\n그리고 우연 기대값 이하 (1·2위 동일쌍)')
ax.set_ylabel('1·2위 동일 득표쌍 수'); ax.legend()
plt.tight_layout(); plt.savefig('figures/fig_taiwan.png'); plt.close()
print('saved figures/fig_taiwan.png')

# ---- fig_tw_vs_kr: 한국 대선(투표구) vs 대만(투개표소), 동일쌍 + 평균규모 ----
D = json.load(open('data/hist_pres_parsed.json', encoding='utf-8'))
def C2(n): return n*(n-1)//2
def p12(units):
    c = Counter(tuple(sorted(u['votes'], reverse=True)[:2]) for u in units)
    return sum(C2(v) for v in c.values() if v >= 2)
kr_order = [('한국 17대\n이명박', '제17대 (이명박·2007)'), ('한국 18대\n박근혜', '제18대 (박근혜·2012)'),
            ('한국 19대\n문재인', '제19대 (문재인·2017)'), ('한국 20대\n윤석열', '제20대 (윤석열·2022)')]
data = []
for lab, key in kr_order:
    us = D[key]['units']; avg = sum(sum(u['votes']) for u in us) / len(us)
    data.append((lab, p12(us), round(avg), 'kr', len(us)))
data.append(('대만 2020\n차이잉원', tw20['obs'], round(tw20['avg']), 'tw', 17226))
data.append(('대만 2024\n라이칭더', tw24['obs'], round(tw24['avg']), 'tw', 17795))
FR = json.load(open('data/fr_result.json', encoding='utf-8'))
data.append(('프랑스 2017\n마크롱', FR['2017']['observed'], FR['2017']['avg'], 'fr', FR['2017']['N']))
data.append(('프랑스 2022\n마크롱', FR['2022']['observed'], FR['2022']['avg'], 'fr', FR['2022']['N']))
labels = [d[0] for d in data]; col = [d[1] for d in data]
CMAP = {'kr': '#3b6fb6', 'tw': '#c0392b', 'fr': '#27a844'}
colors = [CMAP[d[3]] for d in data]
fig, ax = plt.subplots(figsize=(10.5, 5.2))
ax.bar(range(len(data)), col, color=colors)
ax.set_yscale('log'); ax.set_ylim(30, max(col) * 4)
for i, d in enumerate(data):
    ax.text(i, d[1] * 1.12, f'{d[1]:,}쌍', ha='center', va='bottom', fontsize=8.5, fontweight='bold')
    ax.text(i, 40, f'{d[4]:,}곳\n평균{d[2]}표', ha='center', va='bottom', fontsize=7.5, color='#333')
ax.set_xticks(range(len(data))); ax.set_xticklabels(labels, fontsize=8.5)
ax.set_title('투표소가 많을수록·작을수록 동일쌍 급증 (세로축 로그)\n한국 대선·대만 총통·프랑스 대선, 모두 전국 풀링 — 종이·수기개표 프랑스가 최다')
ax.set_ylabel('1·2위 동일 득표쌍 수 (로그)')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color='#3b6fb6', label='한국 대선(투표구 ~1.4만)'),
                   Patch(color='#c0392b', label='대만 총통(투개표소 ~1.8만)'),
                   Patch(color='#27a844', label='프랑스 대선(투표소 ~6.9만, 수기개표)')], loc='upper left')
plt.tight_layout(); plt.savefig('figures/fig_tw_vs_kr.png'); plt.close()
print('saved figures/fig_tw_vs_kr.png')
