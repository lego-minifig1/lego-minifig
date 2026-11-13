import os, io, time, subprocess, urllib.request, urllib.error
from PIL import Image

T0 = time.time()
LST = ".github/mimg/marvel.txt"
SRC = ".github/mimg/src.txt"
FAIL = ".github/mimg/fail.txt"


def save():
    subprocess.run("git add -A thumb .github/mimg && (git diff --cached --quiet || (git -c user.name=lego-minifig1 -c user.email=329362638+lego-minifig1@users.noreply.github.com commit -q -m 'Update files' && git push -q origin HEAD:marvel-img))", shell=True)


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
    return r.read()


def is_image(b):
    return b[:4] == b"\x89PNG" or b[:3] == b"\xff\xd8\xff" or b[:4] == b"GIF8" or (b[:4] == b"RIFF" and b[8:12] == b"WEBP")


src = dict(l.split(" ", 1) for l in open(SRC).read().splitlines()) if os.path.exists(SRC) else {}
fails = []
made = 0
streak = 0
for line in open(LST):
    p = line.split()
    if len(p) < 2:
        continue
    out, urls = p[0], p[1:]
    if os.path.exists(out):
        continue
    if time.time() - T0 > 320 * 60:
        break
    ok = False
    for u in urls:
        for attempt in range(3):
            try:
                b = get(u)
                if not is_image(b):
                    break
                im = Image.open(io.BytesIO(b)).convert("RGBA")
                im.thumbnail((1200, 1200), Image.LANCZOS)
                bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                bg.alpha_composite(im)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                bg.convert("RGB").save(out, "WEBP", quality=90, method=6)
                src[out] = "%s %dx%d" % (u, im.size[0], im.size[1])
                ok = True
                streak = 0
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 503, 403):
                    streak += 1
                    time.sleep(15 * (attempt + 1))
                    continue
                break
            except Exception:
                time.sleep(3)
                continue
        time.sleep(0.3)
        if ok:
            break
    if ok:
        made += 1
        if made % 300 == 0:
            open(SRC, "w").write("\n".join("%s %s" % kv for kv in sorted(src.items())) + "\n")
            save()
            print("made", made, "elapsed", int(time.time() - T0), flush=True)
    else:
        fails.append(out)
    if streak >= 20:
        print("blocked? resting 10 min", flush=True)
        time.sleep(600)
        streak = 0
open(SRC, "w").write("\n".join("%s %s" % kv for kv in sorted(src.items())) + "\n")
open(FAIL, "w").write("\n".join(fails) + "\n")
print("done made", made, "fail", len(fails), flush=True)
save()
