"""
Step 1: download the source footage.

Seventeen real-world clips (retail aisles, traffic, classrooms, factory floors, faces,
people walking) published by Intel's IoT DevKit under CC BY 4.0. Each download is
recorded in a manifest with its URL, size, SHA-256 and license so every clip in the
dataset can be traced to its source and credited.

    python ingest/fetch_sources.py
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sources"
BASE = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master"
LICENSE = "CC BY 4.0, Intel IoT DevKit sample-videos"

SOURCES = [
    "bolt-detection", "bolt-multi-size-detection", "bottle-detection", "car-detection", "classroom",
    "face-demographics-walking-and-pause", "face-demographics-walking", "fruit-and-vegetable-detection",
    "head-pose-face-detection-female-and-male", "head-pose-face-detection-female",
    "head-pose-face-detection-male", "one-by-one-person-detection", "people-detection",
    "person-bicycle-car-detection", "store-aisle-detection", "worker-zone-detection",
    "driver-action-recognition",
]


def fetch(url: str, attempts: int = 4) -> bytes:
    for i in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "clip-curator/1.0"}), timeout=180) as r:
                return r.read()
        except Exception as exc:
            if i == attempts - 1:
                raise SystemExit(f"Failed to fetch {url}: {exc}")
            time.sleep(2 ** i)
    raise AssertionError


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name in SOURCES:
        url, path = f"{BASE}/{name}.mp4", OUT / f"{name}.mp4"
        if not path.exists():
            path.write_bytes(fetch(url))
        body = path.read_bytes()
        manifest.append({"source_id": name, "file": path.name, "url": url, "license": LICENSE,
                         "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                         "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        print(f"  {name:<44} {len(body) / 1e6:>6.1f} MB")
    (OUT / "_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
