"""Snapshot for the Shorts HUD dashboard: channel videos and repo activity as JSON files.

    python hud.py [out_dir]   # default output/hud -> videos.json, activity.json

Each file is {"rows": [...], "meta": [...]}; the daily run uploads them to the dashboard.
"""
import datetime as dt
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

from engager import api, my_channel
from publisher import access_token

HERE = os.path.dirname(os.path.abspath(__file__))
ROME = ZoneInfo("Europe/Rome")
SNAPSHOT = dt.datetime.now(ROME).strftime("%Y-%m-%d %H:%M")


def rome(ts):
    if not ts:
        return None
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t.astimezone(ROME).strftime("%Y-%m-%d %H:%M")


def slugs_by_title():
    out = {}
    for f in os.listdir(os.path.join(HERE, "examples")):
        if f.endswith(".json"):
            s = json.load(open(os.path.join(HERE, "examples", f)))
            out[s.get("title", "").strip().lower()] = s.get("slug", f[:-5])
    return out


def videos(token):
    me, uploads = my_channel(token)
    items = api("GET", "playlistItems", token, params={
        "part": "contentDetails", "playlistId": uploads, "maxResults": 50})["items"]
    ids = [i["contentDetails"]["videoId"] for i in items]
    slugs = slugs_by_title()
    rows = []
    for k in range(0, len(ids), 50):
        for v in api("GET", "videos", token, params={
                "part": "snippet,status,statistics", "id": ",".join(ids[k:k + 50])})["items"]:
            st, sn, stats = v["status"], v["snippet"], v.get("statistics", {})
            scheduled = st["privacyStatus"] == "private" and st.get("publishAt")
            rows.append({
                "video_id": v["id"],
                "title": sn["title"],
                "slug": slugs.get(sn["title"].strip().lower(), ""),
                "status": "scheduled" if scheduled else st["privacyStatus"],
                "goes_live": rome(st.get("publishAt") or sn.get("publishedAt")),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "url": f"https://youtube.com/shorts/{v['id']}",
                "snapshot": SNAPSHOT,
            })
    rows.sort(key=lambda r: r["goes_live"] or "", reverse=True)
    return rows


def activity(n=30):
    subprocess.run(["git", "-C", HERE, "fetch", "-q", "origin", "main"], check=False)
    log = subprocess.run(["git", "-C", HERE, "log", "origin/main", f"-n{n}",
                          "--format=%H%x09%cI%x09%s"], capture_output=True, text=True).stdout
    rows = []
    for line in log.splitlines():
        sha, when, subject = line.split("\t", 2)
        kind = "short" if subject.startswith(("Short ", "topics")) else "code"
        rows.append({"when": rome(when), "kind": kind, "event": subject, "commit": sha[:7]})
    return rows


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "output", "hud")
    os.makedirs(out, exist_ok=True)
    now = SNAPSHOT
    code = open(os.path.abspath(__file__)).read()
    meta = [{"label": "Snapshot (Rome)", "value": now},
            {"label": "hud.py", "value": code, "type": "code", "lang": "python"}]
    for name, rows in (("videos", videos(access_token())), ("activity", activity())):
        path = os.path.join(out, f"{name}.json")
        json.dump({"rows": rows, "meta": meta}, open(path, "w"), indent=1, ensure_ascii=False)
        print(f"{path}: {len(rows)} rows")


if __name__ == "__main__":
    main()
