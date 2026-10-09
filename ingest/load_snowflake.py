"""
Copy the raw landing zone from the local DuckDB warehouse into Snowflake, table for table.

Each raw table is written to Parquet, uploaded to an internal stage with PUT and loaded with
COPY INTO, then row counts are checked against DuckDB. JSON columns become VARIANT. Lower-case
column names land unquoted (upper case in Snowflake) so dbt's unquoted references resolve;
mixed-case source names (e.g. "Date") keep their exact case, as the staging models quote them.

Sign-in is key-pair: set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER and SNOWFLAKE_PRIVATE_KEY_PATH.

    python ingest/load_snowflake.py --database BELLWETHER --schemas raw_datahub
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

import duckdb
import snowflake.connector

TYPES = {"VARCHAR": "VARCHAR", "BIGINT": "NUMBER", "INTEGER": "NUMBER", "HUGEINT": "NUMBER", "SMALLINT": "NUMBER",
         "DOUBLE": "FLOAT", "FLOAT": "FLOAT", "BOOLEAN": "BOOLEAN", "DATE": "DATE", "JSON": "VARIANT",
         "TIMESTAMP": "TIMESTAMP_NTZ", "TIMESTAMP WITH TIME ZONE": "TIMESTAMP_TZ"}


def sf_name(name: str, keep_case: bool) -> str:
    if keep_case or name != name.lower() or not name.replace("_", "").isalnum():
        return '"' + name.replace('"', '""') + '"'
    return name


def connect():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"],
        private_key_file=os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duckdb", required=True)
    ap.add_argument("--database", required=True)
    ap.add_argument("--schemas", required=True, help="comma-separated raw schemas to copy")
    a = ap.parse_args()

    wh = os.environ.get("SNOWFLAKE_WAREHOUSE", "PORTFOLIO_WH")
    duck = duckdb.connect(a.duckdb, read_only=True)
    sf = connect()
    cur = sf.cursor()
    cur.execute(f"create warehouse if not exists {wh} warehouse_size = xsmall auto_suspend = 60 auto_resume = true initially_suspended = true")
    cur.execute(f"use warehouse {wh}")
    cur.execute(f"create database if not exists {a.database}")
    cur.execute(f"use database {a.database}")
    tmp = Path(tempfile.mkdtemp())

    for schema in a.schemas.split(","):
        cur.execute(f"create schema if not exists {schema}")
        cur.execute(f"use schema {schema}")
        cur.execute("create stage if not exists _load_stage")
        tables = [r[0] for r in duck.execute(
            "select table_name from information_schema.tables where table_schema = ? order by 1", [schema]).fetchall()]
        for t in tables:
            cols = duck.execute("select column_name, data_type from information_schema.columns "
                                "where table_schema = ? and table_name = ? order by ordinal_position", [schema, t]).fetchall()
            keep = t.startswith("_")
            pq = tmp / f"{schema}__{t}.parquet"
            duck.execute(f"copy (select * from {schema}.\"{t}\") to '{pq.as_posix()}' (format parquet)")
            cur.execute(f"put 'file://{pq.as_posix()}' @_load_stage auto_compress = false overwrite = true")
            ddl, sel = [], []
            for name, dtype in cols:
                st = TYPES.get(dtype.upper().split("(")[0], "VARCHAR")
                ident = sf_name(name, keep)
                ddl.append(f"{ident} {st}")
                src = f'$1:"{name}"'
                sel.append(f"parse_json({src}::varchar)" if st == "VARIANT" else f"{src}::{st}")
            table = sf_name(t, False) if not keep else t.upper()
            cur.execute(f"create or replace table {table} ({', '.join(ddl)})")
            cur.execute(f"copy into {table} from (select {', '.join(sel)} from @_load_stage/{pq.name}) "
                        f"file_format = (type = parquet) force = true")
            n_sf = cur.execute(f"select count(*) from {table}").fetchone()[0]
            n_dk = duck.execute(f'select count(*) from {schema}."{t}"').fetchone()[0]
            if n_sf != n_dk:
                raise SystemExit(f"{schema}.{t}: Snowflake has {n_sf:,} rows, DuckDB has {n_dk:,}")
            print(f"  {a.database}.{schema}.{t:<26} {n_sf:>12,} rows")
            pq.unlink()
    sf.close()


if __name__ == "__main__":
    main()
