# Shorts agent

Topic -> finished YouTube Short in English (1080x1920, ~50 s), same style as the Archegos test.

| Step | Tool |
|---|---|
| Script, image prompts, SFX cues, title/description | Claude (`claude-opus-5-5`, structured JSON) |
| Images | Cloudflare Workers AI, `flux-2-klein-9b` (free daily quota) |
| Voice | Kokoro `am_michael` (local, free, OK for monetized channels) |
| SFX | synthesised from scratch (whoosh on cuts, impact, riser, tick) |
| Montage | ffmpeg: Ken Burns, 1-3 word captions with yellow numbers, hook on top, drone |

## Setup

```bash
pip install -r requirements.txt
curl -sSL -o models/voices-v1.0.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
curl -sSL -o models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
```

Env vars: `ANTHROPIC_API_KEY` (only for topic mode), `CLOUDFLARE_API_TOKEN` (not needed in the
Claude cloud environment, where the proxy injects it), optional `CF_IMAGE_MODEL`
(e.g. `@cf/leonardo/lucid-origin`).

## Use

```bash
python agent.py "Nick Leeson and the fall of Barings Bank"   # full auto
python agent.py --script examples/barings.json                # ready-made script
python agent.py --resume output/barings                       # re-render after edits
```

Output in `output/<slug>/`: `short_<slug>.mp4`, `short_<slug>_upload.txt`, `script.json`, `img/`.
To swap an image, delete `img/N.jpg` (or edit its prompt in `script.json`) and `--resume`.

Before publishing: watch it, check the facts, and tick "Altered or synthetic content" in YouTube Studio.
