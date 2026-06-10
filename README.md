# 동일 득표쌍(Twin Votes) 부정선거 의혹 — 통계 검증

2026년 6·3 지방선거에서 "사전투표 1·2위 후보 득표수가 똑같은 투표소가 6쌍 있다"는 부정선거 의혹이 제기됐습니다. 이 저장소는 **선관위·대만 중앙선거위의 공식 공개 데이터**를 전수 수집·분석해, 그 "동일 득표쌍"이 조작의 증거인지 통계적으로 검증한 코드와 보고서입니다.

**결론(요약):** 동일 득표쌍은 실재하지만 그 수는 **우연으로 기대되는 수준**이며(생일의 역설), 본투표·다른 선거·진보/보수 텃밭·수기개표하는 대만 선거 어디서나 나타나는 **자연스러운 통계 현상**입니다. 자세한 내용은 `REPORT_FINAL.pdf` 참조.

## 핵심 결과

| 검증 | 결과 |
|---|---|
| 2026 사전투표 1·2위 동일쌍 | 관측 9쌍 ≈ 우연 기대 ~11쌍 (p=0.80) |
| 본투표(대조군) | 동일 현상 발생 |
| 2025 대선 / 과거 대선(이명박·박근혜·문재인·윤석열) | 모두 우연 기대 이하, 양 진영 텃밭 모두 |
| 대만(수기개표·사전투표 없음) | 동일쌍 수천 쌍(2024년 2,395쌍) — 더 많음 |

## 저장소 구조

```
├── REPORT_FINAL.md / .pdf   # 최종 통합 보고서 (먼저 보세요)
├── REPORT.md / .pdf         # 2026 지선 상세 분석 (본편)
├── REPORT2.md / .pdf        # 과거 대선 — 진영 검증
├── REPORT3.md / .pdf        # 대만 — 수기개표 검증
├── data/                    # 수집·가공 데이터 (JSON/CSV/XLSX)
├── figures/                 # 보고서 그래프 (PNG)
└── *.py                     # 분석 코드 (아래)
```

## 데이터 출처

| 데이터 | 출처 | 입수 |
|---|---|---|
| 2026 지선 · 2025 대선 | 선관위 선거통계시스템 [info.nec.go.kr](https://info.nec.go.kr/) | `crawler.py`, `crawl_hist.py` |
| 과거 대선(제17~20대) | 국가선거정보 개방포털 [data.nec.go.kr](http://data.nec.go.kr/) | `data/hist_xlsx/*.xlsx` (투표구별 개표결과) |
| 대만 총통선거(2020·2024) | 대만 중앙선거위 [data.gov.tw/dataset/13119](https://data.gov.tw/dataset/13119) | `votedata.zip`(아래) |

> **대만 데이터:** 용량(110MB)이 커 저장소에서 제외했습니다. 재현하려면 위 출처의 `votedata.zip`을 내려받아 저장소 루트에 `tw_votedata.zip`으로 두고 `tw_analyze.py`를 실행하세요.

## 코드

**수집**
- `crawler.py` — 2026 지선(시도지사·국회의원) 개표단위별 결과 크롤링 → `data/data_raw.json`
- `crawl_hist.py <electionId> <out.json> <gov|pres|asm>` — 대선/시도지사/국회의원 크롤링
- `parse_hist_pres.py` — 과거 대선 xlsx 파싱 → `data/hist_pres_parsed.json`

**분석 (2026 지선)**
- `analyze.py` — 동일쌍 전수 관측
- `closed_form.py` — 간이 경우의 수(생일 공식) 기대값
- `montecarlo.py` — 귀무모형 몬테카를로(모형 A/B)
- `per_contest.py` — 선거구(시도) 내 동일쌍
- `cluster.py` — "한 곳에 몰릴 확률" 검정
- `compare_mc.py` — 2026 vs 2025 비교 → `data/compare_mc_result.json`

**분석 (과거 대선·대만)**
- `hist_mc2.py` — 과거 대선 전국풀링 시뮬레이션 → `data/hist_mc2_result.json`
- `tw_analyze.py` — 대만 투개표소별 동일쌍 + 시뮬레이션 → `data/tw_result.json`

**그래프 · 검증 · 문서**
- `make_plots.py`, `plot_cross.py`, `plot_hist.py`, `tw_plot.py` — `figures/*.png` 생성
- `verify.py` — 보고서 수치를 데이터에서 재계산해 대조 (41개 체크)
- `build_pdf.py <report.md>` — 마크다운 → PDF (pandoc + Edge 필요)

## 실행 방법

### 한 번에 실행 (권장)

저장소에 포함된 데이터로 **분석 → 그래프 → 검증**을 한 번에 재현합니다 (네트워크 불필요).

```bash
pip install -r requirements.txt

bash run_all.sh        # Mac / Linux / Git-bash
run_all.bat            # Windows (더블클릭 또는 명령창)
```

실행하면 `figures/` 의 그래프가 다시 생성되고, 마지막에 `verify.py` 가 보고서 수치를 데이터에서 재계산해 일치를 확인합니다. (시뮬레이션 포함이라 수 분 소요)

### 개별 실행

```bash
python analyze.py          # 관측 동일쌍
python closed_form.py      # 간이 경우의 수(생일 공식)
python montecarlo.py       # 귀무모형 몬테카를로
python per_contest.py      # 선거구 내 동일쌍
python cluster.py          # 한 곳에 몰릴 확률
python compare_mc.py       # 2026 vs 2025
python hist_mc2.py         # 과거 대선 전국풀링
python make_plots.py; python plot_cross.py; python plot_hist.py; python tw_plot.py  # 그래프
python verify.py           # 전 수치 재계산 대조
```

### 데이터 재수집 (선택 — 네트워크/대용량 파일 필요)

```bash
python crawler.py                                            # 2026 지선 → data/data_raw.json
python crawl_hist.py 0020250603 data/hist_2025_pres.json pres  # 2025 대선
python parse_hist_pres.py                                    # data/hist_xlsx/*.xlsx → 파싱
python tw_analyze.py                                         # tw_votedata.zip 필요 → data/tw_result.json
```

## 재현성 / 데이터 신뢰성

- 분석에 쓴 원자료(`data/`)는 모두 공식 공개 데이터이며, 표본추출 없이 전수 사용했습니다.
- `verify.py`는 보고서의 수치를 데이터에서 다시 계산해 일치를 확인합니다.
- 파싱한 데이터로 재구성한 각 선거의 1위 득표율이 **실제 선거 결과와 일치**함을 확인했습니다(예: 제17대 이명박 48.7%).
- 시뮬레이션 난수 시드(`20260603`)를 고정해 결과가 재현됩니다.

## 라이선스

분석 코드는 MIT 라이선스로 자유롭게 사용할 수 있습니다. 원자료의 저작권은 각 선거관리기관에 있습니다.
