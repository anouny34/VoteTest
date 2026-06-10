# -*- coding: utf-8 -*-
"""제17~21대 대선 투표구별 개표결과 파싱 + 시도별 동일쌍/승자 분석
목적: '동일쌍 쏠림이 현 여당 강세지역에서만 나온다'는 반론 검증 —
      보수 승리 선거에선 보수 강세지역(TK)에 쏠리는지 확인."""
import pandas as pd, numpy as np, json, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')

FILES = [('제17대 (이명박·2007)', 'pres_17_lee2007.xlsx', '보수'),
         ('제18대 (박근혜·2012)', 'pres_18_park2012.xlsx', '보수'),
         ('제19대 (문재인·2017)', 'pres_19_moon2017.xlsx', '진보'),
         ('제20대 (윤석열·2022)', 'pres_20_yoon2022.xlsx', '보수')]

def num(x):
    s = str(x).replace(',', '').strip()
    if s in ('', 'nan', 'None'): return None
    try: return int(float(s))
    except: return None

NONPRECINCT = ('소계', '합계', '사전', '거소', '선상', '재외', '부재자', '관외', '관내')
def is_precinct(tg):
    # 선거일 실제 투표소만 (소계/합계/사전/거소/재외/부재자 제외)
    return isinstance(tg, str) and tg.strip() not in ('', 'nan') and not any(k in tg for k in NONPRECINCT)

def parse(fn):
    raw = pd.read_excel('data/hist_xlsx/' + fn, header=None)
    # 헤더행 h: col0가 '시도'/'시도명'
    h = next(i for i in range(min(10, len(raw))) if str(raw.iloc[i, 0]).strip() in ('시도', '시도명'))
    def looks_cand(x):
        return isinstance(x, str) and ('\n' in x or '당' in x) and '후보자별' not in x
    name_row = h if looks_cand(raw.iloc[h, 6]) else h + 1
    # 계 컬럼: col>=6에서 텍스트가 '계'로 끝나는 첫 컬럼
    gye = None
    for j in range(6, raw.shape[1]):
        for r in {h, name_row}:
            v = str(raw.iloc[r, j]).strip()
            if v == '계' or v.endswith('계'):
                gye = j; break
        if gye: break
    cand = [str(raw.iloc[name_row, j]).replace('\n', ' ').replace('_x000D_', '').strip()
            for j in range(6, gye)]
    units = []
    cur_sido = None
    for _, row in raw.iloc[name_row + 1:].iterrows():
        if isinstance(row[0], str) and row[0].strip() not in ('', 'nan'):
            cur_sido = row[0].strip()  # 시도는 병합셀이라 마지막 값 유지
        tg = row[3]
        if not is_precinct(tg): continue
        if cur_sido in (None, '전국'): continue
        votes = [num(row[j]) for j in range(6, gye)]
        if any(v is None for v in votes) or len(votes) < 2: continue
        units.append({'sido': cur_sido, 'votes': votes})
    return cand, units

def C2(n): return n*(n-1)//2
def pairs12(units):
    keys = [tuple(sorted(u['votes'], reverse=True)[:2]) for u in units]
    c = Counter(keys); return sum(C2(v) for v in c.values() if v >= 2)

allparsed = {}
for label, fn, camp in FILES:
    cand, units = parse(fn)
    allparsed[label] = {'camp': camp, 'cand': cand, 'units': units}
    # 전국 승자
    agg = np.zeros(len(cand))
    for u in units: agg += np.array(u['votes'])
    win = cand[int(agg.argmax())]
    # 시도별
    by = defaultdict(list)
    for u in units: by[u['sido']].append(u)
    print('='*70)
    print(f"{label}  [{camp} 승리]  전국 1위: {win}  | 투표소 {len(units):,}개, 후보 {len(cand)}명")
    rows = []
    for sido, us in by.items():
        a = np.zeros(len(cand))
        for u in us: a += np.array(u['votes'])
        sw = cand[int(a.argmax())]; share = a.max()/a.sum()*100
        rows.append((pairs12(us), sido, len(us), sw, share))
    rows.sort(reverse=True)
    print(f"  {'시도':<12}{'투표소':>6}{'동일쌍':>6}{'1위(득표율)':>22}")
    for p, sido, n, sw, sh in rows[:6]:
        print(f"  {sido:<12}{n:>6}{p:>6}   {sw} ({sh:.0f}%)")
    print(f"  전국 동일쌍 합계: {sum(r[0] for r in rows)}")

json.dump({k: {'camp': v['camp'], 'cand': v['cand'], 'units': v['units']}
           for k, v in allparsed.items()},
          open('data/hist_pres_parsed.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('\nsaved data/hist_pres_parsed.json')
