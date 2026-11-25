import json, os, shutil, subprocess, sys

FPS = 30
m = json.load(open("output/manifest.json"))
script = json.load(open("output/script.json"))
scenes = m["scenes"]
os.makedirs("output/clips", exist_ok=True)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:])
        sys.exit(1)


# 1. One zooming clip per scene
for i, s in enumerate(scenes, 1):
    frames = max(15, round(s["seconds"] * FPS))
    if i == len(scenes):
        frames += 15
    fc = (
        "[0:v]split[a][b];"
        "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:6[bg];"
        "[b]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,"
        f"zoompan=z='min(zoom+0.0006,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps={FPS},"
        "format=yuv420p[v]"
    )
    run(["ffmpeg", "-y", "-i", s["image"], "-filter_complex", fc, "-map", "[v]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", f"output/clips/clip_{i:02d}.mp4"])
    print(f"Clip {i}: {frames} frames")

with open("output/clips/list.txt", "w") as f:
    for i in range(1, len(scenes) + 1):
        f.write(f"file 'clip_{i:02d}.mp4'\n")


# 2. Captions (4 words at a time)
def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,DejaVu Sans,78,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,80,80,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
lines, t = [], 0.0
for s in scenes:
    words = s["line"].replace("{", "").replace("}", "").split()
    chunks = [" ".join(words[j:j + 4]) for j in range(0, len(words), 4)] or [""]
    per = s["seconds"] / len(chunks)
    for k, c in enumerate(chunks):
        lines.append(f"Dialogue: 0,{ts(t + k * per)},{ts(t + (k + 1) * per)},Cap,,0,0,0,,{c}")
    t += s["seconds"]
open("output/captions.ass", "w").write(head + "\n".join(lines) + "\n")

# 3. Join clips + voiceover + captions
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "output/clips/list.txt", "-i", m["audio"],
     "-vf", "subtitles=output/captions.ass", "-map", "0:v", "-map", "1:a",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "160k",
     "-shortest", "-movflags", "+faststart", "output/short.mp4"])
shutil.rmtree("output/clips")

# 4. Description file for YouTube
tags = " ".join(h if h.startswith("#") else "#" + h for h in script.get("hashtags", []))
with open("output/description.txt", "w") as f:
    f.write(f"TITLE:\n{script['title']}\n\nDESCRIPTION:\n{script.get('description', '')}\n\n{tags}\n\n")
    f.write("IMAGE CREDITS:\n" + "\n".join(m.get("image_credits", [])) + "\n")

print("Editor done: output/short.mp4,", round(os.path.getsize("output/short.mp4") / 1e6, 1), "MB")
