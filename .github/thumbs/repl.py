import os, io, re, time, glob, subprocess, urllib.request
from PIL import Image
# 점검 기간에 대체 사이트(리브릭커블·브릭셋·아카이브)에서 받은 사진을 브릭링크 원본으로 다시 받아 바꿈
T0 = time.time()
def save():
    subprocess.run("git add thumb .github/thumbs && (git diff --cached --quiet || (git -c user.name=lego-minifig1 -c user.email=329362638+lego-minifig1@users.noreply.github.com commit -q -m 'Update files' && (git pull -q --rebase origin thumb-work || true) && git push -q origin HEAD:thumb-work))", shell=True)
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
def is_image(b):
    return b[:4] == b"\x89PNG" or b[:3] == b"\xff\xd8\xff" or b[:4] == b"GIF8" or (b[:4] == b"RIFF" and b[8:12] == b"WEBP")
lists = {os.path.basename(p)[3:-4]: p for p in glob.glob(".github/thumbs/[0-9]*.txt")}
made = 0
for book, lf in sorted(lists.items()):
    keys = set()
    for ext in ("alt", "arch"):
        f = ".github/thumbs/%s.%s" % (book, ext)
        if os.path.exists(f):
            keys |= {l.split("\t")[0] for l in open(f).read().splitlines() if l.strip()}
    rf = ".github/thumbs/%s.repl" % book
    done = set(open(rf).read().split()) if os.path.exists(rf) else set()
    keys -= done
    if not keys:
        continue
    urls = {}
    for line in open(lf):
        p = line.split()
        if len(p) >= 2 and "img.bricklink.com" in p[1]:
            urls[p[0]] = p[1]
    for key in sorted(keys):
        if key not in urls:
            continue
        if time.time() - T0 > 320 * 60:
            break
        try:
            b = get(urls[key])
            if not is_image(b):
                continue
            im = Image.open(io.BytesIO(b)).convert("RGBA")
            im.thumbnail((1200, 1200), Image.LANCZOS)
            bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im)
            bg.convert("RGB").save("thumb/%s/%s.webp" % (book, key), "WEBP", quality=90, method=6)
            done.add(key); made += 1
            if made % 300 == 0:
                open(rf, "w").write("\n".join(sorted(done))); save(); print(book, made, flush=True)
        except Exception:
            pass
        time.sleep(0.25)
    open(rf, "w").write("\n".join(sorted(done))); save(); print(book, "replaced", len(done), flush=True)
print("total", made)
