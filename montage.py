"""Step 5: 1080x1920 montage with Ken Burns, word-chunk captions, hook, drone, voice and SFX."""
import os
import re
import subprocess

FPS = 30


def _run(args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)


def _ts(s):
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def _segments(timing, total):
    segs = []
    for i, t in enumerate(timing):
        end = timing[i + 1]["start"] if i + 1 < len(timing) else total
        if segs and segs[-1][0] == t["img"]:
            segs[-1][1] += end - t["start"]
        else:
            segs.append([t["img"], end - t["start"]])
    return segs


def _subs(timing, hook, highlights, path):
    hdr = """[Script Info]
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Display,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Hook,Inter Display,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB0000000,-1,0,0,0,100,100,0,0,3,18,0,8,60,60,230,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    hook_end = timing[min(1, len(timing) - 1)]
    ev = [f"Dialogue: 1,{_ts(0)},{_ts(hook_end['start'] + hook_end['dur'])},Hook,,0,0,0,,"
          f"{{\\fad(150,200)}}{hook.upper().replace(chr(10), chr(92) + 'N')}"]
    words = {w.strip(".,!?").upper() for h in highlights for w in h.split()}
    hl = sorted((re.escape(w) for w in words if len(w) > 2), key=len, reverse=True)
    hl_re = re.compile(r"(\b\d[\d,.]*%?|\$[\d,.]+\w*" + (r"|\b(?:" + "|".join(hl) + r")\b" if hl else "") + r")")
    for t in timing:
        chunks, cur = [], []
        for w in t["text"].split():
            cur.append(w)
            if len(cur) == 3 or re.search(r"[.,!?;:]$", w) or len(" ".join(cur)) > 14:
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        total_len = sum(len(" ".join(c)) + 2 for c in chunks)
        s = t["start"]
        for c in chunks:
            d = t["dur"] * (len(" ".join(c)) + 2) / total_len
            txt = hl_re.sub(r"{\\c&H00D7FF&}\1{\\c&HFFFFFF&}", " ".join(c).upper())
            ev.append(f"Dialogue: 0,{_ts(s)},{_ts(s + d)},Cap,,0,0,0,,"
                      f"{{\\pos(540,1180)\\fscx90\\fscy90\\t(0,80,\\fscx100\\fscy100)}}{txt}")
            s += d
    with open(path, "w") as f:
        f.write(hdr + "\n".join(ev) + "\n")


def render(d, timing, hook, highlights, out_name):
    os.chdir(d)
    total = timing[-1]["start"] + timing[-1]["dur"] + 0.6
    parts = []
    for i, (img, dur) in enumerate(_segments(timing, total)):
        n = int(round(dur * FPS)); out = f"seg{i:02d}.mp4"
        z = "min(1.0+0.0009*on,1.25)" if i % 2 == 0 else "max(1.22-0.0009*on,1.0)"
        vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps={FPS},"
              f"eq=brightness=-0.04:contrast=1.08,vignette=PI/5,format=yuv420p")
        _run(["-loop", "1", "-i", f"img/{img}.jpg", "-vf", vf, "-frames:v", str(n),
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out])
        parts.append(out)
    with open("list.txt", "w") as f:
        f.write("".join(f"file '{p}'\n" for p in parts))
    _run(["-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "video.mp4"])
    _subs(timing, hook, highlights, "subs.ass")

    # fixed voice gain from measured peak (dynamic loudnorm faded the ending)
    comp = "acompressor=threshold=0.1:ratio=3:attack=5:release=80"
    r = subprocess.run(["ffmpeg", "-i", "voice.wav", "-af", comp + ",volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    gain = -1.5 - float(re.search(r"max_volume: (-?[\d.]+) dB", r).group(1))
    drone = ("aevalsrc='0.5*sin(2*PI*55*t)*(0.6+0.4*sin(2*PI*0.1*t))"
             "+0.3*sin(2*PI*82.4*t)+0.15*sin(2*PI*110*t)':s=48000")
    fc = (f"[2:a]lowpass=f=400,volume=0.05,afade=t=out:st={total - 1.5:.2f}:d=1.5[m];"
          f"[1:a]aresample=48000,{comp},volume={gain:.2f}dB,alimiter=limit=0.89[v];"
          f"[3:a]aresample=48000[s];"
          f"[v][m][s]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.89[a];"
          f"[0:v]subtitles=subs.ass[vv]")
    _run(["-i", "video.mp4", "-i", "voice.wav", "-f", "lavfi", "-t", f"{total}", "-i", drone,
          "-i", "sfx.wav", "-filter_complex", fc, "-map", "[vv]", "-map", "[a]",
          "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "aac", "-b:a", "192k",
          "-t", f"{total}", "-movflags", "+faststart", out_name])
    for p in parts + ["list.txt", "video.mp4"]:
        os.remove(p)
    return total
