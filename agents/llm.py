import json, os, sys, time, urllib.request, urllib.error

KEY = os.environ["GEMINI_API_KEY"].strip()
FIRST = os.environ.get("GEMINI_MODEL", "gemini-flash-latest").strip()
MODELS = [FIRST, "gemini-flash-lite-latest", "gemini-flash-latest"]


def ask_json(prompt):
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode()
    for model in MODELS:
        for attempt in range(1, 4):
            print(f"Trying {model} (attempt {attempt})")
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                data=body,
                headers={"Content-Type": "application/json", "x-goog-api-key": KEY},
            )
            try:
                data = json.load(urllib.request.urlopen(req, timeout=60))
                return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
            except urllib.error.HTTPError as e:
                print("  failed:", e.code, e.read().decode()[:300])
                if e.code in (429, 500, 503):
                    time.sleep(15 * attempt)
                    continue
                break
            except Exception as e:
                print("  failed:", e)
                time.sleep(10)
    print("All models busy or unavailable.")
    sys.exit(1)
