# -*- coding: utf-8 -*-
"""이번 분석에 쓴 모든 선거의 1·2위 동일 득표쌍을 엑셀로 추출
출력: 동일득표쌍_전체.xlsx  (선거별 시트, 선거구/투표소/1·2위 후보명/득표수)"""
import json, sys, zipfile, csv, io
from collections import defaultdict
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

def top2(votes): sv = sorted(votes, reverse=True); return (sv[0], sv[1])

def rank12(votes, cands):
    """(1위후보,1위표,2위후보,2위표)"""
    idx = sorted(range(len(votes)), key=lambda i: -votes[i])
    return cands[idx[0]], votes[idx[0]], cands[idx[1]], votes[idx[1]]

def make_pairs(units):
    """units: [{'votes','cands','region','sub','station'}]; 같은 (1위,2위)값 ≥2 그룹"""
    g = defaultdict(list)
    for u in units:
        if len(u['votes']) >= 2:
            g[top2(u['votes'])].append(u)
    out = []
    pid = 0
    for k, us in sorted(g.items(), key=lambda x: -x[0][0]):
        if len(us) >= 2:
            pid += 1
            for u in us:
                w, wv, r, rv = rank12(u['votes'], u['cands'])
                out.append(dict(쌍번호=pid, **{'1위득표': k[0], '2위득표': k[1], '투표소수': len(us),
                            '지역': u['region'], '시군구등': u['sub'], '투표소': u['station'],
                            '1위후보': w, '2위후보': r}))
    return out

sheets = {}

# ---------- 1) 2026 지방선거 (관내사전투표) ----------
recs = json.load(open('data/data_raw.json', encoding='utf-8'))
def kor_units(rs):
    return [{'votes': r['votes'], 'cands': r['cands'], 'region': r['sido'],
             'sub': r['gusigun'], 'station': r['emd']} for r in rs]
# 시도지사 (광주·전남 통합)
gov = [r for r in recs if r['ec'] == '3' and r['gubun'] == '관내사전투표']
gov_units = kor_units(gov)
for u, r in zip(gov_units, gov):
    if r['sido'] in ('광주광역시', '전라남도'): u['region'] = '광주·전남(통합)'
sheets['2026_시도지사_사전'] = make_pairs(gov_units)
# 국회의원
asm = [r for r in recs if r['ec'] == '2' and r['gubun'] == '관내사전투표']
au = [{'votes': r['votes'], 'cands': r['cands'], 'region': r['contest'],
       'sub': r['gusigun'], 'station': r['emd']} for r in asm]
sheets['2026_국회의원_사전'] = make_pairs(au)

# ---------- 2) 2025 대선 ----------
pres25 = json.load(open('data/hist_2025_pres.json', encoding='utf-8'))
for gb, name in [('관내사전투표', '2025_대선_사전'), ('선거일투표', '2025_대선_본투표')]:
    rs = [r for r in pres25 if r['gubun'] == gb]
    sheets[name] = make_pairs(kor_units(rs))

# ---------- 3) 과거 대선 (xlsx 재파싱: 위치명 포함) ----------
def num(x):
    s = str(x).replace(',', '').strip()
    try: return int(float(s))
    except: return None
NONPRE = ('소계', '합계', '사전', '거소', '선상', '재외', '부재자', '관외', '관내')
PAST = [('제17대_이명박2007', 'pres_17_lee2007.xlsx'), ('제18대_박근혜2012', 'pres_18_park2012.xlsx'),
        ('제19대_문재인2017', 'pres_19_moon2017.xlsx'), ('제20대_윤석열2022', 'pres_20_yoon2022.xlsx')]
past_all = []
for label, fn in PAST:
    raw = pd.read_excel('data/hist_xlsx/' + fn, header=None)
    h = next(i for i in range(10) if str(raw.iloc[i, 0]).strip() in ('시도', '시도명'))
    looks = lambda x: isinstance(x, str) and ('\n' in x or '당' in x) and '후보자별' not in x
    nrow = h if looks(raw.iloc[h, 6]) else h + 1
    gye = next(j for j in range(6, raw.shape[1])
               for r in {h, nrow} if str(raw.iloc[r, j]).strip().endswith('계'))
    cand = [str(raw.iloc[nrow, j]).replace('\n', ' ').replace('_x000D_', '').strip() for j in range(6, gye)]
    units = []
    cur_sido = None
    for _, row in raw.iloc[nrow + 1:].iterrows():
        if isinstance(row[0], str) and row[0].strip() not in ('', 'nan'): cur_sido = row[0].strip()
        tg = row[3]
        if not (isinstance(tg, str) and tg.strip() not in ('', 'nan') and not any(k in tg for k in NONPRE)): continue
        if cur_sido in (None, '전국'): continue
        votes = [num(row[j]) for j in range(6, gye)]
        if any(v is None for v in votes) or len(votes) < 2: continue
        gu = row[1] if isinstance(row[1], str) else ''
        emd = row[2] if isinstance(row[2], str) else ''
        units.append({'votes': votes, 'cands': cand, 'region': cur_sido,
                      'sub': (gu + ' ' + emd).strip(), 'station': tg.strip()})
    for p in make_pairs(units):
        p2 = {'선거': label, **p}; past_all.append(p2)
sheets['과거대선'] = past_all

# ---------- 4) 대만 (號次→후보명, 위치는 코드) ----------
TWNAME = {'2024': {'1': '柯文哲(민중당)', '2': '賴淸德(민진당)', '3': '侯友宜(국민당)'},
          '2020': {'1': '宋楚瑜(친민당)', '2': '韓國瑜(국민당)', '3': '蔡英文(민진당)'}}
z = zipfile.ZipFile('tw_votedata.zip')
def dec(n):
    try: return n.encode('cp437').decode('big5')
    except: return n
M = {dec(n): n for n in z.namelist()}
tw_all = []
for yr, path in [('2024', 'votedata/votedata/voteData/2024總統立委/總統/elctks.csv'),
                 ('2020', 'votedata/votedata/voteData/2020總統立委/總統/elctks.csv')]:
    rows = list(csv.reader(io.StringIO(z.read(M[path]).decode('latin1'))))
    st = defaultdict(dict)
    for r in rows:
        if r[5] == '0000': continue
        st[tuple(r[0:6])][r[6]] = int(r[7])
    nm = TWNAME[yr]
    units = []
    for key, d in st.items():
        ho = sorted(d)  # 號次 순
        votes = [d[h] for h in ho]; cands = [nm.get(h, '號' + h) for h in ho]
        units.append({'votes': votes, 'cands': cands, 'region': '대만 전국',
                      'sub': '縣市코드 ' + key[0] + key[1], 'station': '투개표소코드 ' + '-'.join(key)})
    for p in make_pairs(units):
        tw_all.append({'선거': '대만총통_' + yr, **p})
sheets['대만총통'] = tw_all

# ---------- 요약 + 저장 ----------
summary = []
for name, rows in sheets.items():
    npairs = len(set((r.get('선거', name), r['쌍번호']) for r in rows))
    summary.append({'시트': name, '동일쌍_그룹수': npairs, '행수(투표소)': len(rows)})

with pd.ExcelWriter('동일득표쌍_전체.xlsx', engine='openpyxl') as xw:
    pd.DataFrame(summary).to_excel(xw, sheet_name='요약', index=False)
    for name, rows in sheets.items():
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['쌍번호'])
        df.to_excel(xw, sheet_name=name[:31], index=False)
        print(f'{name}: {len(rows)}행')
print('saved 동일득표쌍_전체.xlsx')
