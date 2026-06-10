# -*- coding: utf-8 -*-
"""대만 총통선거(수기개표·사전투표 없음) 투개표소별 동일 득표쌍 분석
관측 vs 우연기대(MC, 縣市별 model A). 한국과 동일 현상인지 확인."""
import zipfile, sys, csv, io, json, numpy as np
from collections import defaultdict, Counter
sys.stdout.reconfigure(encoding='utf-8')
rng = np.random.default_rng(20260603)
z = zipfile.ZipFile('tw_votedata.zip')
def dec(n):
    try: return n.encode('cp437').decode('big5')
    except: return n
M = {dec(n): n for n in z.namelist()}

ELECS = {
    '2024 총통선거 (賴清德·민진당 승리)': 'votedata/votedata/voteData/2024總統立委/總統/elctks.csv',
    '2020 총통선거 (蔡英文·민진당 승리)': 'votedata/votedata/voteData/2020總統立委/總統/elctks.csv',
}
OUT = {}
def C2(n): return n*(n-1)//2
def pc(vals):
    c = Counter(vals); return sum(C2(v) for v in c.values() if v >= 2)

def load_stations(path):
    rows = list(csv.reader(io.StringIO(z.read(M[path]).decode('latin1'))))
    st = defaultdict(dict)   # lockey -> {호수: 표}
    for r in rows:
        if r[5] == '0000':   # 투개표소 단위만 (집계행 제외)
            continue
        key = tuple(r[0:6]); st[key][r[6]] = int(r[7])
    # 縣市 = (col0,col1)
    units = []
    for key, d in st.items():
        votes = [d[k] for k in sorted(d)]
        if len(votes) >= 2:
            units.append({'city': key[0] + key[1], 'votes': votes})
    return units

for label, path in ELECS.items():
    units = load_stations(path)
    N = len(units)
    top2 = [tuple(sorted(u['votes'], reverse=True)[:2]) for u in units]
    obs = pc(top2)
    fullvec = pc([tuple(u['votes']) for u in units])
    print('=' * 64)
    print(f'[{label}]')
    print(f'  투개표소 {N:,}개, 후보 {len(units[0]["votes"])}명, 비교쌍 C(N,2)={C2(N):,}')
    print(f'  1·2위 동일쌍(전국 풀링): {obs}')
    print(f'  후보 전원(3명) 득표 완전일치 쌍: {fullvec}')
    # MC: 縣市별 model A
    by = defaultdict(list)
    for u in units: by[u['city']].append(u['votes'])
    cu = []
    for c, vl in by.items():
        arr = np.array(vl, float); Ts = arr.sum(1).astype(int)
        p = arr.sum(0) / arr.sum(); cu.append((Ts, p))
    B = 500; sims = np.zeros(B, int)
    for b in range(B):
        pool = []
        for Ts, p in cu:
            for T in Ts:
                if T <= 0: continue
                sv = np.sort(rng.multinomial(T, p))[::-1]
                pool.append((int(sv[0]), int(sv[1])))
        sims[b] = pc(pool)
    pv = (np.sum(sims >= obs) + 1) / (B + 1)
    print(f'  → 우연 기대(MC, 縣市별): {sims.mean():.0f}쌍 (95% {np.percentile(sims,2.5):.0f}~{np.percentile(sims,97.5):.0f}), p={pv:.3f}')
    OUT[label] = dict(N=N, obs=int(obs), fullvec=int(fullvec),
                      avg=sum(sum(u['votes']) for u in units) / N,
                      exp=float(sims.mean()), lo=float(np.percentile(sims, 2.5)),
                      hi=float(np.percentile(sims, 97.5)), p=float(pv))

json.dump(OUT, open('data/tw_result.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('saved data/tw_result.json')
