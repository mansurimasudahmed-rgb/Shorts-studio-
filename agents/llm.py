import json, os, sys, time, urllib.request, urllib.error

KEY = os.environ["GEMINI_API_KEY"].strip()
FIRST = os.environ.get("GEMINI_MODEL", "").strip()
BASE = "https://generativelanguage.googleapis.com/v1beta"
SKIP = ("image", "tts", "live", "audio", "embedding", "robotics", "computer", "thinking")


def list_models():
    names = []
    try:
        req = urllib.request.Request(f"{BASE}/models?pageSize=200", headers={"x-goog-api-key": KEY})
        for m in json.load(urllib.request.urlopen(req, timeout=30)).get("models", []):
            n = m["name"].split("/")[-1]
            ok = "generateContent" in m.get("supportedGenerationMethods", [])
            if ok and "flash" in n and not any(s in n for s in SKIP):
                names.append(n)
    except Exception as e:
        print("Could not list models:", e)
    order = ([FIRST] if FIRST else []) + names + ["gemini-flash-latest", "gemini-flash-lite-latest"]
    seen = []
    for n in order:
        if n not in seen:
            seen.append(n)
    return seen[:10]


def ask_json(prompt):
    models = list_models()
    print("Models to try:", models)
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }).encode()
    for round_no in range(1, 4):
        for model in models:
            req = urllib.request.Request(
                f"{BASE}/models/{model}:generateContent",
                data=body,
                headers={"Content-Type": "application/json", "x-goog-api-key": KEY},
            )
            try:
                data = json.load(urllib.request.urlopen(req, timeout=60))
                print("Worked with:", model)
                return json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
            except urllib.error.HTTPError as e:
                print(f"  {model}: {e.code}", e.read().decode()[:120].replace("\n", " "))
            except Exception as e:
                print(f"  {model}: {e}")
        print(f"Round {round_no} done, waiting 20s")
        time.sleep(20)
    print("All models busy or unavailable.")
    sys.exit(1)
