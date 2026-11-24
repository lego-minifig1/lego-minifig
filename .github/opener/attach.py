# 도감 파일(*.html)에 '바로 열기'가 빠져 있으면 다시 붙임
# 대문 통합 검색 결과를 누르면 도감에서 그 카드가 바로 열리게 하는 작은 스크립트.
# 도감을 새로 만들어 올리면 빠지므로, 올릴 때마다 자동으로 확인함.
import base64, hashlib, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
OP = open(os.path.join(HERE, "opener.js"), encoding="utf-8").read()
CFG = json.load(open(os.path.join(HERE, "cfg.json"), encoding="utf-8"))
MARK = "카드 여는 중"
done = []
for book, cfg in CFG.items():
    f = book + ".html"
    if not os.path.isfile(f):
        continue
    html = open(f, encoding="utf-8").read()
    js = OP.replace("window.__OPEN_CFG || {}", json.dumps(cfg, ensure_ascii=False))
    h = "'sha256-" + base64.b64encode(hashlib.sha256(js.encode("utf-8")).digest()).decode() + "'"
    if MARK in html:
        # 이미 붙어 있으면: 예전 판이면 새 판으로 바꿔 끼움(보안 설정의 해시도 같이 바꿈)
        mm = re.search(r'<script(?: id="hsaddon")?>(?=/\* 대문 통합 검색에서 넘어올 때)', html)
        if not mm:
            continue
        s = mm.end()
        e = html.index("</script>", s)
        old = html[s:e]
        if old == js:
            continue
        oh = "'sha256-" + base64.b64encode(hashlib.sha256(old.encode("utf-8")).digest()).decode() + "'"
        if oh not in html:
            print("건너뜀(예전 해시를 못 찾음):", f)
            continue
        html = html[:s] + js + html[e:]
        html = html.replace(oh, h, 1)
        open(f, "w", encoding="utf-8").write(html)
        done.append(f + "(새 판)")
        continue
    m = re.search(r'(<meta http-equiv="Content-Security-Policy" content="[^"]*?script-src )', html)
    if not m or "</body>" not in html:
        print("건너뜀(모양이 다름):", f)
        continue
    html = html[:m.end()] + h + " " + html[m.end():]
    i = html.rindex("</body>")
    html = html[:i] + "<script>" + js + "</script>\n" + html[i:]
    open(f, "w", encoding="utf-8").write(html)
    done.append(f)
print("바로 열기 붙임:", ", ".join(done) if done else "없음")

# 휴대폰 뒤로 가기를 누르면 도감에서 나가지 않고 상세 창만 닫히게 하는 작은 스크립트.
# 아래 도감은 도감 쪽에 그 처리가 없어서, 올릴 때마다 빠져 있으면 다시 붙임.
BACK = open(os.path.join(HERE, "back.js"), encoding="utf-8").read()
BACK_BOOKS = ["Harry", "dc", "jurassic", "ninjago", "adventure", "oldlego", "brickheadz", "toon", "pirates", "city"]
BACK_MARK = "dlgBack"
done = []
for book in BACK_BOOKS:
    f = book + ".html"
    if not os.path.isfile(f):
        continue
    html = open(f, encoding="utf-8").read()
    if BACK_MARK in html:
        continue
    h = "'sha256-" + base64.b64encode(hashlib.sha256(BACK.encode("utf-8")).digest()).decode() + "'"
    m = re.search(r'(<meta http-equiv="Content-Security-Policy" content="[^"]*?script-src )', html)
    if not m or "</body>" not in html:
        print("건너뜀(모양이 다름):", f)
        continue
    html = html[:m.end()] + h + " " + html[m.end():]
    i = html.rindex("</body>")
    html = html[:i] + "<script>" + BACK + "</script>\n" + html[i:]
    open(f, "w", encoding="utf-8").write(html)
    done.append(f)
print("뒤로 가기 붙임:", ", ".join(done) if done else "없음")

# 브라우저 탭 아이콘: 도감 파일에 아이콘 줄이 없으면 넣음
ICON = '<link rel="icon" href="favicon.png" type="image/png"><link rel="apple-touch-icon" href="apple-touch-icon.png">'
done = []
import glob
for f in sorted(glob.glob("*.html")):
    if f == "404.html":
        continue
    html = open(f, encoding="utf-8").read()
    if 'rel="icon"' in html:
        continue
    i = html.find("<head>")
    if i < 0 or i > 2000:
        print("건너뜀(모양이 다름):", f)
        continue
    html = html[:i + 6] + ICON + html[i + 6:]
    open(f, "w", encoding="utf-8").write(html)
    done.append(f)
print("탭 아이콘 넣음:", ", ".join(done) if done else "없음")
