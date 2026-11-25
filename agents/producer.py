import asyncio, json, os, re, sys, textwrap, time, urllib.request, urllib.parse
import edge_tts
from mutagen.mp3 import MP3
from PIL import Image, ImageDraw, ImageFont

UA = {"User-Agent": "ShortsStudio/0.1 (https://github.com/mansurimasudahmed-rgb/Shorts-studio-; personal project) python-urllib"}
API = "https://commons.wikimedia.org/w/api.php"
VOICES = [os.environ.get("VOICE", "").strip(), "en-US-GuyNeural", "en-US-AriaNeural"]

script = json.load(open("output/script.json"))
topic = json.load(open("output/topic.json"))
os.makedirs("output/images", exist_ok=True)


async def speak(voice):
    await edge_tts.Communicate(script["script"], voice).save("output/voice.mp3")


ok = False
for v in VOICES:
    if not v:
        continue
    try:
        asyncio.run(speak(v))
        print("Voice used:", v)
        ok = True
        break
    except Exception as e:
        print("Voice failed:", v, e)
if not ok:
    print("No voice worked.")
    sys.exit(1)

duration = MP3("output/voice.mp3").info.length
print(f"Voiceover length: {duration:.1f}s")
if duration > 58:
    print("WARNING: over 58 seconds, the Writer should trim the script")

scenes = script["scenes"]
words = [max(1, len(s["line"].split())) for s in scenes]
total = sum(words)
used = set()


def clean(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def license_ok(name):
    n = name.lower()
    tokens = re.split(r"[^a-z0-9]+", n)
    if "nc" in tokens or "nd" in tokens:
        return False
    return "public domain" in n or "cc0" in n or n.startswith("pd") or n.startswith("cc by")


def find(query):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": query + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 20,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280,
    }
    time.sleep(1)
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    data = json.load(urllib.request.urlopen(req, timeout=30))
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    for p in pages:
        info = (p.get("imageinfo") or [None])[0]
        if not info or info.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if info.get("width", 0) < 800 or p["pageid"] in used:
            continue
        meta = info.get("extmetadata", {})
        lic = meta.get("LicenseShortName", {}).get("value", "")
        if not license_ok(lic):
            continue
        used.add(p["pageid"])
        artist = clean(meta.get("Artist", {}).get("value", "")) or "Unknown"
        name = p["title"].replace("File:", "")
        return {"url": info.get("thumburl") or info["url"],
                "credit": f"{name} by {artist[:60]} ({lic}) via Wikimedia Commons"}
    return None


def make_card(path, text):
    img = Image.new("RGB", (1080, 1920), (20, 18, 16))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=64)
    except TypeError:
        font = ImageFont.load_default()
    d.multiline_text((540, 960), textwrap.fill(text[:140], 22), font=font,
                     fill=(235, 225, 200), anchor="mm", align="center", spacing=14)
    img.save(path, "JPEG")


manifest, credits = [], []
for i, s in enumerate(scenes, 1):
    visual = s["visual"]
    queries = [visual, " ".join(visual.split()[:2]), topic.get("title", "mystery")]
    path = f"output/images/scene_{i:02d}.jpg"
    got = False
    for q in queries:
        try:
            p = find(q)
            if p:
                req = urllib.request.Request(p["url"], headers=UA)
                open(path, "wb").write(urllib.request.urlopen(req, timeout=60).read())
                credits.append(p["credit"])
                print(f"Scene {i}: '{q}' -> {p['credit'][:70]}")
                got = True
                break
        except Exception as e:
            print(f"Scene {i}: '{q}' failed: {e}")
    if not got:
        make_card(path, s["line"])
        print(f"Scene {i}: no usable image, made a text card")
    manifest.append({"image": path, "seconds": round(duration * words[i - 1] / total, 2), "line": s["line"]})

with open("output/manifest.json", "w") as f:
    json.dump({"title": script["title"], "audio": "output/voice.mp3", "duration": round(duration, 2),
               "scenes": manifest, "image_credits": credits}, f, indent=2)
print("Producer done:", len(manifest), "scenes,", f"{duration:.1f}s,", len(credits), "credited images")
