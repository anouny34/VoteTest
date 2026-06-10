#!/usr/bin/env bash
# =============================================================
#  동일 득표쌍 통계 검증 — 분석 재현 스크립트 (Mac / Linux / Git-bash)
#  저장소에 포함된 data/ 의 공식 원자료로 분석·그래프·검증을 한 번에 실행합니다.
#  (네트워크 불필요 — 데이터 재수집은 맨 아래 주석 참고)
#
#  사용법:  bash run_all.sh
# =============================================================
set -e
cd "$(dirname "$0")"

echo "==================================================="
echo " 0) 의존성 설치 확인"
echo "==================================================="
python -c "import requests,pandas,numpy,matplotlib,openpyxl" 2>/dev/null \
  || { echo '의존성 설치: pip install -r requirements.txt'; pip install -r requirements.txt; }

echo "==================================================="
echo " 1) 데이터 파싱 (과거 대선 엑셀 -> JSON)"
echo "==================================================="
python parse_hist_pres.py

echo "==================================================="
echo " 2) 2026 지선 분석"
echo "==================================================="
python analyze.py          # 관측 동일쌍
python closed_form.py      # 간이 경우의 수(생일 공식)
python montecarlo.py       # 귀무모형 몬테카를로 (수십 초~1분)
python per_contest.py      # 선거구(시도) 내 동일쌍
python cluster.py          # 한 곳에 몰릴 확률

echo "==================================================="
echo " 3) 선거 간 비교 (2025 대선 / 과거 대선) — 시뮬레이션, 수 분 소요"
echo "==================================================="
python compare_mc.py       # 2026 vs 2025
python hist_mc2.py         # 과거 대선 전국풀링

echo "==================================================="
echo " 4) 그래프 생성 -> figures/"
echo "==================================================="
python make_plots.py
python plot_cross.py
python plot_hist.py
python tw_plot.py          # data/tw_result.json 사용 (대만 zip 불필요)

echo "==================================================="
echo " 5) 수치 검증 (보고서 값 = 데이터 재계산값)"
echo "==================================================="
python verify.py

echo
echo "✅ 완료. 그래프는 figures/, 검증 결과는 위 출력을 확인하세요."

# -------------------------------------------------------------
# (선택) 데이터 재수집 — 네트워크/대용량 파일 필요, 기본 실행에서 제외
#   python crawler.py                                  # 2026 지선 크롤링 -> data/data_raw.json
#   python crawl_hist.py 0020250603 data/hist_2025_pres.json pres   # 2025 대선
#   # 대만: data.gov.tw/dataset/13119 의 votedata.zip 을 tw_votedata.zip 으로 저장 후
#   python tw_analyze.py                               # -> data/tw_result.json
# -------------------------------------------------------------
