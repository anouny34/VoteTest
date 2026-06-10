# -*- coding: utf-8 -*-
"""보고서용 그래프 생성"""
import json, sys, numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter
from montecarlo import run, observed, groups
sys.stdout.reconfigure(encoding='utf-8')

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 110

recs = json.load(open('data/data_raw.json', encoding='utf-8'))
def top(v, k):
    sv = sorted(v, reverse=True); return sv[k] if len(sv) > k else None

# ---- 데이터 준비 ----
a_sa = [top(r['votes'], 0) for r in recs if r['gubun'] == '관내사전투표']
rankpairs = [(0,1),(1,2),(2,3)]
obs_sa = observed('관내사전투표', rankpairs)
obs_bn = observed('선거일투표', rankpairs)

print('MC 모형A 실행중...')
pc_sa, pool_sa = run('관내사전투표', rankpairs, B=2000, model='A')
pc_bn, pool_bn = run('선거일투표', rankpairs, B=2000, model='A')

# ============ Fig1: 1위 득표수 분포 (클러스터링) ============
fig, ax = plt.subplots(figsize=(8,4.2))
ax.hist(a_sa, bins=60, color='#4C72B0', edgecolor='white')
med = int(np.median(a_sa))
ax.axvline(med, color='crimson', ls='--', lw=2, label=f'중앙값 {med}표')
ax.set_title('사전투표소별 1위 후보 득표수 분포\n(소규모 투표소에 집중 → 동일값이 겹치기 쉬움)')
ax.set_xlabel('1위 후보 득표수'); ax.set_ylabel('투표소 수')
ax.legend()
plt.tight_layout(); plt.savefig('figures/fig1_distribution.png'); plt.close()

# ============ Fig2: 순위쌍별 동일쌍 (관측 vs 기대) ============
labels = ['(1위,2위)', '(2위,3위)', '(3위,4위)']
obs_vals = [obs_sa[rp]['pooled'] for rp in rankpairs]
exp_vals = [pool_sa[rp].mean() for rp in rankpairs]
x = np.arange(len(labels)); w=0.38
fig, ax = plt.subplots(figsize=(8,4.2))
ax.bar(x-w/2, obs_vals, w, label='실제 관측', color='#C44E52')
ax.bar(x+w/2, exp_vals, w, label='우연 기대(시뮬레이션)', color='#55A868')
for i,(o,e) in enumerate(zip(obs_vals,exp_vals)):
    ax.text(i-w/2,o,str(o),ha='center',va='bottom',fontsize=9)
    ax.text(i+w/2,e,f'{e:.0f}',ha='center',va='bottom',fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_title('순위쌍별 동일 득표쌍 수 — 사전투표 (전국 풀링)\n하위 순위일수록 동일쌍 폭증: 전형적 우연 현상')
ax.set_ylabel('동일 득표쌍 수'); ax.legend()
plt.tight_layout(); plt.savefig('figures/fig2_rankpairs.png'); plt.close()

# ============ Fig3: 사전 vs 본투표, 세 방법 비교 (1위2위) ============
# 간이 경우의수 E
def closed_E(gubun):
    A=[top(r['votes'],0) for r in recs if r['gubun']==gubun]
    B=[top(r['votes'],1) for r in recs if r['gubun']==gubun]
    N=len(A); C2=N*(N-1)//2
    def eff(v): c=Counter(v); n=len(v); return 1/sum((x/n)**2 for x in c.values())
    return C2/(eff(A)*eff(B))
methods = ['실제 관측','간이 경우의수\n공식','몬테카를로\n시뮬레이션']
sa_vals = [obs_sa[(0,1)]['pooled'], closed_E('관내사전투표'), pool_sa[(0,1)].mean()]
bn_vals = [obs_bn[(0,1)]['pooled'], closed_E('선거일투표'), pool_bn[(0,1)].mean()]
x=np.arange(len(methods)); w=0.38
fig,ax=plt.subplots(figsize=(8,4.2))
ax.bar(x-w/2, sa_vals, w, label='사전투표', color='#4C72B0')
ax.bar(x+w/2, bn_vals, w, label='본투표(대조군)', color='#DD8452')
for i,(s,b) in enumerate(zip(sa_vals,bn_vals)):
    ax.text(i-w/2,s,f'{s:.1f}',ha='center',va='bottom',fontsize=9)
    ax.text(i+w/2,b,f'{b:.1f}',ha='center',va='bottom',fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(methods)
ax.set_title('1·2위 동일 득표쌍: 관측치와 우연 기대값이 같은 수준\n(세 가지 방법 모두 한 자릿수~십여 개로 수렴)')
ax.set_ylabel('동일 득표쌍 수'); ax.legend()
plt.tight_layout(); plt.savefig('figures/fig3_three_methods.png'); plt.close()

# ============ Fig4: 귀무분포 + 관측치 위치 ============
dist = pool_sa[(0,1)]; obsv = obs_sa[(0,1)]['pooled']
fig,ax=plt.subplots(figsize=(8,4.2))
ax.hist(dist, bins=range(0,int(dist.max())+2), color='#55A868', edgecolor='white', alpha=0.85)
ax.axvline(obsv, color='crimson', lw=2.5, label=f'실제 관측 = {obsv}쌍')
ax.axvline(dist.mean(), color='navy', ls='--', lw=2, label=f'우연 평균 = {dist.mean():.1f}쌍')
ax.set_title('"우연이라면 몇 쌍?" — 시뮬레이션 2,000회 분포 (사전투표 1·2위)\n관측치는 우연 분포의 한가운데에 위치')
ax.set_xlabel('동일 득표쌍 수'); ax.set_ylabel('시뮬레이션 횟수'); ax.legend()
plt.tight_layout(); plt.savefig('figures/fig4_null_dist.png'); plt.close()

print('saved: fig1_distribution.png, fig2_rankpairs.png, fig3_three_methods.png, fig4_null_dist.png')
print(f'관측 사전(1,2)={obsv}, 간이={sa_vals[1]:.2f}, MC평균={dist.mean():.2f}, p={(np.sum(dist>=obsv)+1)/(len(dist)+1):.3f}')
