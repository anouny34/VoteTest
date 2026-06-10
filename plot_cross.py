# -*- coding: utf-8 -*-
import json, sys, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.stdout.reconfigure(encoding='utf-8')
plt.rcParams['font.family'] = 'Malgun Gothic'; plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 110

R = json.load(open('data/compare_mc_result.json', encoding='utf-8'))
# key: '라벨|구분' -> [N, obs, mean, lo, hi, pval]
groups = [('2026 지방선거\n(시도지사)', '2026 지방선거(시도지사)'),
          ('2025 대통령선거', '2025 대통령선거')]
gubuns = [('관내사전투표', '사전투표'), ('선거일투표', '본투표')]

fig, ax = plt.subplots(figsize=(9, 4.8))
x = np.arange(len(groups)); w = 0.2
colors_obs = '#C44E52'; colors_exp = '#55A868'
offsets = [-1.5, -0.5, 0.5, 1.5]
i = 0
for gi, (gk, glabel) in enumerate(gubuns):
    obs = [R[f'{key}|{gk}'][1] for _, key in groups]
    mean = [R[f'{key}|{gk}'][2] for _, key in groups]
    lo = [R[f'{key}|{gk}'][2] - R[f'{key}|{gk}'][3] for _, key in groups]
    hi = [R[f'{key}|{gk}'][4] - R[f'{key}|{gk}'][2] for _, key in groups]
    ax.bar(x + offsets[i]*w, obs, w, color=colors_obs, alpha=0.6 if gi else 1.0,
           label=f'관측({glabel})', hatch='' if gi == 0 else '//')
    i += 1
    ax.bar(x + offsets[i]*w, mean, w, yerr=[lo, hi], capsize=4, color=colors_exp,
           alpha=0.6 if gi else 1.0, label=f'우연기대({glabel})', hatch='' if gi == 0 else '//')
    i += 1
for gi, (gk, _) in enumerate(gubuns):
    for xi, (_, key) in enumerate(groups):
        o = R[f'{key}|{gk}'][1]
        ax.text(xi + offsets[gi*2]*w, o, str(o), ha='center', va='bottom', fontsize=9)
ax.set_xticks(x); ax.set_xticklabels([g for g, _ in groups])
ax.set_title('서로 다른 두 선거 모두: 동일 득표쌍(관측)은 우연 기대값 이하\n'
             '— 2025 대선 사전투표는 우연 기대 ~20쌍인데 실제 0쌍')
ax.set_ylabel('1·2위 동일 득표쌍 수')
ax.legend(fontsize=8, ncol=2)
plt.tight_layout(); plt.savefig('figures/fig5_cross_election.png'); plt.close()
print('saved fig5_cross_election.png')
