# -*- coding: utf-8 -*-
"""
귀무모형 몬테카를로: 순수 우연으로 기대되는 동일 득표쌍 수 분포
모형A(공통 p): 각 contest 내 모든 단위가 동일 모집단 비율 p_contest에서 추출된다고 가정.
              각 단위 i의 총득표 T_i 고정, votes_i ~ Multinomial(T_i, p_contest).
모형B(단위별 부트스트랩): votes_i ~ Multinomial(T_i, p_i), p_i = 해당 단위 실제 득표비율.
              (각 단위의 실제 지지성향을 보존하고 표본오차만 부여 → 패러메트릭 부트스트랩)
관측 대비 시뮬레이션 분포에서 동일쌍 수의 기대값과 p-value(관측 이상 확률) 산출.
"""
import json, sys, numpy as np
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(20260603)
recs = json.load(open('data/data_raw.json', encoding='utf-8'))

groups = defaultdict(list)
for r in recs:
    groups[(r['contest'], r['gubun'])].append(r['votes'])

def pair_count(vals):
    c = Counter(vals)
    return sum(n * (n - 1) // 2 for n in c.values() if n >= 2)

def topkeys(draw_sorted, rankpairs):
    out = {}
    L = len(draw_sorted)
    for rp in rankpairs:
        if L > max(rp):
            out[rp] = tuple(int(draw_sorted[r]) for r in rp)
    return out

def observed(gubun, rankpairs):
    res = {rp: {'percontest': 0, 'pooled': []} for rp in rankpairs}
    for (c, g), vlist in groups.items():
        if g != gubun:
            continue
        per = {rp: [] for rp in rankpairs}
        for v in vlist:
            sv = sorted(v, reverse=True)
            for rp in rankpairs:
                if len(sv) > max(rp):
                    per[rp].append(tuple(sv[r] for r in rp))
        for rp in rankpairs:
            res[rp]['percontest'] += pair_count(per[rp])
            res[rp]['pooled'] += per[rp]
    return {rp: {'percontest': res[rp]['percontest'], 'pooled': pair_count(res[rp]['pooled'])}
            for rp in rankpairs}

def run(gubun, rankpairs, B=1000, model='A'):
    # precompute contest unit info
    contests = []
    for (c, g), vlist in groups.items():
        if g != gubun:
            continue
        arr = np.array(vlist, dtype=float)  # units x cands
        Ts = arr.sum(axis=1).astype(int)
        if model == 'A':
            agg = arr.sum(axis=0)
            p = agg / agg.sum() if agg.sum() > 0 else None
            contests.append((Ts, p, None))
        else:
            with np.errstate(invalid='ignore', divide='ignore'):
                P = np.where(Ts[:, None] > 0, arr / Ts[:, None], 0)
            contests.append((Ts, None, P))
    sims_pc = {rp: np.zeros(B, int) for rp in rankpairs}
    sims_pool = {rp: np.zeros(B, int) for rp in rankpairs}
    for b in range(B):
        pool = {rp: [] for rp in rankpairs}
        for (Ts, p, P) in contests:
            per = {rp: [] for rp in rankpairs}
            for i, T in enumerate(Ts):
                if T <= 0:
                    continue
                pp = p if model == 'A' else P[i]
                draw = rng.multinomial(T, pp)
                sv = np.sort(draw)[::-1]
                for rp in rankpairs:
                    if len(sv) > max(rp):
                        per[rp].append(tuple(int(sv[r]) for r in rp))
            for rp in rankpairs:
                sims_pc[rp][b] += pair_count(per[rp])
                pool[rp] += per[rp]
        for rp in rankpairs:
            sims_pool[rp][b] = pair_count(pool[rp])
    return sims_pc, sims_pool

if __name__ == '__main__':
    rankpairs = [(0, 1), (1, 2), (2, 3)]
    B = 2000
    for gubun in ['관내사전투표', '선거일투표']:
        obs = observed(gubun, rankpairs)
        for model in ['A', 'B']:
            pc, pool = run(gubun, rankpairs, B=B, model=model)
            print('\n' + '=' * 70)
            print(f'[{gubun}] 모형{model}  (B={B})')
            for rp in rankpairs:
                ob_pc = obs[rp]['percontest']; ob_pool = obs[rp]['pooled']
                sp = pc[rp]; spool = pool[rp]
                lab = tuple(r + 1 for r in rp)
                pval_pc = (np.sum(sp >= ob_pc) + 1) / (B + 1)
                pval_pool = (np.sum(spool >= ob_pool) + 1) / (B + 1)
                print(f'  순위쌍{lab} contest내: 관측={ob_pc:4d} | 기대={sp.mean():6.1f} '
                      f'(95%구간 {np.percentile(sp,2.5):.0f}~{np.percentile(sp,97.5):.0f}) p={pval_pc:.3f}')
                print(f'           전국풀링: 관측={ob_pool:4d} | 기대={spool.mean():6.1f} '
                      f'(95%구간 {np.percentile(spool,2.5):.0f}~{np.percentile(spool,97.5):.0f}) p={pval_pool:.3f}')
