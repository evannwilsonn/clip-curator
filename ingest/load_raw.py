"""
Step 4: load the extracted tables into the warehouse landing zone (schema raw_video).

JSON-lines tables land as a single JSON column (`payload`), the same shape a Snowflake
VARIANT column has, and dbt staging pulls the fields out. The ground truth CSV lands
as text. Every table gets _source_file and _loaded_at audit columns.

    python ingest/load_raw.py
On Snowflake, the same files are staged and loaded with COPY INTO (ingest/snowflake_load.sql).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "extracted"
DB = ROOT / "warehouse" / "clip_curator.duckdb"
SCHEMA = "raw_video"
JSON_TABLES = ["clips", "frames", "detections", "scenes", "embeddings", "pairs", "sources"]


def main() -> None:
    if not (EXT / "clips.jsonl").exists():
        raise SystemExit("Nothing extracted yet. Run extract/run_extract.py first.")
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute(f"create schema if not exists {SCHEMA}")
    loaded_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"Loading into {DB.relative_to(ROOT)}")
    for t in JSON_TABLES:
        path = (EXT / f"{t}.jsonl").as_posix()
        con.execute(f"""create or replace table {SCHEMA}.{t} as
            select json as payload, ? as _source_file, cast(? as timestamp) as _loaded_at
            from read_json_objects('{path}', format = 'newline_delimited')""", [f"{t}.jsonl", loaded_at])
        print(f"  {SCHEMA}.{t:<12} {con.execute(f'select count(*) from {SCHEMA}.{t}').fetchone()[0]:>7,} rows")
    con.execute(f"""create or replace table {SCHEMA}.ground_truth as
        select *, 'ground_truth.csv' as _source_file, cast(? as timestamp) as _loaded_at
        from read_csv('{(EXT / 'ground_truth.csv').as_posix()}', header = true, all_varchar = true)""", [loaded_at])
    print(f"  {SCHEMA}.ground_truth {con.execute(f'select count(*) from {SCHEMA}.ground_truth').fetchone()[0]:>7,} rows")
    con.close()


if __name__ == "__main__":
    main()
