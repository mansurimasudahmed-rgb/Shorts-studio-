import json, os
from llm import ask_json

prompt = """You are the Researcher for a faceless YouTube Shorts channel about
mysteries and history. Pick ONE lesser-known but well-documented topic that
fits a 55-second video. Avoid gore. Return JSON only with keys:
title, hook (one gripping opening line), facts (list of 5 short facts),
sources (list of reputable sources to verify them), uncertain (list of any
claims that are disputed)."""

topic = ask_json(prompt)
os.makedirs("output", exist_ok=True)
with open("output/topic.json", "w") as f:
    json.dump(topic, f, indent=2)
print("Researcher picked:", topic.get("title"))
