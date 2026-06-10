# -*- coding: utf-8 -*-
"""
과거 선거 개표단위별 결과 크롤러 (일반화 버전)
사용: python crawl_hist.py <electionId> <outfile.json> <mode: gov|asm>
  gov = 시도지사(electionCode=3),  asm = 국회의원(electionCode=2)
"""
import requests, re, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

EID = sys.argv[1]
OUT = sys.argv[2]
MODE = sys.argv[3]
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
            return s.get(SB + url, params=p, timeout=20).json().get('jsonResult', {}).get('body', [])
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
            'requestURI': '/electioninfo/%s/vc/vccp08.jsp' % EID, 'statementId': stmt,
            'electionCode': ec, 'cityCode': city, 'sggCityCode': sgg,
            'townCode': town, 'sggTownCode': sggtown, 'townCodeFromSgg': townfromsgg}
    for _ in range(3):
        try:
            r = s.post(REPORT, data=data, timeout=60); r.encoding = 'utf-8'
            return r.text
        except Exception:
            time.sleep(2)
    return ''

def parse(html):
    tabs = re.findall(r'<table.*?</table>', html, re.S)
    if not tabs:
        return None, []
    trs = [cells(x) for x in re.findall(r'<tr[^>]*>(.*?)</tr>', max(tabs, key=len), re.S)]
    trs = [c for c in trs if c]
    if len(trs) < 2:
        return None, []
    hdr = trs[1]
    cands = hdr[:-1] if hdr and hdr[-1] == '계' else hdr
    n = len(cands)
    rows = []
    for c in trs[2:]:
        if len(c) == 1 and '없습니다' in c[0]:
            return cands, []
        if len(c) < 4 + n:
            continue
        votes = [num(v) for v in c[4:4 + n]]
        if any(v is None for v in votes):
            continue
        rows.append({'emd': c[0], 'gubun': c[1], 'votes': votes})
    return cands, rows

records = []
def add(ec, contest, sido, gusigun, cands, rows):
    for r in rows:
        if r['gubun'] in ('관내사전투표', '선거일투표'):
            records.append({'ec': ec, 'contest': contest, 'sido': sido, 'gusigun': gusigun,
                            'emd': r['emd'], 'gubun': r['gubun'], 'cands': cands, 'votes': r['votes']})

def crawl_governor(ec='3'):
    # ec=3 시도지사, ec=1 대통령선거 (둘 다 cityCode->townCode 드릴, 시도/전국 단일 후보군)
    cities = [c for c in body('selectbox_cityCodeBySgJson.json', electionId=EID, electionCode=ec)
              if str(c['CODE']) not in ('0', '-1')]
    label = '대통령선거' if ec == '1' else '시도지사'
    print(f'[{label}] {len(cities)} 시도', flush=True)
    for c in cities:
        city = str(c['CODE']); sido = c['NAME']
        towns = [t for t in body('selectbox_townCodeJson.json', electionId=EID, cityCode=city)
                 if str(t['CODE']) not in ('0', '-1')]
        for t in towns:
            cands, rows = parse(post_report(ec, city, town=str(t['CODE'])))
            if cands:
                # 대선은 전국 단일 contest로 묶음
                contest = '제21대 대통령선거' if ec == '1' else sido
                add(ec, contest, sido, t['NAME'], cands, rows)
            time.sleep(0.12)
        print(f'  {sido} done ({len(records)})', flush=True)

def crawl_assembly():
    cities = [c for c in body('selectbox_cityCodeBySgJson.json', electionId=EID, electionCode='2')
              if str(c['CODE']) not in ('0', '-1')]
    print(f'[국회의원] {len(cities)} 시도', flush=True)
    for c in cities:
        city = str(c['CODE']); sido = c['NAME']
        sggs = [x for x in body('selectbox_getSggCityCodeJson.json', electionId=EID, electionCode='2', cityCode=city)
                if str(x['CODE']) not in ('0', '-1')]
        for sg in sggs:
            sgg = str(sg['CODE']); contest = sido + ' ' + sg['NAME']
            guls = [g for g in body('selectbox_townCodeFromSggJson.json', electionId=EID, electionCode='2',
                                    cityCode=city, sggCityCode=sgg) if str(g['CODE']) not in ('0', '-1')]
            for g in guls:
                cands, rows = parse(post_report('2', city, sgg=sgg, sggtown='0', townfromsgg=str(g['CODE'])))
                if not rows:
                    cands, rows = parse(post_report('2', city, sgg=sgg, sggtown='0',
                                                    townfromsgg=str(g['CODE']), stmt='VCCP08_#00_S'))
                if cands:
                    add('2', contest, sido, g['NAME'], cands, rows)
                time.sleep(0.12)
        print(f'  {sido} done ({len(records)})', flush=True)

warm()
if MODE == 'gov':
    crawl_governor('3')
elif MODE == 'pres':
    crawl_governor('1')
else:
    crawl_assembly()
json.dump(records, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('TOTAL', len(records), '->', OUT)
