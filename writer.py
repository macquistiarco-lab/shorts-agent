"""Step 1: Claude writes the Short (script, image prompts, SFX cues, upload text)."""
import json

import anthropic

MODEL = "claude-opus-5-5"
SFX = ["none", "whoosh", "impact", "riser", "tick"]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["slug", "title", "description", "hashtags", "hook_text",
                 "highlight_words", "first_comment", "images", "lines"],
    "properties": {
        "slug": {"type": "string", "description": "short snake_case file name"},
        "title": {"type": "string", "description": "YouTube title, max 60 chars, ends with #shorts"},
        "description": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "hook_text": {"type": "string", "description": "2 short ALL CAPS lines separated by \\n, shown on top in the first seconds"},
        "highlight_words": {"type": "array", "items": {"type": "string"},
                            "description": "UPPERCASE words/numbers to colour yellow in captions"},
        "first_comment": {"type": "string", "description": "comment the channel posts and pins, max 150 chars"},
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
business told like a thriller. Two kinds, alternate them:
- FALL: a fortune lost, a fraud, a crash ("He lost $20 billion in 48 hours").
- RISE: someone who made a huge amount fast, legally and documented ("He turned $1,000 into
  $100 million in 3 years"): a trade, a startup sale, a bet against the market, a viral product.

What the Shorts feed rewards: viewers choosing to watch instead of swiping in the first 1-2
seconds, watching to the end, and rewatching. Every rule below serves those three.

Rules:
- 30-40 seconds of narration (about 85-110 words), 9-12 lines, one sentence or two very short ones per line.
  Shorter and complete beats longer and dropped.
- Line 1 is the hook, spoken in under 2 seconds (max 12 words). Start on the payoff or the
  stakes, never on a date, a name or background. Use one of: an impossible number ("He made
  one billion dollars in a single day."), a contradiction ("The safest bank in Britain died in a
  weekend."), a direct challenge ("You've used his invention today. He got nothing."), or a
  cliffhanger ("One email cost this company forty billion dollars.").
- Line 2 opens a question the viewer needs answered (how? who? what went wrong?) and keep that
  question open until the last 2-3 lines. Put a small reveal or a twist every 2-3 lines.
  Short, concrete, present tense where it reads naturally; no filler ("Let's dive in", "Did you know").
- Write numbers as words when spoken ("twenty billion dollars") so the TTS reads them well.
- Second-to-last line: the payoff or a sharp final fact that makes line 1 hit again on a replay
  (the video loops), e.g. "...and it all started with one email." when line 1 was about one email.
- Last line: a short call to follow, max 8 words ("Follow for more fortunes made and lost.").
- Only well-established facts. If unsure of a detail, leave it out.
- title: max 50 chars before " #shorts", a curiosity gap with the key number, not the full answer
  ("He Made $1 Billion in One Day. Legally." / "One Email Erased $40 Billion").
- hook_text: 2 short ALL CAPS lines, max 6 words each, the stakes in one glance; it must not
  repeat line 1 word for word.
- Exactly 8 images. Each prompt: cinematic, photo-realistic, dramatic lighting, film grain, vertical
  composition, "no text, no logos, no signs". Image 0 is the strongest, most striking shot (it is
  on screen during the hook). Never depict a real person's face: use silhouettes, hands,
  backs, places and objects instead. Reuse images across lines; change image every 1-2 lines.
  RISE stories can be brighter (gold, warm light) than FALL stories.
- sfx: "impact" on line 1 and on 2-3 key reveals, "riser" on the line right before the climax,
  "tick" on a money figure, otherwise "none". Whooshes on image changes are added automatically,
  so use "whoosh" rarely.
- highlight_words: the key numbers and money words as they appear in the text, uppercase.
- first_comment: the comment the channel pins under the Short to start the discussion. A sharp
  either/or or "what would you do" question tied to this story, easy to answer in a few words,
  max 150 chars, at most one emoji, no links (e.g. "Would you have sold at one million, or held
  for the billion? 👇")."""


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
