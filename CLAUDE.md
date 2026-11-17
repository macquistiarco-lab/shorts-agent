# Shorts agent - working notes

Python pipeline that turns a script into a finished YouTube Short (see README.md).
Channel: faceless English finance/business true stories told like a thriller
("He lost $20 billion in 48 hours"). Owner speaks Italian: reply in short Italian.

## Daily routine ("crea lo Short del giorno")

1. Setup (fresh machine): `pip install -q -r requirements.txt`. The voice model downloads by
   itself on the first run. Cloudflare images work through the proxy, no key needed.
2. Pick ONE new topic not already in `topics.md`: a real, well-documented money/business
   collapse, scam, heist, bubble or comeback with a shocking number. Prefer stories you know
   well; facts must be solid.
3. Write `examples/<slug>.json` yourself, following the schema and rules in `writer.py`
   (SCHEMA and SYSTEM): 10-14 lines, 110-140 words, numbers as words, 6-8 image prompts,
   no real faces, sfx cues, hook_text, highlight_words. `examples/barings.json` is the model.
   No ANTHROPIC_API_KEY is needed: you are the writer.
4. Render: `python agent.py --script examples/<slug>.json`.
5. Check it: extract 4-5 frames with ffmpeg and look at them (captions readable, images fit,
   no garbled text in images). If an image is bad, delete `output/<slug>/img/N.jpg`, change
   its prompt in `output/<slug>/script.json` and run `python agent.py --resume output/<slug>`.
6. Send `output/<slug>/short_<slug>.mp4` and `short_<slug>_upload.txt` to the user with
   SendUserFile (status proactive).
7. Append a line to `topics.md` (date, slug, title), commit `topics.md` and
   `examples/<slug>.json` on `main` and push. Never commit `output/` or `models/`.
8. Final message, 3-4 lines in Italian: title, length, any fact you are less than sure of.
