# -*- coding: utf-8 -*-
"""
제9회 전국동시지방선거(2026-06-03) 개표단위별 개표결과 크롤러
대상: 시도지사선거(electionCode=3), 국회의원선거(재보궐, electionCode=2)
출처: info.nec.go.kr  메뉴 VCCP08(개표단위별 개표결과)
저장: data/data_raw.json  (record per (contest, 읍면동, 구분))
"""
import requests, re, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

EID = '0020260603'
BASE = 'https://info.nec.go.kr'
SB = BASE + '/bizcommon/selectbox/'
REPORT = BASE + '/electioninfo/electionInfo_report.xhtml'

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Referer': BASE + '/'})

def warm():
    s.get(BASE + '/main/showDocument.xhtml',
          params={'electionId': EID, 'topMenuId': 'VC', 'secondMenuId': 'VCCP08'}, timeout=20)

def body(url, **p):
    for _ in range(3):
        try:
            r = s.get(SB + url, params=p, timeout=20)
            return r.json().get('jsonResult', {}).get('body', [])
        except Exception:
            time.sleep(1)
    return []

def clean(x):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x)).strip()

def cells(row):
    return [clean(c) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S)]

def num(x):
    x = x.replace(',', '').strip()
    if x in ('', '-'):
        return 0
    try:
        return int(x)
    except ValueError:
        return None

def post_report(ec, city, sgg='-1', town='-1', sggtown='-1', townfromsgg='-1', stmt='VCCP08_#00'):
    data = {'electionId': EID, 'topMenuId': 'VC', 'secondMenuId': 'VCCP08', 'menuId': 'VCCP08',
            'requestURI': '/electioninfo/0020260603/vc/vccp08.jsp', 'statementId': stmt,
            'electionCode': ec, 'cityCode': city, 'sggCityCode': sgg,
            'townCode': town, 'sggTownCode': sggtown, 'townCodeFromSgg': townfromsgg}
    for _ in range(3):
        try:
            r = s.post(REPORT, data=data, timeout=60)
            r.encoding = 'utf-8'
            return r.text
        except Exception:
            time.sleep(2)
    return ''

def parse(html):
    """returns (cand_names list, rows) ; rows = list of (emd, gubun, 선거인수, 투표수, votes[], 무효, 기권)"""
    tabs = re.findall(r'<table.*?</table>', html, re.S)
    if not tabs:
        return None, []
    tab = max(tabs, key=len)
    trs = [cells(x) for x in re.findall(r'<tr[^>]*>(.*?)</tr>', tab, re.S)]
    trs = [c for c in trs if c]
    if len(trs) < 2:
        return None, []
    # header row 2 = candidate names + '계'
    hdr = trs[1]
    if hdr and hdr[-1] == '계':
        cands = hdr[:-1]
    else:
        cands = hdr
    n = len(cands)
    rows = []
    for c in trs[2:]:
        if len(c) == 1 and '없습니다' in c[0]:
            return cands, []
        # data row: [emd, gubun, 선거인수, 투표수, *votes(n), 계, 무효, 기권]
        if len(c) < 4 + n:
            continue
        emd, gubun = c[0], c[1]
        seon = num(c[2]); tu = num(c[3])
        votes = [num(v) for v in c[4:4 + n]]
        if any(v is None for v in votes):
            continue
        invalid = num(c[4 + n + 1]) if len(c) > 4 + n + 1 else None
        rows.append({'emd': emd, 'gubun': gubun, 'seonin': seon, 'tu': tu,
                     'votes': votes, 'invalid': invalid})
    return cands, rows

records = []

def add_rows(ec, contest, sido, gusigun, cands, rows):
    for r in rows:
        if r['gubun'] not in ('관내사전투표', '선거일투표'):
            continue
        records.append({'ec': ec, 'contest': contest, 'sido': sido, 'gusigun': gusigun,
                        'emd': r['emd'], 'gubun': r['gubun'], 'cands': cands,
                        'votes': r['votes'], 'seonin': r['seonin'], 'tu': r['tu']})

# ---------- 시도지사 (electionCode=3) ----------
def crawl_governor():
    cities = body('selectbox_cityCodeBySgJson.json', electionId=EID, electionCode='3')
    cities = [c for c in cities if str(c['CODE']) not in ('0', '-1')]
    print(f'[시도지사] {len(cities)} 시도', flush=True)
    for c in cities:
        city = str(c['CODE']); sido = c['NAME']
        towns = body('selectbox_townCodeJson.json', electionId=EID, cityCode=city)
        towns = [t for t in towns if str(t['CODE']) not in ('0', '-1')]
        for t in towns:
            html = post_report('3', city, town=str(t['CODE']))
            cands, rows = parse(html)
            if cands:
                add_rows('3', sido, sido, t['NAME'], cands, rows)
            time.sleep(0.15)
        print(f'  {sido}: {len([r for r in records if r["sido"]==sido])} early/day rows so far', flush=True)

# ---------- 국회의원 (electionCode=2) ----------
def crawl_assembly():
    cities = body('selectbox_cityCodeBySgJson.json', electionId=EID, electionCode='2')
    cities = [c for c in cities if str(c['CODE']) not in ('0', '-1')]
    print(f'[국회의원] {len(cities)} 시도', flush=True)
    for c in cities:
        city = str(c['CODE']); sido = c['NAME']
        sggs = body('selectbox_getSggCityCodeJson.json', electionId=EID, electionCode='2', cityCode=city)
        sggs = [x for x in sggs if str(x['CODE']) not in ('0', '-1')]
        for sg in sggs:
            sgg = str(sg['CODE']); contest = sido + ' ' + sg['NAME']
            guls = body('selectbox_townCodeFromSggJson.json', electionId=EID, electionCode='2',
                        cityCode=city, sggCityCode=sgg)
            guls = [g for g in guls if str(g['CODE']) not in ('0', '-1')]
            stmt = 'VCCP08_#00_S' if sgg == '2530301' else 'VCCP08_#00'
            for g in guls:
                gcode = str(g['CODE'])
                st = stmt
                if sgg == '2530901' and gcode == '5303':
                    st = 'VCCP08_#00_S'
                html = post_report('2', city, sgg=sgg, sggtown='0', townfromsgg=gcode, stmt=st)
                cands, rows = parse(html)
                if not rows:  # fallback try alternate statementId
                    html = post_report('2', city, sgg=sgg, sggtown='0', townfromsgg=gcode,
                                        stmt='VCCP08_#00_S' if st == 'VCCP08_#00' else 'VCCP08_#00')
                    cands, rows = parse(html)
                if cands:
                    add_rows('2', contest, sido, g['NAME'], cands, rows)
                time.sleep(0.15)
            print(f'  {contest}: {len([r for r in records if r["contest"]==contest])} rows', flush=True)

if __name__ == '__main__':
    warm()
    crawl_governor()
    crawl_assembly()
    json.dump(records, open('data/data_raw.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('TOTAL records:', len(records))
    print('saved data/data_raw.json')
