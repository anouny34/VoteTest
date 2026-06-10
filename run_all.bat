@echo off
REM ============================================================
REM  동일 득표쌍 통계 검증 - 분석 재현 스크립트 (Windows)
REM  저장소에 포함된 data\ 의 공식 원자료로 분석.그래프.검증을 한 번에 실행.
REM  (네트워크 불필요. 데이터 재수집은 파일 하단 주석 참고)
REM
REM  사용법:  더블클릭 또는  run_all.bat
REM ============================================================
chcp 65001 >nul
cd /d "%~dp0"

echo === 0) 의존성 확인 ===
python -c "import requests,pandas,numpy,matplotlib,openpyxl" 2>nul || pip install -r requirements.txt

echo === 1) 데이터 파싱 (과거 대선 엑셀 -^> JSON) ===
python parse_hist_pres.py || goto :err

echo === 2) 2026 지선 분석 ===
python analyze.py || goto :err
python closed_form.py || goto :err
python montecarlo.py || goto :err
python per_contest.py || goto :err
python cluster.py || goto :err

echo === 3) 선거 간 비교 (시뮬레이션, 수 분 소요) ===
python compare_mc.py || goto :err
python hist_mc2.py || goto :err

echo === 4) 그래프 생성 -^> figures\ ===
python make_plots.py || goto :err
python plot_cross.py || goto :err
python plot_hist.py || goto :err
python tw_plot.py || goto :err

echo === 5) 수치 검증 ===
python verify.py || goto :err

echo.
echo [완료] 그래프는 figures\, 검증 결과는 위 출력을 확인하세요.
goto :eof

:err
echo.
echo [오류] 중단되었습니다. 위 메시지를 확인하세요.
exit /b 1

REM ------------------------------------------------------------
REM (선택) 데이터 재수집 - 네트워크/대용량 파일 필요
REM   python crawler.py
REM   python crawl_hist.py 0020250603 data\hist_2025_pres.json pres
REM   python tw_analyze.py      (tw_votedata.zip 필요)
REM ------------------------------------------------------------
