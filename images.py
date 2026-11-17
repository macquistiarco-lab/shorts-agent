"""Step 2: vertical images via Cloudflare Workers AI."""
import base64
import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests

ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "e3fa680817e9e513cbaadea35d703817")
# In the cloud environment the proxy injects the real token; locally set CLOUDFLARE_API_TOKEN.
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "proxy-injected")
# Neurons per vertical image (free quota: 10,000/day): klein-4b ~160, schnell ~60, klein-9b ~1370.
MODEL = os.environ.get("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-2-klein-4b")
FALLBACK = "@cf/black-forest-labs/flux-1-schnell"


class QuotaError(RuntimeError):
    pass


def _call(model: str, prompt: str) -> dict:
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{model}"
    hdr = {"Authorization": f"Bearer {TOKEN}"}
    if "flux-2" in model:  # multipart input
        r = requests.post(url, headers=hdr, timeout=180,
                          files={"prompt": (None, prompt), "width": (None, "768"),
                                 "height": (None, "1344")})
    elif "schnell" in model:
        r = requests.post(url, headers=hdr, json={"prompt": prompt, "steps": 4}, timeout=180)
    else:
        r = requests.post(url, headers=hdr, json={"prompt": prompt, "width": 1080, "height": 1920},
                          timeout=180)
    return r.json()


def _gen(prompt: str, out: str, tries: int = 3) -> None:
    err = None
    for model in dict.fromkeys([MODEL, FALLBACK]):
        for attempt in range(tries):
            try:
                d = _call(model, prompt)
                if d.get("success") and d["result"].get("image"):
                    with open(out, "wb") as f:
                        f.write(base64.b64decode(d["result"]["image"]))
                    return
                err = d.get("errors")
                if any(e.get("code") == 4006 for e in err or []):
                    raise QuotaError("Cloudflare daily free quota used up (resets 00:00 UTC)")
            except QuotaError:
                raise
            except Exception as e:  # network / JSON errors
                err = e
            time.sleep(3 * (attempt + 1))
        print(f"[shorts] {model} failed for {out}: {err}; trying fallback", flush=True)
    raise RuntimeError(f"Image generation failed for {out}: {err}")


def generate_images(prompts: list[str], img_dir: str) -> None:
    os.makedirs(img_dir, exist_ok=True)
    jobs = [(p, os.path.join(img_dir, f"{i}.jpg")) for i, p in enumerate(prompts)
            if not os.path.exists(os.path.join(img_dir, f"{i}.jpg"))]
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(lambda j: _gen(*j), jobs))
