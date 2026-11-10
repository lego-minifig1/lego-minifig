import os, io, re, time, glob, json, subprocess, urllib.request, urllib.error
from PIL import Image

SIZE = {"architecture": (800, 800)}
DEFAULT = (600, 600)
T0 = time.time()


def save():
    add = "git add thumb .github/thumbs" if os.path.isdir("thumb") and os.listdir("thumb") else "git add .github/thumbs"
    subprocess.run(add + " && (git diff --cached --quiet || (git -c user.name=lego-minifig1 -c user.email=329362638+lego-minifig1@users.noreply.github.com commit -q -m 'Update files' && (git pull -q --rebase origin thumb-work || true) && git push -q origin HEAD:thumb-work))", shell=True)


def host(u):
    m = re.match(r"https?://([^/?#]+)", u)
    return m.group(1).lower() if m else ""


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
    return r.read()


def is_image(b):
    return b[:4] == b"\x89PNG" or b[:3] == b"\xff\xd8\xff" or b[:4] == b"GIF8" or (b[:4] == b"RIFF" and b[8:12] == b"WEBP")


lists = sorted(glob.glob(".github/thumbs/[0-9]*.txt"))
# 사이트별 상태: 각 목록의 첫 주소로 시험
down = {}
status = {}
for lst in lists:
    for line in open(lst):
        parts = line.split()
        if len(parts) < 2:
            continue
        h = host(parts[1])
        if h in status:
            continue
        try:
            b = get(parts[1])
            status[h] = "ok" if is_image(b) else "not image: " + b[:40].hex()
        except urllib.error.HTTPError as e:
            status[h] = "HTTP %d" % e.code if e.code != 404 else "ok"
        except Exception as e:
            status[h] = repr(e)[:100]
        down[h] = status[h] != "ok"
os.makedirs(".github/thumbs", exist_ok=True)
json.dump(status, open(".github/thumbs/_probe.json", "w"), indent=1)
print(status)
save()

made = 0
streak = {}
skipped_down = 0
stop = False
for lst in lists:
    book = os.path.basename(lst)[:-4].split("-", 1)[-1]
    size = SIZE.get(book, DEFAULT)
    os.makedirs(f"thumb/{book}", exist_ok=True)
    fails, waits = [], []
    for line in open(lst):
        parts = line.split()
        if len(parts) < 2:
            continue
        key, urls = parts[0], parts[1:]
        out = f"thumb/{book}/{key}.webp"
        if os.path.exists(out):
            continue
        if time.time() - T0 > 310 * 60:
            stop = True
            break
        h = host(urls[0])
        if down.get(h):
            # 첫 주소(원본)의 사이트가 막혀 있으면 건너뛰고 나중에 다시 받음 (대체 주소의 다른 사진으로 채우지 않음)
            waits.append(key); skipped_down += 1
            continue
        ok = False
        for u in urls:
            if host(u) != h and not ok and urls.index(u) > 0 and down.get(host(u)):
                continue
            try:
                b = get(u)
                if not is_image(b):
                    raise ValueError("not image")
                im = Image.open(io.BytesIO(b)).convert("RGBA")
                im.thumbnail(size, Image.LANCZOS)
                bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                bg.alpha_composite(im)
                bg.convert("RGB").save(out, "WEBP", quality=90, method=6)
                ok = True
                break
            except urllib.error.HTTPError as e:
                if e.code in (403, 429, 503):
                    streak[h] = streak.get(h, 0) + 1
                if e.code != 404:
                    break
            except Exception:
                streak[h] = streak.get(h, 0) + 1
                break
        time.sleep(0.35)
        if ok:
            streak[h] = 0
            made += 1
            if made % 150 == 0:
                save()
            continue
        fails.append(key)
        if streak.get(h, 0) >= 25:
            print("host blocking:", h, "- resting 10 min")
            save()
            time.sleep(600)
            streak[h] = 0
            try:
                if not is_image(get(urls[0])):
                    down[h] = True
            except Exception:
                down[h] = True
    open(f".github/thumbs/{book}.fail", "w").write("\n".join(fails))
    open(f".github/thumbs/{book}.wait", "w").write("\n".join(waits))
    print(book, "made so far", made, "fails", len(fails), "waiting (host down)", len(waits))
    if stop:
        break
open(".github/thumbs/_status.txt", "w").write(
    "%s made=%d waiting=%d stop=%s down=%s\n" % (time.ctime(), made, skipped_down, stop, [h for h in down if down[h]]))
save()
