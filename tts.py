"""Step 3: voiceover with Kokoro (local, free, commercial use OK) + per-line timing."""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models")
GAP = 0.18
BASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
FILES = ["voices-v1.0.bin", "kokoro-v1.0.onnx"]


def ensure_models() -> None:
    """Download the Kokoro voice model (~350 MB) the first time."""
    import urllib.request
    os.makedirs(MODELS, exist_ok=True)
    for name in FILES:
        path = os.path.join(MODELS, name)
        if os.path.exists(path):
            continue
        print(f"[shorts] downloading {name} (first run only)...", flush=True)
        urllib.request.urlretrieve(BASE + name, path + ".part")
        os.replace(path + ".part", path)


def synth(lines: list[dict], out_dir: str, voice: str = "am_michael", speed: float = 1.08) -> list[dict]:
    from kokoro_onnx import Kokoro
    ensure_models()
    k = Kokoro(os.path.join(MODELS, "kokoro-v1.0.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
    audio, timing, t, sr = [], [], 0.0, 24000
    for line in lines:
        a, sr = k.create(line["text"], voice=voice, speed=speed, lang="en-us")
        dur = len(a) / sr
        timing.append({**line, "start": t, "dur": dur})
        audio += [a, np.zeros(int(sr * GAP), dtype=a.dtype)]
        t += dur + GAP
    sf.write(os.path.join(out_dir, "voice.wav"), np.concatenate(audio), sr)
    with open(os.path.join(out_dir, "timing.json"), "w") as f:
        json.dump(timing, f, indent=1)
    return timing
