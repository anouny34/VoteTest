# -*- coding: utf-8 -*-
"""크롤링 충실성 검증: 선관위에서 표본 구를 실시간 재수집 → 저장 data_raw와 한 표까지 대조 + 완전성."""
import json, sys
import crawler  # 같은 폴더의 크롤러 재사용 (warm/body/post_report/parse)
sys.stdout.reconfigure(encoding='utf-8')

recs = json.load(open('data/data_raw.json', encoding='utf-8'))
crawler.warm()

# 시도 코드/이름
cities = {c['NAME']: str(c['CODE']) for c in
          crawler.body('selectbox_cityCodeBySgJson.json', electionId=crawler.EID, electionCode='3')
          if str(c['CODE']) not in ('0', '-1')}

# 동일쌍이 포함된 구 등 표본
SAMPLE = [('인천광역시', '연수구'), ('전라남도', '신안군'), ('경상북도', '의성군'),
          ('서울특별시', '종로구'), ('경기도', '성남시분당구'), ('전라남도', '장성군')]

total_cmp = 0; mismatch = 0; missing = 0
for sido, gu in SAMPLE:
    city = cities.get(sido)
    towns = {t['NAME']: str(t['CODE']) for t in
             crawler.body('selectbox_townCodeJson.json', electionId=crawler.EID, cityCode=city)}
    if gu not in towns:
        print(f'  [{sido} {gu}] 구 코드 없음 (이름 불일치?) — skip'); continue
    cands, rows = crawler.parse(crawler.post_report('3', city, town=towns[gu]))
    live = {(r['emd'], r['gubun']): r['votes'] for r in rows
            if r['gubun'] in ('관내사전투표', '선거일투표')}
    saved = {(r['emd'], r['gubun']): r['votes'] for r in recs
             if r['ec'] == '3' and r['sido'] == sido and r['gusigun'] == gu
             and r['gubun'] in ('관내사전투표', '선거일투표')}
    # 비교
    keys = set(live) | set(saved)
    nmis = 0
    for k in keys:
        total_cmp += 1
        if k not in saved or k not in live:
            missing += 1; nmis += 1
            print(f'    ✗ 한쪽에만 존재: {sido} {gu} {k}')
        elif live[k] != saved[k]:
            mismatch += 1; nmis += 1
            print(f'    ✗ 득표 불일치: {sido} {gu} {k}  실시간{live[k]} vs 저장{saved[k]}')
    print(f'  [{sido} {gu}] 읍면동×구분 {len(keys)}개 대조, 불일치 {nmis}개 (후보 {len(cands)}명)')

print(f'\n=== 표본 재크롤링 대조: 총 {total_cmp}개 중 불일치 {mismatch}, 누락 {missing} ===')

# 완전성: 시도별 관내사전 읍면동 수
print('\n=== 완전성: 시도별 사전투표소(읍면동) 수 (data_raw) ===')
from collections import Counter
c = Counter(r['sido'] for r in recs if r['ec'] == '3' and r['gubun'] == '관내사전투표')
print(f'  17개 시도 모두 존재: {len(c) == 17}  (시도 {len(c)}개)')
print('  합계 사전투표소:', sum(c.values()))
