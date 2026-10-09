"""
Reproducibility check: run the AI extraction a second time and confirm every output file
is byte-for-byte identical to the first run. Fixed seeds, a fixed thread count and pinned
model weights mean the same clips must always produce the same data and the same decisions.

    python scripts/check_reproducible.py     (after `make all`)
"""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "extracted"
FILES = ["clips", "frames", "detections", "scenes", "labels", "embeddings", "pairs"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not (EXT / "clips.jsonl").exists():
        raise SystemExit("Run the pipeline first (make all).")
    before = {f: digest(EXT / f"{f}.jsonl") for f in FILES}
    backup = Path(tempfile.mkdtemp()) / "extracted"
    shutil.copytree(EXT, backup)
    try:
        subprocess.run([sys.executable, str(ROOT / "extract" / "run_extract.py")], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        after = {f: digest(EXT / f"{f}.jsonl") for f in FILES}
    finally:
        shutil.rmtree(EXT)
        shutil.copytree(backup, EXT)
    bad = [f for f in FILES if before[f] != after[f]]
    for f in FILES:
        print(f"  {f + '.jsonl':<18} {'identical' if f not in bad else 'DIFFERENT'}")
    if bad:
        raise SystemExit(f"Not reproducible: {', '.join(bad)}")
    print("Second run matched the first exactly.")


if __name__ == "__main__":
    main()
