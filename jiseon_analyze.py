# -*- coding: utf-8 -*-
"""역대 지방선거 시·도지사 투표구별 1·2위 동일쌍 — 본투표(읍면동)·사전투표(읍면동).
입력: data/hist_xlsx/...제6/7/8회...개표결과...xlsx (개방포털, '시·도지사' 시트)
우연 기대 = 시·도별(=시도지사 선거구별) 평균 지지율 모형(model A). 출력: data/jiseon_result.json"""
import sys, json, glob, numpy as np
import pandas as pd
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(2022)

def num(x):
    s = str(x).replace(',', '').strip()
    try: return int(float(s))
    except: return None
def C2(n): return n * (n - 1) // 2
def pc(L): c = Counter(L); return sum(C2(v) for v in c.values() if v >= 2)
def t2(v): s = sorted(v, reverse=True); return (s[0], s[1])
NONPRE = ('합계', '소계', '사전', '거소', '선상', '재외', '부재자', '관외', '관내', '계')

def parse(fn, mode):
    """지선 시도지사: 읍면동 단위. 본투표='선거일투표'행(2010은 읍면동행), 사전='관내사전투표'행. 연도별 레이아웃 상이."""
    raw = pd.read_excel(fn, sheet_name='시·도지사', header=None)
    h = next(i for i in range(8) if str(raw.iloc[i, 0]).strip() in ('선거구명', '시도', '시도명', '선거종류'))
    c0 = str(raw.iloc[h, 0]).strip(); c3 = str(raw.iloc[h, 3]).strip()
    if c0 == '선거종류':                  # 7회(2018): 선거종류 열로 우측 이동
        sc, gc, vs, gub = 1, 5, 8, True
    elif c3 == '구분':                    # 6·8회: 구분 열 존재
        sc, gc, vs, gub = 0, 3, 6, True
    else:                                 # 5회(2010): 사전 없음 → 구분 열 없음, 읍면동 행=본투표
        sc, gc, vs, gub = 0, None, 5, False
    if mode == 'sa' and not gub: return {}   # 2010은 사전투표 자체가 없음
    gye = None
    for rr in (h, h + 1):
        for j in range(vs, raw.shape[1]):
            if str(raw.iloc[rr, j]).strip().endswith('계'): gye = j; break
        if gye: break
    EXCL = ('합계', '소계', '부재자투표', '거소투표', '거소', '선상', '재외', '부재자', '관외', '관내', '계', '국외부재자')
    target = '선거일투표' if mode == 'bon' else '관내사전투표'
    by = defaultdict(list); cs = None
    for _, row in raw.iloc[h + 1:].iterrows():
        if isinstance(row[sc], str) and row[sc].strip() not in ('', 'nan'): cs = row[sc].strip()
        if cs in (None, '전국', '합계'): continue
        if gub:
            if str(row[gc]).strip() != target: continue
        else:                              # 2010: 읍면동 행만(부재자·합계·'잘못 투입된 투표지' 등 제외)
            emd = str(row[2]).strip()
            if emd in EXCL or '잘못' in emd or '투입' in emd or emd in ('', 'nan') or num(row[3]) is None: continue
        v = [num(row[j]) or 0 for j in range(vs, gye)]
        by[cs].append(v)
    return by

def analyze(by, B=200):
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

YEARS = [('20100602', '제5회 지선(2010·사전前)'), ('20140604', '제6회 지선(2014)'),
         ('20180613', '제7회 지선(2018)'), ('20220601', '제8회 지선(2022)')]
out = {}
for tag, lab in YEARS:
    fn = next(iter(glob.glob(f'data/hist_xlsx/*{tag}*.xlsx')), None)
    if not fn:
        print(f'{lab}: 파일 없음'); continue
    out[lab] = {}
    for mode, nm in [('bon', '본투표(읍면동)'), ('sa', '사전(읍면동)')]:
        N, obs, e, lo, hi = analyze(parse(fn, mode))
        out[lab][mode] = {'N': N, 'obs': obs, 'exp': e, 'lo': lo, 'hi': hi}
        print(f'{lab} {nm}: {N:,}곳, 관측 {obs}, 기대 {e:.0f} ({lo:.0f}~{hi:.0f})')
json.dump(out, open('data/jiseon_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('saved data/jiseon_result.json')
