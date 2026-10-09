"""
Step 3: extract structured data from every clip. This is where the AI models run.

For each clip it writes rows to data/extracted/ (JSON lines, one file per table):

  clips.jsonl       container metadata from ffprobe plus a full decode check
  frames.jsonl      2 frames per second: brightness, contrast, sharpness, clipping,
                    motion vs. the previous sample, and a 64-bit perceptual hash
  detections.jsonl  YOLOv8n object detections (COCO classes) on frames every 1.5 s
  scenes.jsonl      CLIP zero-shot scene scores for the clip (one row per label)
  embeddings.jsonl  a 512-d CLIP embedding per clip
  pairs.jsonl       similarity index: every clip pair whose CLIP embeddings are at least
                    0.90 cosine-similar, with how closely their motion and brightness
                    curves track each other over time (a re-upload tracks almost perfectly;
                    two different shots from the same camera don't)

Nothing is decided here. Thresholds and accept/reject rules live in dbt, so they're
versioned, tested and changeable without re-running the models.

    python extract/run_extract.py
"""
from __future__ import annotations

import hashlib
import json
import os
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
SCENE_LABELS = [
    "a retail store aisle with products on shelves",
    "a city street with cars and traffic",
    "a classroom with students at desks",
    "a factory or warehouse floor",
    "a close-up of a person's face",
    "people walking through an indoor hallway or lobby",
    "a person driving a car, seen from inside the vehicle",
    "fruit and vegetables on a table",
    "metal bolts and machine parts on a conveyor",
    "bottles on a table",
    "an office with people at desks",
]


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
        "probe_error": r.stderr.strip()[:300] or None,
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


def similarity_index() -> None:
    """Pairwise CLIP similarity plus temporal-profile correlation, written as candidate pairs."""
    emb = {}
    for line in (OUT / "embeddings.jsonl").open():
        d = json.loads(line)
        emb[d["clip_id"]] = np.array(d["embedding"])
    prof: dict[str, list] = {}
    for line in (OUT / "frames.jsonl").open():
        d = json.loads(line)
        prof.setdefault(d["clip_id"], []).append(d)

    def corr(a: str, b: str, key: str):
        x = np.array([f[key] or 0.0 for f in prof.get(a, [])][1:])
        y = np.array([f[key] or 0.0 for f in prof.get(b, [])][1:])
        n = min(len(x), len(y))
        if n < 4 or x[:n].std() < 1e-6 or y[:n].std() < 1e-6:
            return None
        return round(float(np.corrcoef(x[:n], y[:n])[0, 1]), 5)

    ids = sorted(emb)
    with (OUT / "pairs.jsonl").open("w") as f:
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                sim = float(emb[a] @ emb[b])
                if sim >= 0.90:
                    f.write(json.dumps({"clip_a": a, "clip_b": b, "clip_similarity": round(sim, 5),
                                        "motion_corr": corr(a, b, "motion"), "brightness_corr": corr(a, b, "brightness")}) + "\n")


def main() -> None:
    import sys
    if "--pairs-only" in sys.argv:
        similarity_index()
        return
    from PIL import Image
    import open_clip
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(max(1, os.cpu_count() or 1))
    OUT.mkdir(parents=True, exist_ok=True)
    yolo = YOLO(str(CACHE / "yolov8n.pt"))
    clip_model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k", cache_dir=str(CACHE))
    clip_model.eval()
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    with torch.no_grad():
        text = clip_model.encode_text(tokenizer([f"a photo of {s}" for s in SCENE_LABELS]))
        text = text / text.norm(dim=-1, keepdim=True)

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

        # CLIP: embed up to 3 evenly spaced frames, average, score scene labels
        picks = [keep[i] for i in np.linspace(0, len(keep) - 1, min(3, len(keep))).round().astype(int)]
        imgs = torch.stack([preprocess(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))) for _, f in picks])
        with torch.no_grad():
            emb = clip_model.encode_image(imgs)
            emb = emb / emb.norm(dim=-1, keepdim=True)
            mean = emb.mean(0)
            mean = mean / mean.norm()
            probs = (100.0 * mean @ text.T).softmax(-1).tolist()
        for label, p in zip(SCENE_LABELS, probs):
            out["scenes"].write(json.dumps({"clip_id": clip_id, "scene_label": label, "probability": round(p, 5)}) + "\n")
        out["embeddings"].write(json.dumps({"clip_id": clip_id, "embedding": [round(v, 6) for v in mean.tolist()]}) + "\n")
        if n % 10 == 0 or n == len(files):
            print(f"  {n}/{len(files)} clips  ({time.time() - t0:.0f}s)")
    for f in out.values():
        f.close()

    similarity_index()

    # ground truth and source manifest travel with the extract so the warehouse load is self-contained
    (OUT / "ground_truth.csv").write_bytes((CLIPS / "_ground_truth.csv").read_bytes())
    sources = json.loads((ROOT / "data" / "sources" / "_manifest.json").read_text())
    with (OUT / "sources.jsonl").open("w") as f:
        for s in sources:
            f.write(json.dumps(s) + "\n")


if __name__ == "__main__":
    main()
