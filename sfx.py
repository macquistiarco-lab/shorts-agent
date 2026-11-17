"""Step 4: original sound effects synthesised from scratch (no copyright issues)."""
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)


def _env(n, a, r):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / r)


def _sweep(n, fmin, fmax, shape):
    x, out, seg = rng.standard_normal(n), np.zeros(n), 512
    for i in range(0, n, seg):
        f = fmin + (fmax - fmin) * shape(i / n)
        sos = butter(2, [max(f * 0.6, 60), min(f * 1.5, 20000)], btype="band", fs=SR, output="sos")
        out[i:i + seg] = sosfilt(sos, x[i:i + seg])
    return out / np.abs(out).max()


def whoosh(dur=0.55):
    n = int(SR * dur)
    return _sweep(n, 300, 3800, lambda p: np.sin(np.pi * p) ** 2) * np.sin(np.pi * np.arange(n) / n) ** 2 * 0.8


def impact(dur=1.6):
    n = int(SR * dur); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(55 * np.exp(-t * 2.5) + 38) / SR) * _env(n, 0.004, 0.45)
    nz = sosfilt(butter(4, 900, fs=SR, output="sos"), rng.standard_normal(n)) * _env(n, 0.001, 0.06) * 0.6
    x = np.tanh(1.8 * (sub + nz))
    return x / np.abs(x).max() * 0.95


def riser(dur=2.6):
    n = int(SR * dur); t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * np.cumsum(110 + 330 * (t / dur) ** 2) / SR) * 0.3
    y = (_sweep(n, 200, 5200, lambda p: p ** 2) + tone) * (t / dur) ** 2.2
    return y / np.abs(y).max() * 0.8


def tick():
    n = int(SR * 0.08)
    return np.sin(2 * np.pi * 2200 * np.arange(n) / SR) * _env(n, 0.0005, 0.012) * 0.7


GEN = {"whoosh": (whoosh, 0.35), "impact": (impact, 0.9), "riser": (riser, 0.45), "tick": (tick, 0.5)}


def build_track(timing: list[dict], total: float, out_dir: str) -> str:
    track = np.zeros(int(SR * (total + 3)))
    cache = {k: f() for k, (f, _) in GEN.items()}

    def put(name, at):
        x = cache[name] * GEN[name][1]
        if name == "riser":
            at -= len(x) / SR  # riser ends where the line starts
        i = max(int(at * SR), 0)
        track[i:i + len(x)] += x[:len(track) - i]

    prev_img = None
    for i, t in enumerate(timing):
        if i > 0 and t["img"] != prev_img:
            put("whoosh", t["start"] - 0.25)
        prev_img = t["img"]
        if t.get("sfx", "none") in GEN:
            put(t["sfx"], t["start"])
    put("impact", 0.0)  # hit on the opening hook
    path = os.path.join(out_dir, "sfx.wav")
    sf.write(path, np.clip(track, -1, 1).astype(np.float32), SR)
    return path
