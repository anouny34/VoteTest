# -*- coding: utf-8 -*-
"""
동일 득표쌍(collision) 분석
- 관측: 관내사전투표 / 선거일투표 단위에서 (1위,2위) 등 순위쌍이 일치하는 투표소 쌍 수
- 귀무모형: 각 투표소의 총득표 T_i 고정, 후보 득표를 Multinomial(T_i, p_contest)로 생성하여
  순수 우연으로 기대되는 동일쌍 분포를 몬테카를로로 추정 → 관측치와 비교
"""
import json, sys, numpy as np
from collections import defaultdict, Counter
from itertools import combinations
sys.stdout.reconfigure(encoding='utf-8')

rng = np.random.default_rng(20260603)
recs = json.load(open('data/data_raw.json', encoding='utf-8'))
print(f'총 레코드: {len(recs)}')

def pair_count(values):
    """values: list of tuples. returns number of unordered matching pairs = sum C(n,2)."""
    c = Counter(values)
    pairs = sum(n * (n - 1) // 2 for n in c.values() if n >= 2)
    groups = sum(1 for n in c.values() if n >= 2)
    return pairs, groups

def topk_key(vec, ranks):
    """vec: vote list. ranks e.g. (0,1) for 1st&2nd (0-indexed). returns tuple of those rank vote counts."""
    sv = sorted(vec, reverse=True)
    if len(sv) <= max(ranks):
        return None
    return tuple(sv[r] for r in ranks)

# group records by (contest, gubun)
groups = defaultdict(list)
for r in recs:
    groups[(r['contest'], r['gubun'])].append(r)

def analyze_observed(gubun_filter, rankpairs):
    """returns dict rankpair-> (pooled_pairs, pooled_groups, per_contest_total_pairs, n_units)"""
    out = {}
    for rp in rankpairs:
        pooled_vals = []
        per_contest_pairs = 0
        n_units = 0
        for (contest, gubun), rs in groups.items():
            if gubun != gubun_filter:
                continue
            vals = [topk_key(r['votes'], rp) for r in rs]
            vals = [v for v in vals if v is not None]
            n_units += len(vals)
            p, g = pair_count(vals)
            per_contest_pairs += p
            pooled_vals += vals
        pp, pg = pair_count(pooled_vals)
        out[rp] = dict(pooled_pairs=pp, pooled_groups=pg,
                       per_contest_pairs=per_contest_pairs, n_units=n_units)
    return out

def full_vector_collisions(gubun_filter):
    pooled = []
    per_contest = 0
    for (contest, gubun), rs in groups.items():
        if gubun != gubun_filter:
            continue
        vals = [tuple(r['votes']) for r in rs]
        pooled += [(contest,) + v for v in vals]  # full vector pooled needs same candset -> keep per contest
        p, g = pair_count([tuple(r['votes']) for r in rs])
        per_contest += p
    # pooled across contests only meaningful if same candidate count; report per-contest sum
    return per_contest

def montecarlo_null(gubun_filter, rankpairs, B=2000):
    """simulate B times; return per rankpair list of pooled_pairs and per_contest_pairs."""
    # precompute per contest: totals T_i and p vector
    sims = {rp: {'pooled': np.zeros(B, dtype=int), 'percontest': np.zeros(B, dtype=int)} for rp in rankpairs}
    contest_units = []  # (Ts array, p array)
    for (contest, gubun), rs in groups.items():
        if gubun != gubun_filter:
            continue
        Ts = np.array([sum(r['votes']) for r in rs])
        agg = np.sum([r['votes'] for r in rs], axis=0).astype(float)
        if agg.sum() == 0:
            continue
        p = agg / agg.sum()
        contest_units.append((Ts, p))
    for b in range(B):
        pooled_vals = {rp: [] for rp in rankpairs}
        percontest = {rp: 0 for rp in rankpairs}
        for Ts, p in contest_units:
            # simulate each unit's vote vector
            for rp in rankpairs:
                vals = []
                # vectorized multinomial per unit
                for T in Ts:
                    if T <= 0:
                        continue
                    draw = rng.multinomial(T, p)
                    sv = np.sort(draw)[::-1]
                    if len(sv) > max(rp):
                        vals.append(tuple(int(sv[r]) for r in rp))
                pp, _ = pair_count(vals)
                percontest[rp] += pp
                pooled_vals[rp] += vals
        for rp in rankpairs:
            pp, _ = pair_count(pooled_vals[rp])
            sims[rp]['pooled'][b] = pp
            sims[rp]['percontest'][b] = percontest[rp]
    return sims

if __name__ == '__main__':
    rankpairs = [(0, 1), (1, 2), (2, 3)]
    for gubun in ['관내사전투표', '선거일투표']:
        print('\n' + '=' * 60)
        print(f'[{gubun}]')
        obs = analyze_observed(gubun, rankpairs)
        for rp in rankpairs:
            o = obs[rp]
            print(f'  순위쌍{tuple(r+1 for r in rp)}: 단위수={o["n_units"]}, '
                  f'동일쌍(시도/선거구내합)={o["per_contest_pairs"]}, '
                  f'전국풀링={o["pooled_pairs"]}(그룹{o["pooled_groups"]})')
        fv = full_vector_collisions(gubun)
        print(f'  전체 득표벡터 완전일치 쌍(contest내): {fv}')
