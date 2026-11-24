import json, os, sys, time, urllib.request, urllib.error

key = os.environ["GEMINI_API_KEY"].strip()
first = os.environ.get("GEMINI_MODEL", "gemini-flash-latest").strip()
models = [first, "gemini-flash-lite-latest", "gemini-flash-latest"]

prompt = """You are the Researcher for a faceless YouTube Shorts channel about
mysteries and history. Pick ONE lesser-known but well-documented topic that
fits a 55-second video. Avoid gore. Return JSON only with keys:
title, hook (one gripping opening line), facts (list of 5 short facts),
sources (list of reputable sources to verify them), uncertain (list of any
claims that are disputed)."""

body = json.dumps({
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseMimeType": "application/json"},
}).encode()

topic = None
for model in models:
    for attempt in range(1, 4):
        print(f"Trying {model} (attempt {attempt})")
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": key},
        )
        try:
            data = json.load(urllib.request.urlopen(req, timeout=60))
            topic = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            print("  failed:", e.code, msg)
            if e.code in (429, 500, 503):
                time.sleep(15 * attempt)
                continue
            break  # 400/404: skip to the next model
        except Exception as e:
            print("  failed:", e)
            time.sleep(10)
    if topic:
        break

if not topic:
    print("Researcher gave up: all models busy or unavailable.")
    sys.exit(1)

os.makedirs("output", exist_ok=True)
with open("output/topic.json", "w") as f:
    json.dump(topic, f, indent=2)
print("Researcher picked:", topic.get("title"))
