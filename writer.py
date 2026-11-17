"""Step 1: Claude writes the Short (script, image prompts, SFX cues, upload text)."""
import json

import anthropic

MODEL = "claude-opus-5-5"
SFX = ["none", "whoosh", "impact", "riser", "tick"]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["slug", "title", "description", "hashtags", "hook_text",
                 "highlight_words", "images", "lines"],
    "properties": {
        "slug": {"type": "string", "description": "short snake_case file name"},
        "title": {"type": "string", "description": "YouTube title, max 60 chars, ends with #shorts"},
        "description": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "hook_text": {"type": "string", "description": "2 short ALL CAPS lines separated by \\n, shown on top in the first seconds"},
        "highlight_words": {"type": "array", "items": {"type": "string"},
                            "description": "UPPERCASE words/numbers to colour yellow in captions"},
        "images": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["prompt"],
            "properties": {"prompt": {"type": "string"}}}},
        "lines": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["text", "img", "sfx"],
            "properties": {
                "text": {"type": "string"},
                "img": {"type": "integer", "description": "index into images"},
                "sfx": {"type": "string", "enum": SFX}}}},
    },
}

SYSTEM = """You write faceless YouTube Shorts in English: true stories about money, finance and
business told like a thriller (e.g. "He lost $20 billion in 48 hours").

Rules:
- 40-55 seconds of narration (about 110-140 words), 10-14 lines, one sentence or two very short ones per line.
- Line 1 is the hook: a shocking concrete fact with a number. Line 2 twists it. No intro, no "in this video".
- Write numbers as words when spoken ("twenty billion dollars") so the TTS reads them well.
- Last line: a short call to follow ("Follow for more stories of money that vanished overnight.").
- Only well-established facts. If unsure of a detail, leave it out.
- Exactly 5 images. Each prompt: cinematic, photo-realistic, dark moody lighting, film grain, vertical
  composition, "no text, no logos". Never depict a real person's face: use silhouettes, hands,
  backs, places and objects instead. Reuse the 5 images across lines; change image every 1-3 lines.
- sfx: "impact" on 3-4 key reveals, "riser" on the line right before the climax, "tick" on a
  money figure, otherwise "none". Whooshes on image changes are added automatically, so use
  "whoosh" rarely.
- highlight_words: the key numbers and money words as they appear in the text, uppercase."""


def write_script(topic: str) -> dict:
    client = anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        thinking={"type": "adaptive"},
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        system=SYSTEM,
        messages=[{"role": "user", "content": f"Topic: {topic}"}],
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude declined the topic: {resp.stop_details}")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("Script output was truncated (max_tokens)")
    text = next(b.text for b in resp.content if b.type == "text")
    script = json.loads(text)
    n = len(script["images"])
    for line in script["lines"]:
        line["img"] = min(max(line["img"], 0), n - 1)
    return script
