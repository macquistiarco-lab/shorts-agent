# shorts-agent graph

Map of the shorts-agent environment for quick lookup. Edges are one per line:
`A -> B : relation`, so `grep -n "<name>" GRAPH.md` finds every link of a node.
For code-level questions (callers, impact, definitions) the Graphify connector also
indexes this repo (`macquistiarco-lab/shorts-agent`): query_graph, graphify_callers, graphify_impact.
Keep this file in sync when you add a module, env var, slot or scheduled run.

## Nodes

### Runs (scheduled tasks on claude.ai, fresh session each, push notification on finish)
- run:12:12        "crea lo Short del giorno", daily 12:12 Europe/Rome
- run:15:37        "crea il secondo Short del giorno", daily 15:37 Europe/Rome
- run:send_later   one-shot, 5 min after each slot: `engager.py pending` + link to pin
- HUD dashboard    https://claude.ai/artifact/Gt3sp46jubpX81nwaHEeGS: videos, activity, tasks (files from hud.py), codegraph (live Graphify)

### Entry points (CLI)
- agent.py         render: `--script examples/<slug>.json` | `--resume output/<slug>` | `<topic>` (needs ANTHROPIC_API_KEY)
- publisher.py     upload: `output/<slug> --slot auto` | `--all` | `--auth` | `--dry-run` | `--at <UTC>`
- engager.py       comments: `inbox` | `reply <file>` | `pending` | `first <folder>` | `auto`

### Modules (function: role)
- writer.py        SCHEMA, SYSTEM (script rules), write_script(topic) [only when no script is given]
- images.py        generate_images(prompts, img_dir) -> _gen (3 tries) -> _call(model); quota error 4006 = stop
- tts.py           ensure_models() downloads Kokoro to models/; synth(lines) -> voice.wav + timing (voice am_michael, speed 1.08)
- sfx.py           build_track(timing) -> sfx.wav; GEN = whoosh, impact, riser, tick
- montage.py       render(d, timing, hook, highlights, name) -> subs.ass + ffmpeg -> short_<slug>.mp4 (30 fps)
- publisher.py     build_metadata, access_token, taken_times, next_slot, upload, publish
- engager.py       REPLY_RULES, my_channel, recent_videos, inbox, post_replies, pending_first_comments, first_comment

### Data
- examples/<slug>.json   script written by Claude (committed). Model: examples/barings.json
- topics.md              topics already done: `- date | slug | title` (committed, never repeat)
- output/<slug>/         git-ignored: script.json, img/0-7.jpg, voice.wav, timing.json, sfx.wav,
                         subs.ass, short_<slug>.mp4, short_<slug>_upload.txt, youtube_metadata.json, youtube.json (id, url, publish_at)
- models/                git-ignored: kokoro-v1.0.onnx, voices-v1.0.bin
- docs/                  index.html, privacy.html, terms.html (pages for the Google OAuth app)

### Config and constants
- SLOTS             publisher.py: 14:00, 18:00 Europe/Rome; MIN_LEAD 20 min; no other video within 90 min
- CF_IMAGE_MODEL    images.py: default @cf/black-forest-labs/flux-2-klein-4b (~156 neurons/image at 768x1344), FALLBACK flux-1-schnell
- CLOUDFLARE_ACCOUNT_ID / CF_ACCOUNT_ID   images.py account; token is injected by the proxy (no key)
- YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN   publisher.env(); PC fallback: client_secret*.json, youtube_token.json
- ANTHROPIC_API_KEY optional, only for writer.py / engager draft_replies (in cloud runs Claude writes directly)
- DISCLAIMER, CTA, BASE_TAGS, CATEGORY_EDUCATION=27   publisher.py metadata; containsSyntheticMedia = True always

### External services
- Cloudflare Workers AI   images; free 10,000 neurons/day, resets 00:00 UTC; error 4006 = quota used up
- YouTube Data API v3     upload (scheduled private + publishAt), playlistItems, videos, commentThreads
- Kokoro (GitHub release) voice model download
- GitHub repo             macquistiarco-lab/shorts-agent, branch main
- Graphify connector      code graph of this repo

## Edges

run:12:12 -> CLAUDE.md : follows "Daily routine"
run:15:37 -> CLAUDE.md : follows "Daily routine"
CLAUDE.md -> engager.py : step 1 inbox, reply, pending
CLAUDE.md -> topics.md : step 2 pick a new topic, step 8 append line
CLAUDE.md -> examples/<slug>.json : step 3 Claude writes it (rules in writer.py SCHEMA/SYSTEM)
CLAUDE.md -> agent.py : step 4 render, step 5 --resume to fix an image
CLAUDE.md -> publisher.py : step 7 --slot auto
CLAUDE.md -> run:send_later : step 7, 5 min after the slot
run:send_later -> engager.py : pending_first_comments
agent.py -> writer.py : write_script (only for a bare topic)
agent.py -> images.py : generate_images -> output/<slug>/img/N.jpg (skips existing files)
agent.py -> tts.py : synth -> voice.wav, timing
agent.py -> sfx.py : build_track -> sfx.wav
agent.py -> montage.py : render -> short_<slug>.mp4
agent.py -> output/<slug>/ : writes script.json, short_<slug>_upload.txt
images.py -> Cloudflare Workers AI : POST ai/run/<model>
tts.py -> Kokoro (GitHub release) : ensure_models -> models/
montage.py -> ffmpeg : subtitles (hook_text, highlight_words), image cuts, audio mix
publisher.py -> output/<slug>/ : reads script.json + mp4, writes youtube.json (skip if exists)
publisher.py -> YouTube Data API v3 : taken_times reads channel schedule -> next_slot -> upload
publisher.py -> SLOTS : next_slot
engager.py -> publisher.py : imports access_token
engager.py -> examples/<slug>.json : pending matches video title -> first_comment
engager.py -> YouTube Data API v3 : commentThreads (403 "disabled comments" = video still scheduled/private)
examples/<slug>.json -> topics.md : committed together on main
Graphify connector -> GitHub repo : indexes main
CLAUDE.md -> hud.py : step 10 refresh the HUD dashboard files

## Gotchas
- A scheduled (private) video refuses comments: pending posts only after it goes public.
- The YouTube API cannot pin comments; the owner pins in Studio (channel under review: pinning not possible yet, keep the reminder).
- Two runs a day fill both slots; the queue runs about one day ahead.
- Never commit output/ or models/; commit only topics.md and examples/<slug>.json in the daily run.
- Image fix: delete output/<slug>/img/N.jpg, edit its prompt in output/<slug>/script.json, `agent.py --resume`.
- AI images often put fake text on signs or billboards: ask for "no signs, no billboards".
