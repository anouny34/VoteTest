# -*- coding: utf-8 -*-
"""역대 총선(국회의원) 투표구별 1·2위 동일쌍 분석 — 본투표(투표구)·사전투표(읍면동).
입력: data/hist_xlsx/asm_20_2016.xlsx · asm_21_2020.xlsx · asm_22_2024.xlsx (개방포털)
우연 기대 = 선거구별 평균 지지율 모형(model A). 출력: data/asm_result.json"""
import sys, json, numpy as np
import pandas as pd
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(2024)

def num(x):
    s = str(x).replace(',', '').strip()
    try: return int(float(s))
    except: return None
def C2(n): return n * (n - 1) // 2
def pc(L): c = Counter(L); return sum(C2(v) for v in c.values() if v >= 2)
def t2(v): s = sorted(v, reverse=True); return (s[0], s[1])

def parse(fn, mode):
    """mode='bon' → 선거일 투표구 / 'sa' → 관내사전(읍면동). returns {선거구: [votes...]}"""
    raw = pd.read_excel('data/hist_xlsx/' + fn, header=None)
    h = next(i for i in range(12) if str(raw.iloc[i, 0]).strip() in ('시도', '시도명'))
    looks = lambda x: isinstance(x, str) and ('\n' in x or '당' in x) and '후보자별' not in x
    nrow = h if looks(raw.iloc[h, 6]) else h + 1
    gye = next(j for j in range(6, raw.shape[1])
               for rr in {h, nrow} if str(raw.iloc[rr, j]).strip().endswith('계'))
    NONPRE = ('소계', '합계', '사전', '거소', '선상', '재외', '부재자', '관외', '관내')
    by = defaultdict(list); cs = None; csgg = None
    for _, row in raw.iloc[nrow + 1:].iterrows():
        if isinstance(row[0], str) and row[0].strip() not in ('', 'nan'): cs = row[0].strip()
        if isinstance(row[1], str) and row[1].strip() not in ('', 'nan', '합계'): csgg = row[1].strip()
        tg = row[3]
        if not isinstance(tg, str): continue
        if mode == 'sa':
            if '관내사전' not in tg: continue
        else:
            if tg.strip() in ('', 'nan') or any(k in tg for k in NONPRE): continue
        if cs in (None, '전국'): continue
        v = [num(row[j]) for j in range(6, gye)]
        if any(x is None for x in v): continue
        by[(cs, csgg)].append(v)
    return by

def analyze(by, B=300):
    allv = [v for vl in by.values() for v in vl]
    obs = pc([t2(v) for v in allv])
    cu = []
    for vl in by.values():
        a = np.array(vl, float)
        if a.sum() > 0: cu.append((a.sum(1).astype(int), a.sum(0) / a.sum()))
    sims = np.zeros(B, int)
    for b in range(B):
        pool = []
        for Ts, p in cu:
            for T in Ts:
                if T > 0:
                    sv = np.sort(rng.multinomial(T, p))[::-1]; pool.append((int(sv[0]), int(sv[1])))
        sims[b] = pc(pool)
    return len(allv), obs, float(sims.mean()), float(np.percentile(sims, 2.5)), float(np.percentile(sims, 97.5))

FILES = [('asm_22_2024.xlsx', '제22대총선(2024)'), ('asm_21_2020.xlsx', '제21대총선(2020)'),
         ('asm_20_2016.xlsx', '제20대총선(2016)'), ('asm_19_2012.xlsx', '제19대총선(2012·사전前)')]
out = {}
for fn, lab in FILES:
    out[lab] = {}
    for mode, name in [('bon', '본투표(투표구)'), ('sa', '사전(읍면동)')]:
        N, obs, e, lo, hi = analyze(parse(fn, mode))
        out[lab][mode] = {'N': N, 'obs': obs, 'exp': e, 'lo': lo, 'hi': hi}
        print(f'{lab} {name}: {N:,}곳, 관측 {obs}, 기대 {e:.0f} ({lo:.0f}~{hi:.0f})')
json.dump(out, open('data/asm_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('saved data/asm_result.json')
