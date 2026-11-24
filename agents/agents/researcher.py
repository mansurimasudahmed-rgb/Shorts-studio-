import json, os, sys, urllib.request

key = os.environ["GEMINI_API_KEY"]
model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

prompt = """You are the Researcher for a faceless YouTube Shorts channel about
mysteries and history. Pick ONE lesser-known but well-documented topic that
fits a 55-second video. Avoid gore. Return JSON only with keys:
title, hook (one gripping opening line), facts (list of 5 short facts),
sources (list of reputable sources to verify them), uncertain (list of any
claims that are disputed)."""

body = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseMimeType": "application/json"},
}
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json", "x-goog-api-key": key},
)
try:
    data = json.load(urllib.request.urlopen(req, timeout=60))
    topic = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
except Exception as e:
    print("Researcher failed:", e)
    sys.exit(1)

os.makedirs("output", exist_ok=True)
with open("output/topic.json", "w") as f:
    json.dump(topic, f, indent=2)
print("Researcher picked:", topic.get("title"))
