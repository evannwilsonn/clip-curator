"""
Step 3: extract structured data from every clip. This is where the AI models run.

For each clip it writes rows to data/extracted/ (JSON lines, one file per table):

  clips.jsonl       container metadata from ffprobe plus a full decode check
  frames.jsonl      2 frames per second: brightness, contrast, sharpness, clipping,
                    motion vs. the previous sample, and a 64-bit perceptual hash
  detections.jsonl  YOLOv8n object detections (COCO classes) on frames every 1.5 s
  scenes.jsonl      CLIP zero-shot scene scores for the clip (one row per scene), each
                    scene scored with several phrasings averaged together (prompt ensembling)
  embeddings.jsonl  a 512-d CLIP embedding per clip
  labels.jsonl      few-shot scene labels: cosine similarity of each clip's CLIP embedding to
                    the average embedding of the labeled reference clips for every scene
                    (seeds/label_references.csv, one reference clip per source video)
  pairs.jsonl       duplicate search: for every pair of clips that look alike to CLIP,
                    16 frames from each are lined up in time and compared pixel by pixel.
                      aligned_diff   how different the matching frames are (0 = identical)
                      alignment_ratio  aligned difference / difference between non-matching
                                       frames. A re-upload lines up frame for frame, so this
                                       drops well below 1; two different moments from the
                                       same fixed camera stay near 1.

Nothing is decided here. Thresholds and accept/reject rules live in dbt, so they're
versioned, tested and changeable without re-running the models.

    python extract/run_extract.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "data" / "clips"
OUT = ROOT / "data" / "extracted"
CACHE = ROOT / "models_cache"
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE))

SAMPLE_FPS = 2.0
DETECT_EVERY_S = 1.5
PAIR_CANDIDATE_SIM = 0.85   # only clip pairs at least this CLIP-similar are compared frame by frame
PAIR_SAMPLES = 16
CLIP_FRAMES = 5
# scene -> several phrasings; CLIP scores each and the text embeddings are averaged
SCENES = {
    "conveyor belt": ["a dark grey woven conveyor belt surface in close-up", "a single metal bolt lying on a dark grey conveyor belt",
                      "an industrial conveyor belt carrying screws and bolts"],
    "objects on a table": ["plastic water bottles standing on a white table", "bottles lined up on a table",
                           "a hand placing bottles on a table"],
    "produce on a conveyor": ["a pineapple on a conveyor belt", "fruit and vegetables moving on a conveyor",
                              "a single piece of fruit on a white shelf"],
    "parking lot from above": ["white parking lines painted on asphalt seen from above",
                               "a white car driving across a parking lot seen from directly above",
                               "a top-down security camera view of a parking lot"],
    "classroom": ["a classroom with students sitting at desks", "a meeting room with people at tables and blue chairs",
                  "a teacher standing in front of a class"],
    "inside a car": ["a driver inside a car", "the interior of a car with a person driving",
                     "a dashboard camera view of the driver's seat"],
    "indoor hallway": ["people walking down an office hallway toward the camera",
                       "people standing in an office hallway with a door and a glass wall behind them",
                       "an empty office corridor with a ceiling light and a wooden floor"],
    "person portrait": ["a head and shoulders portrait of a person against a plain white wall",
                        "two people standing side by side against a blank white wall", "a passport style photo of a person"],
    "retail store aisle": ["shoppers in a store aisle with shelves of products", "a warehouse store aisle stacked with dishes",
                           "people browsing shelves in a shop"],
    "warehouse worker": ["a worker in an orange safety vest and hard hat on a warehouse floor",
                         "an empty concrete warehouse floor with marked zones", "an industrial floor seen from a security camera"],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=codec_name,width,height,avg_frame_rate,nb_frames,bit_rate:format=duration,size",
                        "-of", "json", str(path)], capture_output=True, text=True)
    meta = json.loads(r.stdout or "{}")
    st = (meta.get("streams") or [{}])[0]
    fmt = meta.get("format", {})
    num, _, den = (st.get("avg_frame_rate") or "0/1").partition("/")
    # a full decode is the only reliable corruption check: count errors ffmpeg reports
    d = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], capture_output=True, text=True)
    return {
        "codec": st.get("codec_name"),
        "width": st.get("width"),
        "height": st.get("height"),
        "fps": round(float(num) / float(den), 3) if float(den or 0) else None,
        "duration_s": float(fmt["duration"]) if fmt.get("duration") else None,
        "bytes": int(fmt["size"]) if fmt.get("size") else path.stat().st_size,
        # strip memory addresses and local paths so the same file always yields the same message
        "probe_error": re.sub(r" @ 0x[0-9a-f]+|\S*/", "", r.stderr.strip())[:300] or None,
        "decode_error_lines": len([l for l in d.stderr.splitlines() if l.strip()]),
    }


def dhash(gray: np.ndarray) -> str:
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    return f"{int(''.join('1' if b else '0' for b in bits), 2):016x}"


def frame_rows(path: Path, clip_id: str):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    step = max(1, round(fps / SAMPLE_FPS))
    rows, keep, prev, idx, decoded = [], [], None, 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        decoded += 1
        if idx % step == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            g = cv2.resize(gray, (320, int(320 * gray.shape[0] / gray.shape[1]))) if gray.shape[1] > 320 else gray
            rows.append({
                "clip_id": clip_id,
                "frame_index": idx,
                "ts_s": round(idx / fps, 3),
                "brightness": round(float(g.mean()), 3),
                "contrast": round(float(g.std()), 3),
                "sharpness": round(float(cv2.Laplacian(g, cv2.CV_64F).var()), 3),
                "pct_clipped_high": round(float((g >= 250).mean()), 4),
                "pct_crushed_low": round(float((g <= 8).mean()), 4),
                "motion": None if prev is None or prev.shape != g.shape else round(float(cv2.absdiff(g, prev).mean()), 4),
                "dhash": dhash(gray),
            })
            prev = g
            keep.append((idx / fps, frame))
        idx += 1
    cap.release()
    return rows, keep, decoded


def aligned_frames(path: Path) -> list[np.ndarray] | None:
    """PAIR_SAMPLES evenly spaced frames, grey, 64x36, normalized for brightness and contrast.
    Small and normalized on purpose: a re-encode at another size or quality lands on the same grid."""
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if n < PAIR_SAMPLES:
        return None
    out = []
    for k in range(PAIR_SAMPLES):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((k + 0.5) * n / PAIR_SAMPLES))
        ok, frame = cap.read()
        if not ok:
            return None
        g = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32), (64, 36), interpolation=cv2.INTER_AREA)
        out.append((g - g.mean()) / (g.std() + 1e-6))
    cap.release()
    return out


def similarity_index() -> None:
    """Duplicate search: CLIP narrows the candidates, then frames are lined up in time and compared."""
    emb = {}
    for line in (OUT / "embeddings.jsonl").open():
        d = json.loads(line)
        emb[d["clip_id"]] = np.array(d["embedding"])
    frames = {c: aligned_frames(CLIPS / f"{c}.mp4") for c in emb}
    off_diag = ~np.eye(PAIR_SAMPLES, dtype=bool)
    ids = sorted(emb)
    with (OUT / "pairs.jsonl").open("w") as f:
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                sim = float(emb[a] @ emb[b])
                if sim < PAIR_CANDIDATE_SIM or frames[a] is None or frames[b] is None:
                    continue
                m = np.array([[float(np.mean(np.abs(x - y))) for y in frames[b]] for x in frames[a]])
                diag, off = float(np.median(np.diag(m))), float(np.median(m[off_diag]))
                f.write(json.dumps({"clip_a": a, "clip_b": b, "clip_similarity": round(sim, 5),
                                    "aligned_diff": round(diag, 5),
                                    "alignment_ratio": round(diag / off, 5) if off > 1e-6 else 0.0}) + "\n")


def few_shot_labels() -> None:
    """Score every clip against each scene's reference centroid (nearest-centroid classifier on CLIP)."""
    import csv
    emb = {}
    for line in (OUT / "embeddings.jsonl").open():
        d = json.loads(line)
        emb[d["clip_id"]] = np.array(d["embedding"])
    groups: dict[str, list] = {}
    with (ROOT / "seeds" / "label_references.csv").open() as f:
        for r in csv.DictReader(f):
            if r["clip_id"] not in emb:
                raise SystemExit(f"Reference clip {r['clip_id']} has no embedding; check seeds/label_references.csv")
            groups.setdefault(r["scene"], []).append(emb[r["clip_id"]])
    centroids = {s: (np.mean(v, 0) / np.linalg.norm(np.mean(v, 0))) for s, v in sorted(groups.items())}
    with (OUT / "labels.jsonl").open("w") as f:
        for cid in sorted(emb):
            for scene, c in centroids.items():
                f.write(json.dumps({"clip_id": cid, "scene_label": scene, "similarity": round(float(emb[cid] @ c), 5)}) + "\n")


def main() -> None:
    import sys
    if "--pairs-only" in sys.argv:
        similarity_index()
        few_shot_labels()
        return
    from PIL import Image
    import open_clip
    import torch
    from ultralytics import YOLO

    # fixed seed and thread count so repeated runs produce identical numbers
    torch.manual_seed(0)
    torch.set_num_threads(2)
    OUT.mkdir(parents=True, exist_ok=True)
    yolo = YOLO(str(CACHE / "yolov8n.pt"))
    clip_model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k", cache_dir=str(CACHE))
    clip_model.eval()
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    labels = list(SCENES)
    with torch.no_grad():
        rows = []
        for scene in labels:
            t = clip_model.encode_text(tokenizer([f"a photo of {p}" for p in SCENES[scene]]))
            t = t / t.norm(dim=-1, keepdim=True)
            t = t.mean(0)
            rows.append(t / t.norm())
        text = torch.stack(rows)

    files = sorted(CLIPS.glob("*.mp4"))
    out = {k: (OUT / f"{k}.jsonl").open("w") for k in ["clips", "frames", "detections", "scenes", "embeddings"]}
    t0 = time.time()
    for n, path in enumerate(files, 1):
        clip_id = path.stem
        meta = probe(path)
        frames, keep, decoded = frame_rows(path, clip_id)
        meta.update({"clip_id": clip_id, "file": path.name, "sha256": sha256(path), "frames_decoded": decoded,
                     "frames_sampled": len(frames), "model_versions": "yolov8n; open_clip ViT-B-32 laion2b_s34b_b79k"})
        out["clips"].write(json.dumps(meta) + "\n")
        for r in frames:
            out["frames"].write(json.dumps(r) + "\n")
        if not keep:
            continue

        # YOLO: one frame every DETECT_EVERY_S seconds
        last = -1e9
        det_frames = []
        for ts, fr in keep:
            if ts - last >= DETECT_EVERY_S - 1e-6:
                det_frames.append((ts, fr))
                last = ts
        results = yolo.predict([f for _, f in det_frames], imgsz=640, conf=0.45, verbose=False)
        for (ts, fr), res in zip(det_frames, results):
            h, w = fr.shape[:2]
            for box, cls, conf in zip(res.boxes.xyxy.tolist(), res.boxes.cls.tolist(), res.boxes.conf.tolist()):
                area = max(0.0, (box[2] - box[0]) * (box[3] - box[1])) / (w * h)
                out["detections"].write(json.dumps({"clip_id": clip_id, "ts_s": round(ts, 3), "label": res.names[int(cls)],
                                                    "confidence": round(conf, 4), "box_area_pct": round(area, 4)}) + "\n")

        # CLIP: embed up to CLIP_FRAMES evenly spaced frames, average, score every scene
        picks = [keep[i] for i in np.linspace(0, len(keep) - 1, min(CLIP_FRAMES, len(keep))).round().astype(int)]
        imgs = torch.stack([preprocess(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))) for _, f in picks])
        with torch.no_grad():
            emb = clip_model.encode_image(imgs)
            emb = emb / emb.norm(dim=-1, keepdim=True)
            mean = emb.mean(0)
            mean = mean / mean.norm()
            probs = (100.0 * mean @ text.T).softmax(-1).tolist()
        for label, p in zip(labels, probs):
            out["scenes"].write(json.dumps({"clip_id": clip_id, "scene_label": label, "probability": round(p, 5)}) + "\n")
        out["embeddings"].write(json.dumps({"clip_id": clip_id, "embedding": [round(v, 6) for v in mean.tolist()]}) + "\n")
        if n % 10 == 0 or n == len(files):
            print(f"  {n}/{len(files)} clips  ({time.time() - t0:.0f}s)")
    for f in out.values():
        f.close()

    similarity_index()
    few_shot_labels()

    # ground truth and source manifest travel with the extract so the warehouse load is self-contained
    (OUT / "ground_truth.csv").write_bytes((CLIPS / "_ground_truth.csv").read_bytes())
    sources = json.loads((ROOT / "data" / "sources" / "_manifest.json").read_text())
    with (OUT / "sources.jsonl").open("w") as f:
        for s in sources:
            f.write(json.dumps(s) + "\n")


if __name__ == "__main__":
    main()
