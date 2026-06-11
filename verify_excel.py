# -*- coding: utf-8 -*-
"""동일득표쌍_전체.xlsx 재검증: 내부 정합성 + 원자료 교차검증"""
import json, sys, zipfile, csv, io
from collections import defaultdict
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')
xl = pd.ExcelFile('동일득표쌍_전체.xlsx')
data_sheets = [s for s in xl.sheet_names if s != '요약']

def rank12(votes, cands):
    idx = sorted(range(len(votes)), key=lambda i: -votes[i])
    return cands[idx[0]], votes[idx[0]], cands[idx[1]], votes[idx[1]]

print('===== 1) 내부 정합성 (모든 시트) =====')
bad = 0
for s in data_sheets:
    d = xl.parse(s)
    if '1위득표' not in d.columns:
        print(f'  [{s}] 데이터 없음(빈 시트) — skip'); continue
    keycol = ['선거', '쌍번호'] if '선거' in d.columns else ['쌍번호']
    for k, grp in d.groupby(keycol):
        v1 = grp['1위득표'].unique(); v2 = grp['2위득표'].unique()
        if len(v1) != 1 or len(v2) != 1:
            print(f'  [{s}] {k}: 쌍 내 득표 불일치!'); bad += 1
        if grp['투표소수'].iloc[0] != len(grp):
            print(f'  [{s}] {k}: 투표소수({grp["투표소수"].iloc[0]})≠행수({len(grp)})'); bad += 1
        if v1[0] < v2[0]:
            print(f'  [{s}] {k}: 1위<2위 ({v1[0]}<{v2[0]})'); bad += 1
    print(f'  [{s}] 그룹 {d.groupby(keycol).ngroups}개 점검 완료')
print(f'  → 내부 정합성 문제: {bad}건')

print('\n===== 2) 한국 선거 후보명·득표 전수 교차검증 =====')
recs = json.load(open('data/data_raw.json', encoding='utf-8'))
pres25 = json.load(open('data/hist_2025_pres.json', encoding='utf-8'))
def lookup(rs, gubun):
    m = defaultdict(list)
    for r in rs:
        if r['gubun'] == gubun: m[(r['gusigun'], r['emd'])].append(r)
    return m
checks = [('2026_시도지사_사전', lookup([r for r in recs if r['ec'] == '3'], '관내사전투표')),
          ('2025_대선_본투표', lookup(pres25, '선거일투표'))]
mism = 0
for sheet, lk in checks:
    if sheet not in xl.sheet_names: continue
    d = xl.parse(sheet)
    for _, row in d.iterrows():
        cands_recs = lk.get((row['시군구등'], row['투표소']), [])
        # 같은 (1위,2위) 득표를 가진 레코드 찾기
        hit = None
        for r in cands_recs:
            w, wv, rn, rv = rank12(r['votes'], r['cands'])
            if wv == row['1위득표'] and rv == row['2위득표']:
                hit = (w, wv, rn, rv); break
        if not hit:
            print(f'  ✗ 원자료 못찾음/불일치: {sheet} {row["시군구등"]} {row["투표소"]} ({row["1위득표"]},{row["2위득표"]})'); mism += 1
        elif hit[0] != row['1위후보'] or hit[2] != row['2위후보']:
            print(f'  ✗ 후보명 불일치: {row["투표소"]} 엑셀({row["1위후보"]}/{row["2위후보"]}) vs 원본({hit[0]}/{hit[2]})'); mism += 1
    print(f'  [{sheet}] {len(d)}행 교차검증 완료')
print(f'  → 후보명/득표 불일치: {mism}건')

print('\n===== 3) 과거대선·대만 표본 교차검증 =====')
# 과거대선: 18대 한 쌍 재확인 (xlsx 직접)
d = xl.parse('과거대선(17,18,19,20)') if '과거대선(17,18,19,20)' in xl.sheet_names else None
if d is not None:
    samp = d.iloc[0]
    print(f'  과거대선 표본행: {samp["선거"]} {samp["지역"]} {samp["시군구등"]} {samp["투표소"]} → 1위 {samp["1위후보"]} {samp["1위득표"]}, 2위 {samp["2위후보"]} {samp["2위득표"]}')
# 대만: elctks에서 표본 투개표소 직접 확인
tw = xl.parse('대만총통(2020, 2024)') if '대만총통(2020, 2024)' in xl.sheet_names else None
if tw is not None:
    z = zipfile.ZipFile('tw_votedata.zip')
    def dec(n):
        try: return n.encode('cp437').decode('big5')
        except: return n
    M = {dec(n): n for n in z.namelist()}
    rows24 = list(csv.reader(io.StringIO(z.read(M['votedata/votedata/voteData/2024總統立委/總統/elctks.csv']).decode('latin1'))))
    samp = tw[tw['선거'] == '대만총통_2024'].iloc[0]
    code = samp['투표소'].replace('투개표소코드 ', '').split('-')
    got = {r[6]: int(r[7]) for r in rows24 if tuple(r[0:6]) == tuple(code)}
    print(f'  대만 표본: {samp["투표소"]}')
    print(f'    엑셀: 1위 {samp["1위후보"]} {samp["1위득표"]}, 2위 {samp["2위후보"]} {samp["2위득표"]}')
    print(f'    elctks 원본 號次별 득표: {got}  (號1柯/2賴/3侯)')
