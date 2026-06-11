# -*- coding: utf-8 -*-
"""REPORT.md -> PDF (pandoc로 HTML 변환, 이미지 base64 내장, Edge 헤드리스로 PDF 출력)"""
import subprocess, base64, re, os, sys, shutil, tempfile, glob
sys.stdout.reconfigure(encoding='utf-8')

SRC = sys.argv[1] if len(sys.argv) > 1 else 'REPORT.md'
OUT_PDF = (sys.argv[2] if len(sys.argv) > 2
           else os.path.splitext(SRC)[0] + '.pdf')
WORK = os.getcwd()

# 1) pandoc: markdown -> HTML body fragment
body = subprocess.run(
    ['pandoc', SRC, '-f', 'gfm', '-t', 'html5'],
    capture_output=True, text=True, encoding='utf-8', cwd=WORK)
if body.returncode != 0:
    print('pandoc error:', body.stderr); sys.exit(1)
html_body = body.stdout

# 2) 이미지 <img src="figN.png"> -> base64 data URI
def embed(m):
    src = m.group(1)
    path = os.path.join(WORK, src)
    if os.path.exists(path):
        b = base64.b64encode(open(path, 'rb').read()).decode()
        return f'<img src="data:image/png;base64,{b}"'
    return m.group(0)
html_body = re.sub(r'<img src="([^"]+\.png)"', embed, html_body)

# 2-b) 특정 챕터는 앞 챕터에 이어지도록 페이지 분리 해제
if 'FINAL' in os.path.basename(SRC).upper():
    NO_BREAK_TITLES = ['8. 본 분석']  # 최종보고서: 8장만 7장에 이어붙임(2·3·7장은 새 페이지)
else:
    NO_BREAK_TITLES = ['4. 결과', '7. 본 분석의 한계']
for title in NO_BREAK_TITLES:
    html_body = re.sub(r'(<h2\b)([^>]*>\s*' + re.escape(title) + ')',
                       r'\1 style="page-break-before:avoid"\2', html_body, count=1)
# 소제목·문단을 새 페이지에서 시작: 4-6, 그리고 4-4의 ② 몬테카를로
html_body = re.sub(r'(<h3\b)([^>]*>\s*4-6\.)',
                   r'\1 style="page-break-before:always"\2', html_body, count=1)
html_body = re.sub(r'<p>(<strong>② 몬테카를로)',
                   r'<p style="page-break-before:always">\1', html_body, count=1)

# 3) HTML 템플릿 + CSS
CSS = """
@page { size: A4; margin: 17mm 16mm; }
* { box-sizing: border-box; }
body { font-family:'Malgun Gothic','맑은 고딕',sans-serif; font-size:10.5pt;
       line-height:1.65; color:#1a1a1a; }
h1 { font-size:19pt; border-bottom:3px solid #2c3e50; padding-bottom:8px; color:#2c3e50; }
h2 { font-size:15pt; color:#2c3e50; border-bottom:1px solid #d0d7de; padding-bottom:5px;
     margin-top:0; padding-top:2px; page-break-before:always; page-break-after:avoid; }
h2:first-of-type { page-break-before:avoid; }  /* 1번 챕터는 제목과 같은 페이지 */
h3 { font-size:12.5pt; color:#34495e; margin-top:18px; page-break-after:avoid; }
h4 { font-size:11pt; color:#555; margin-top:12px; page-break-after:avoid; }
table { border-collapse:collapse; width:100%; margin:12px 0; font-size:9.5pt;
        page-break-inside:avoid; }
th,td { border:1px solid #c8ced3; padding:6px 9px; text-align:left; vertical-align:top; }
th { background:#eef2f6; font-weight:700; }
tr:nth-child(even) td { background:#fafbfc; }
blockquote { border-left:4px solid #4C72B0; background:#f4f7fb; margin:12px 0;
             padding:9px 15px; color:#333; }
img { max-width:92%; display:block; margin:14px auto; page-break-inside:avoid;
      border:1px solid #e1e4e8; }
code { background:#f0f1f3; padding:1px 5px; border-radius:3px; font-size:9.5pt; }
hr { display:none; }  /* 챕터가 페이지로 분리되므로 구분선 숨김 */
strong { color:#111; }
ul,ol { padding-left:22px; }
li { margin:3px 0; }
"""
html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<style>{CSS}</style></head><body>{html_body}</body></html>"""

# 4) 임시 ASCII 경로에서 Edge로 PDF 렌더 (경로 한글/공백 회피)
import time
tmp = tempfile.mkdtemp(prefix='necpdf_')
html_path = os.path.join(tmp, 'report.html')
pdf_path = os.path.join(tmp, 'report.pdf')
prof = os.path.join(tmp, 'prof')
open(html_path, 'w', encoding='utf-8').write(html)

edge = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
url = 'file:///' + html_path.replace('\\', '/')
cmd = [edge, '--headless=new', '--disable-gpu', '--user-data-dir=' + prof,
       '--no-pdf-header-footer', f'--print-to-pdf={pdf_path}', url]
subprocess.run(cmd, capture_output=True, text=True, timeout=120)
for _ in range(60):  # Edge가 자식 프로세스에서 PDF를 쓰므로 폴링 대기
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        break
    time.sleep(0.5)

if os.path.exists(pdf_path):
    dest = os.path.join(WORK, OUT_PDF)
    try:
        shutil.copy(pdf_path, dest)
        print('OK ->', OUT_PDF, '(', os.path.getsize(pdf_path), 'bytes )')
    except PermissionError:
        alt = os.path.join(WORK, 'REPORT_updated.pdf')
        shutil.copy(pdf_path, alt)
        print('!! REPORT.pdf 가 열려있어 덮어쓰기 실패. ->', os.path.basename(alt), '로 저장함.')
        print('   (뷰어를 닫은 뒤 REPORT_updated.pdf를 REPORT.pdf로 바꾸거나 다시 실행하세요)')
else:
    print('PDF 생성 실패'); print(r.stdout[-500:]); print(r.stderr[-500:])
shutil.rmtree(tmp, ignore_errors=True)
