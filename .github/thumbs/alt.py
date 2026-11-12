import os, io, re, time, glob, subprocess, urllib.request, urllib.error
from PIL import Image

T0 = time.time()
LIMIT = 320 * 60


def save():
    subprocess.run("git add thumb .github/thumbs && (git diff --cached --quiet || (git -c user.name=lego-minifig1 -c user.email=329362638+lego-minifig1@users.noreply.github.com commit -q -m 'Update files' && (git pull -q --rebase origin thumb-work || true) && git push -q origin HEAD:thumb-work))", shell=True)


def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
    return r.read()


def is_image(b):
    return b[:4] == b"\x89PNG" or b[:3] == b"\xff\xd8\xff" or b[:4] == b"GIF8" or (b[:4] == b"RIFF" and b[8:12] == b"WEBP")


def alts(key, urls):
    out = [u for u in urls[1:] if "bricklink.com" not in u]
    m = re.match(r"https://img\.bricklink\.com/ItemImage/(MN|SN)/(?:\d+/)?(.+)\.png$", urls[0])
    if m:
        t, code = m.groups()
        if t == "SN":
            out += ["https://cdn.rebrickable.com/media/sets/%s.jpg" % code.lower(),
                    "https://images.brickset.com/sets/images/%s.jpg" % code]
        else:
            out += ["https://images.brickset.com/minifigs/large/%s.jpg" % code]
            m2 = re.match(r"([a-z]+)0(\d{3}[a-z]?)$", code)
            if m2:
                out.append("https://images.brickset.com/minifigs/large/%s%s.jpg" % m2.groups())
    seen = []
    for u in out:
        if u not in seen:
            seen.append(u)
    return seen


# 브릭링크가 막혀 있을 때만: 브릭링크 사진 대신 리브릭커블·브릭셋의 같은 품목 사진으로 채움 (나중에 브릭링크 사진으로 바꿀 수 있게 <book>.alt 에 기록)
try:
    bl_down = not is_image(get("https://img.bricklink.com/ItemImage/MN/0/njo001.png"))
except Exception:
    bl_down = True
print("bricklink down:", bl_down, flush=True)

made = 0
stop = False
if bl_down:
    order = ["retired", "museum", "city", "toon", "original", "disney", "space", "oldlego", "castle", "adventure", "pirates",
             "architecture", "ring", "sw", "ninjago", "minifig", "harry", "dc", "jurassic", "alba", "parts"]
    lists = {os.path.basename(p)[3:-4]: p for p in glob.glob(".github/thumbs/[0-9]*.txt")}
    for book in order:
        if book not in lists or stop:
            continue
        af = ".github/thumbs/%s.alt" % book
        done = dict(l.split("\t", 1) for l in open(af).read().splitlines() if "\t" in l) if os.path.exists(af) else {}
        nf = ".github/thumbs/%s.noalt" % book
        noalt = set(open(nf).read().split()) if os.path.exists(nf) else set()
        os.makedirs("thumb/%s" % book, exist_ok=True)
        n0 = made
        for line in open(lists[book]):
            p = line.split()
            if len(p) < 2 or "img.bricklink.com" not in p[1]:
                continue
            key = p[0]
            out = "thumb/%s/%s.webp" % (book, key)
            if os.path.exists(out) or key in noalt:
                continue
            if time.time() - T0 > LIMIT:
                stop = True
                break
            ok = False
            for u in alts(key, p[1:]):
                try:
                    b = get(u)
                    if not is_image(b):
                        continue
                    im = Image.open(io.BytesIO(b)).convert("RGBA")
                    im.thumbnail((640, 640), Image.LANCZOS)  # 브릭링크 세트 사진 크기(대부분 640px)에 맞춤
                    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
                    bg.alpha_composite(im)
                    bg.convert("RGB").save(out, "WEBP", quality=85, method=6)
                    done[key] = u
                    ok = True
                    break
                except urllib.error.HTTPError as e:
                    if e.code in (429, 503):
                        time.sleep(30)
                except Exception:
                    pass
                time.sleep(0.2)
            if ok:
                made += 1
                if made % 200 == 0:
                    open(af, "w").write("\n".join("%s\t%s" % kv for kv in done.items()))
                    open(nf, "w").write("\n".join(sorted(noalt)))
                    save()
                    print(book, "made", made, "elapsed", int(time.time() - T0), flush=True)
            else:
                noalt.add(key)
            time.sleep(0.3)
        open(af, "w").write("\n".join("%s\t%s" % kv for kv in done.items()))
        open(nf, "w").write("\n".join(sorted(noalt)))
        save()
        print(book, "alt made", made - n0, "no alt", len(noalt), flush=True)

open(".github/thumbs/_status.txt", "w").write("%s alt made=%d stop=%s bl_down=%s\n" % (time.ctime(), made, stop, bl_down))
save()
