"""
Export the reporting marts (plus a small thumbnail per clip) into dashboard/data.json.

Run after `dbt build`:  python dashboard/export_data.py
"""
from __future__ import annotations

import base64
import json
from datetime import date
from pathlib import Path

import cv2
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "clip_curator.duckdb"
CLIPS = ROOT / "data" / "clips"
OUT = ROOT / "dashboard" / "data.json"


def thumb(path: Path) -> str | None:
    cap = cv2.VideoCapture(str(path))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, n // 2))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return None
    h, w = frame.shape[:2]
    frame = cv2.resize(frame, (192, int(192 * h / w)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 62])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def table(con, sql):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = []
    for r in cur.fetchall():
        rows.append([round(v, 4) if isinstance(v, float) else (float(v) if hasattr(v, "as_tuple") else v) for v in r])
    return {"columns": cols, "rows": rows}


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    decisions = table(con, """select clip_id, source_id, setting, decision, reasons, duplicate_of, duration_s, width_px,
        avg_brightness, median_sharpness, avg_motion, ai_scene, ai_scene_correct, is_label_reference, contains_people,
        ai_objects, injected_defect, outcome from reporting.rpt_clip_decisions order by clip_id""")
    payload = {
        "generated": date.today().isoformat(),
        "decisions": decisions,
        "rules": table(con, "select * from reporting.rpt_rule_performance order by action, rule_id"),
        "defects": table(con, "select * from reporting.rpt_defect_detection order by injected_defect"),
        "composition": table(con, "select * from reporting.rpt_dataset_composition order by accepted_clips desc"),
        "label_quality": table(con, "select * from reporting.rpt_label_quality order by method"),
        "objects": table(con, "select * from reporting.rpt_object_inventory order by clips desc, detections desc limit 12"),
        "sources": table(con, "select source_id, license, source_url from staging.stg_video__sources order by 1"),
        "totals": dict(zip(["clips", "frames", "detections", "scene_scores", "pairs"], con.execute("""select
            (select count(*) from staging.stg_video__clips), (select count(*) from staging.stg_video__frames),
            (select count(*) from staging.stg_video__detections), (select count(*) from staging.stg_video__scenes),
            (select count(*) from staging.stg_video__pairs)""").fetchone())),
        "thumbs": {cid: thumb(CLIPS / f"{cid}.mp4") for cid, *_ in decisions["rows"]},
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
