"""
Step 2: cut the source footage into clips and build a labeled challenge set.

Every source video is split into 6-second clips (640 px wide, H.264), the unit a
training-data team reviews. Then, with a fixed seed, a share of clips get one known
defect applied. That gives the QC rules a ground truth to be scored against: we know
exactly which clips *should* be rejected, so precision and recall can be measured
instead of guessed.

Defects applied (each one a real failure seen in collected video data):
  blurred        heavy Gaussian blur (out of focus)
  too_dark       exposure pulled far down (underexposed)
  overexposed    exposure pushed up until highlights clip
  frozen         a single frame repeated (stalled capture)
  black          black frames only (lens cap / dead feed)
  low_res        downscaled to 160 px wide
  too_short      cut to 1 second
  corrupt        file truncated mid-stream
  exact_dupe     byte-for-byte copy of another clip
  near_dupe      same content re-encoded, slightly cropped and recompressed

The ground truth is written to data/clips/_ground_truth.csv. Clean clips are labeled "none".

    python ingest/build_clips.py
"""
from __future__ import annotations

import csv
import json
import random
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "sources"
OUT = ROOT / "data" / "clips"
CLIP_SECONDS = 6
SEED = 20261009

DEFECT_FILTERS = {
    "blurred": "scale=640:-2,gblur=sigma=12",
    "too_dark": "scale=640:-2,eq=brightness=-0.42:contrast=0.55",
    "overexposed": "scale=640:-2,eq=brightness=0.55:contrast=1.6",
    "frozen": "scale=640:-2,trim=end_frame=1,loop=loop=-1:size=1,fps=15",
    "black": "scale=640:-2,drawbox=c=black:t=fill",
    "low_res": "scale=160:-2",
}


def ff(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def encode(src: Path, start: float, dst: Path, vf: str = "scale=640:-2", seconds: float = CLIP_SECONDS) -> None:
    ff("-ss", f"{start:.2f}", "-t", f"{seconds:.2f}", "-i", str(src), "-vf", vf, "-an", "-t", f"{seconds:.2f}",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p", str(dst))


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    rng = random.Random(SEED)

    # 1) cut every source into clean 6-second segments (at most 8 per source to keep sources balanced)
    segments = []
    for src in sorted(SRC.glob("*.mp4")):
        total = duration(src)
        starts = [s for s in range(0, int(total) - CLIP_SECONDS + 1, CLIP_SECONDS)][:8]
        for k, s in enumerate(starts):
            segments.append((src, s, f"{src.stem}__{k:02d}"))
    print(f"{len(segments)} segments from {len(list(SRC.glob('*.mp4')))} sources")

    # 2) choose which segments get a defect: ~35% of clips, every defect type represented
    defects = list(DEFECT_FILTERS) + ["too_short", "corrupt", "near_dupe", "exact_dupe"]
    shuffled = segments[:]
    rng.shuffle(shuffled)
    n_defective = round(len(segments) * 0.35)
    plan = {seg[2]: defects[i % len(defects)] for i, seg in enumerate(shuffled[:n_defective])}

    truth = []
    clean_ids = []
    for src, start, seg_id in segments:
        defect = plan.get(seg_id, "none")
        clip_id = seg_id
        dst = OUT / f"{clip_id}.mp4"
        if defect in DEFECT_FILTERS:
            encode(src, start, dst, DEFECT_FILTERS[defect])
        elif defect == "too_short":
            encode(src, start, dst, seconds=1.0)
        elif defect == "corrupt":
            encode(src, start, dst)
            data = dst.read_bytes()
            dst.write_bytes(data[: len(data) // 3])           # cut the file off a third of the way in
        elif defect in ("near_dupe", "exact_dupe"):
            continue                                          # made from clean clips below
        else:
            encode(src, start, dst)
            clean_ids.append(clip_id)
        truth.append({"clip_id": clip_id, "source_id": src.stem, "start_seconds": start, "injected_defect": defect})

    # 3) duplicates are new clips copied from clean ones, so the original stays in the set
    dupes = [d for d in plan.values() if d in ("near_dupe", "exact_dupe")]
    originals = rng.sample(clean_ids, len(dupes))
    for i, (kind, orig) in enumerate(zip(dupes, originals)):
        clip_id = f"{orig}__{'copy' if kind == 'exact_dupe' else 'reupload'}"
        src_path, dst = OUT / f"{orig}.mp4", OUT / f"{clip_id}.mp4"
        if kind == "exact_dupe":
            shutil.copyfile(src_path, dst)
        else:
            ff("-i", str(src_path), "-vf", "crop=iw*0.94:ih*0.94,scale=600:-2", "-an",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "32", "-pix_fmt", "yuv420p", str(dst))
        source_id, _, seg = orig.partition("__")
        truth.append({"clip_id": clip_id, "source_id": source_id, "start_seconds": int(seg) * CLIP_SECONDS,
                      "injected_defect": kind, "duplicate_of": orig})

    with (OUT / "_ground_truth.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["clip_id", "source_id", "start_seconds", "injected_defect", "duplicate_of"])
        w.writeheader()
        w.writerows(truth)
    counts: dict[str, int] = {}
    for t in truth:
        counts[t["injected_defect"]] = counts.get(t["injected_defect"], 0) + 1
    print(f"{len(truth)} clips written: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
