import os, io, re, time, glob, subprocess, urllib.request, urllib.error
from PIL import Image

T0 = time.time()
ORDER = ["ring", "dc", "harry", "jurassic", "retired", "sw", "ninjago", "minifig", "space", "adventure",
         "oldlego", "castle", "toon", "original", "pirates", "alba", "disney", "architecture", "city", "museum", "parts"]


def save():
    subprocess.run("git add thumb .github/thumbs && (git diff --cached --quiet || (git -c user.name=lego-minifig1 -c user.email=329362638+lego-minifig1@users.noreply.github.com commit -q -m 'Update files' && (git pull -q --rebase origin thumb-work || true) && git push -q origin HEAD:thumb-work))", shell=True)


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 (lego-minifig thumbnails)"}), timeout=60)
    return r.read()


def is_image(b):
    return b[:4] == b"\x89PNG" or b[:3] == b"\xff\xd8\xff" or b[:4] == b"GIF8" or (b[:4] == b"RIFF" and b[8:12] == b"WEBP")


lists = {os.path.basename(p)[:-4].split("-", 1)[-1]: p for p in glob.glob(".github/thumbs/[0-9]*.txt")}
made = 0
stop = False
for book in ORDER:
    if book not in lists or stop:
        continue
    urlmap = {}
    for line in open(lists[book]):
        p = line.split()
        if len(p) >= 2:
            urlmap[p[0]] = p[1]
    wf = f".github/thumbs/{book}.wait"
    waits = [k for k in open(wf).read().split() if k] if os.path.exists(wf) else []
    af = f".github/thumbs/{book}.arch"
    arch = set(open(af).read().split()) if os.path.exists(af) else set()
    nf = f".github/thumbs/{book}.noarch"
    noarch = set(open(nf).read().split()) if os.path.exists(nf) else set()
    os.makedirs(f"thumb/{book}", exist_ok=True)
    left = []
    rest429 = 0
    for key in waits:
        out = f"thumb/{book}/{key}.webp"
        if os.path.exists(out) or key in noarch or key not in urlmap:
            if not os.path.exists(out):
                left.append(key)
            continue
        if time.time() - T0 > 320 * 60:
            stop = True
            left.append(key)
            continue
        u = "https://web.archive.org/web/2026id_/" + urlmap[key]
        ok = False
        for attempt in range(3):
            try:
                b = get(u)
                if not is_image(b):
                    raise ValueError("not image")
                im = Image.open(io.BytesIO(b)).convert("RGBA")
                im.thumbnail((1200, 1200), Image.LANCZOS)
                bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                bg.alpha_composite(im)
                bg.convert("RGB").save(out, "WEBP", quality=90, method=6)
                ok = True
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    rest429 += 1
                    time.sleep(30 * (attempt + 1))
                    continue
                break
            except Exception:
                time.sleep(5)
                continue
        time.sleep(1.0)
        if ok:
            arch.add(key)
            made += 1
            if made % 100 == 0:
                open(af, "w").write("\n".join(sorted(arch)))
                save()
        else:
            noarch.add(key)
            left.append(key)
    open(af, "w").write("\n".join(sorted(arch)))
    open(nf, "w").write("\n".join(sorted(noarch)))
    print(book, "archive made", len(arch), "still waiting", len(left), "rest429", rest429, flush=True)
    save()
open(".github/thumbs/_status.txt", "w").write("%s archive made=%d stop=%s\n" % (time.ctime(), made, stop))
save()
