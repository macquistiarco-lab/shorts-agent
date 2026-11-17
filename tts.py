"""Step 3: voiceover with Kokoro (local, free, commercial use OK) + per-line timing."""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = 0.18


def synth(lines: list[dict], out_dir: str, voice: str = "am_michael", speed: float = 1.08) -> list[dict]:
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(HERE, "models/kokoro-v1.0.onnx"),
               os.path.join(HERE, "models/voices-v1.0.bin"))
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
