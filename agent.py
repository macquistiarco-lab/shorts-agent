#!/usr/bin/env python3
"""Shorts agent: topic -> finished YouTube Short (mp4 + upload text).

  python agent.py "The Archegos collapse"          # Claude writes the script
  python agent.py --script my_script.json          # use a ready script (no API key needed)
  python agent.py --resume output/archegos         # re-render after editing script.json / images
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import images  # noqa: E402
import montage  # noqa: E402
import sfx  # noqa: E402
import tts  # noqa: E402


def log(msg):
    print(f"[shorts] {msg}", flush=True)


def upload_text(s):
    tags = " ".join("#" + h.lstrip("#") for h in s["hashtags"])
    return (f"TITLE:\n{s['title']}\n\nDESCRIPTION:\n{s['description']}\n\n{tags}\n\n"
            + (f"FIRST COMMENT (pin it):\n{s['first_comment']}\n\n" if s.get("first_comment") else "")
            + "NOTE: YouTube Studio -> \"Altered or synthetic content\" = Yes (realistic AI images).\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", nargs="?")
    ap.add_argument("--script", help="ready script.json (same schema Claude produces)")
    ap.add_argument("--resume", help="existing output folder to re-render")
    ap.add_argument("--voice", default="am_michael")
    ap.add_argument("--out", default=os.path.join(HERE, "output"))
    a = ap.parse_args()

    if a.resume:
        d = os.path.abspath(a.resume)
        script = json.load(open(os.path.join(d, "script.json")))
    else:
        if a.script:
            script = json.load(open(a.script))
        elif a.topic:
            log(f"writing script with Claude: {a.topic}")
            from writer import write_script
            script = write_script(a.topic)
        else:
            ap.error("give a topic, --script or --resume")
        d = os.path.join(os.path.abspath(a.out), script["slug"])
        os.makedirs(d, exist_ok=True)
        json.dump(script, open(os.path.join(d, "script.json"), "w"), indent=1)

    log(f"{len(script['images'])} images ({images.MODEL})")
    images.generate_images([i["prompt"] for i in script["images"]], os.path.join(d, "img"))
    log("voiceover (Kokoro)")
    timing = tts.synth(script["lines"], d, voice=a.voice)
    log("sound effects")
    total = timing[-1]["start"] + timing[-1]["dur"] + 0.6
    sfx.build_track(timing, total, d)
    log("montage (ffmpeg)")
    name = f"short_{script['slug']}.mp4"
    montage.render(d, timing, script["hook_text"], script.get("highlight_words", []), name)
    open(os.path.join(d, f"short_{script['slug']}_upload.txt"), "w").write(upload_text(script))
    log(f"done: {os.path.join(d, name)} ({total:.1f}s)")


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")
    main()
