"""Step 2: vertical images via Cloudflare Workers AI."""
import base64
import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests

ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "e3fa680817e9e513cbaadea35d703817")
# In the cloud environment the proxy injects the real token; locally set CLOUDFLARE_API_TOKEN.
TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "proxy-injected")
MODEL = os.environ.get("CF_IMAGE_MODEL", "@cf/black-forest-labs/flux-2-klein-9b")


def _gen(prompt: str, out: str, tries: int = 3) -> None:
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{MODEL}"
    hdr = {"Authorization": f"Bearer {TOKEN}"}
    for attempt in range(tries):
        try:
            if "flux-2" in MODEL:  # multipart input
                r = requests.post(url, headers=hdr, timeout=180,
                                  files={"prompt": (None, prompt), "width": (None, "768"),
                                         "height": (None, "1344")})
            else:
                body = {"prompt": prompt, "width": 1080, "height": 1920}
                if "schnell" in MODEL:
                    body = {"prompt": prompt, "steps": 8}
                r = requests.post(url, headers=hdr, json=body, timeout=180)
            d = r.json()
            if d.get("success") and d["result"].get("image"):
                with open(out, "wb") as f:
                    f.write(base64.b64decode(d["result"]["image"]))
                return
            err = d.get("errors")
        except Exception as e:  # network / JSON errors
            err = e
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Image generation failed for {out}: {err}")


def generate_images(prompts: list[str], img_dir: str) -> None:
    os.makedirs(img_dir, exist_ok=True)
    jobs = [(p, os.path.join(img_dir, f"{i}.jpg")) for i, p in enumerate(prompts)
            if not os.path.exists(os.path.join(img_dir, f"{i}.jpg"))]
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(lambda j: _gen(*j), jobs))
