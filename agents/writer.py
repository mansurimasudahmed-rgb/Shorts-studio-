import json, os
from llm import ask_json

topic = json.load(open("output/topic.json"))

prompt = f"""You are the Writer for a faceless YouTube Shorts channel about
mysteries and history. Using ONLY these researched facts, write a voiceover
script that takes about 50 seconds to read aloud (110 to 135 words). Open with
the hook, build tension, end with a question or twist. No gore. Do not invent
facts beyond the ones given; if something is disputed, say so briefly.

RESEARCH: {json.dumps(topic)}

Return JSON only with these keys:
title (max 60 characters),
script (the full voiceover text, plain sentences, no stage directions),
scenes (list of 6 to 8 objects, each with "line" = the part of the script
spoken in that scene and "visual" = 2 to 4 words to search for a stock image),
description (2 sentences for YouTube),
hashtags (list of 5)."""

result = ask_json(prompt)
words = len(result["script"].split())
if words > 150:
    print(f"Too long ({words} words), asking for a trim")
    result = ask_json(prompt + f"\n\nYour last script was {words} words. Rewrite it under 135 words.")
    words = len(result["script"].split())

with open("output/script.json", "w") as f:
    json.dump(result, f, indent=2)
print("Writer done:", result["title"], "|", words, "words |", len(result["scenes"]), "scenes")
