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
    if MARK in html:
        continue
    js = OP.replace("window.__OPEN_CFG || {}", json.dumps(cfg, ensure_ascii=False))
    h = "'sha256-" + base64.b64encode(hashlib.sha256(js.encode("utf-8")).digest()).decode() + "'"
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
