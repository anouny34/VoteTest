# -*- coding: utf-8 -*-
"""19대·20대 대선 관내사전투표 동일쌍을 동일득표쌍_전체.xlsx 에 시트로 덧붙임 (기존 시트 보존)"""
import sys
from collections import defaultdict
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

def num(x):
    s = str(x).replace(',', '').strip()
    try: return int(float(s))
    except: return None
def top2(v): sv = sorted(v, reverse=True); return (sv[0], sv[1])
def rank12(v, c):
    i = sorted(range(len(v)), key=lambda k: -v[k]); return c[i[0]], v[i[0]], c[i[1]], v[i[1]]

def parse_sajeon(fn):
    raw = pd.read_excel('data/hist_xlsx/' + fn, header=None)
    h = next(i for i in range(10) if str(raw.iloc[i, 0]).strip() in ('시도', '시도명'))
    looks = lambda x: isinstance(x, str) and ('\n' in x or '당' in x) and '후보자별' not in x
    nrow = h if looks(raw.iloc[h, 6]) else h + 1
    gye = next(j for j in range(6, raw.shape[1])
               for r in {h, nrow} if str(raw.iloc[r, j]).strip().endswith('계'))
    cand = [str(raw.iloc[nrow, j]).replace('\n', ' ').replace('_x000D_', '').strip() for j in range(6, gye)]
    units = []; cs = cg = ce = None
    for _, row in raw.iloc[nrow + 1:].iterrows():
        c0, c1, c2, tg = row[0], row[1], row[2], row[3]
        if isinstance(c0, str) and c0.strip() not in ('', 'nan'): cs = c0.strip()
        if isinstance(c1, str) and c1.strip() not in ('', 'nan', '합계'): cg = c1.strip()
        if isinstance(c2, str) and c2.strip() not in ('', 'nan', '합계'): ce = c2.strip()
        if isinstance(tg, str) and '관내사전' in tg:
            votes = [num(row[j]) for j in range(6, gye)]
            if any(v is None for v in votes) or len(votes) < 2 or cs in (None, '전국'): continue
            units.append({'votes': votes, 'cands': cand, 'region': cs, 'sub': cg, 'station': ce})
    return units

def make_pairs(units):
    g = defaultdict(list)
    for u in units:
        if len(u['votes']) >= 2: g[top2(u['votes'])].append(u)
    out = []; pid = 0
    for k, us in sorted(g.items(), key=lambda x: -x[0][0]):
        if len(us) >= 2:
            pid += 1
            for u in us:
                w, wv, r, rv = rank12(u['votes'], u['cands'])
                out.append({'쌍번호': pid, '1위득표': k[0], '2위득표': k[1], '투표소수': len(us),
                            '지역': u['region'], '시군구등': u['sub'], '투표소': u['station'],
                            '1위후보': w, '2위후보': r})
    return out

new = {'19대_대선_사전투표': make_pairs(parse_sajeon('pres_19_moon2017.xlsx')),
       '20대_대선_사전투표': make_pairs(parse_sajeon('pres_20_yoon2022.xlsx'))}

with pd.ExcelWriter('동일득표쌍_전체.xlsx', mode='a', engine='openpyxl', if_sheet_exists='replace') as xw:
    for name, rows in new.items():
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['쌍번호'])
        df.to_excel(xw, sheet_name=name, index=False)
        ng = df['쌍번호'].nunique() if '쌍번호' in df and len(df) else 0
        print(f'{name}: 그룹 {ng}, 행 {len(df)}')
print('추가 완료')
