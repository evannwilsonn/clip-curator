-- Load the extracted tables into Snowflake: the same raw landing zone the DuckDB loader builds.
-- 1) Run the extract locally: python ingest/fetch_sources.py && python ingest/build_clips.py && python extract/run_extract.py
-- 2) Run this file with SnowSQL from the project folder (PUT needs a client, not a worksheet):
--      snowsql -a <account> -u <user> -f ingest/snowflake_load.sql
-- JSON-lines tables land as one VARIANT column (payload); dbt staging pulls the fields out.

create database if not exists clip_curator;
use database clip_curator;
create schema if not exists raw_video;
use schema raw_video;

create or replace file format jsonl type = json;
create or replace file format csv_header type = csv parse_header = true field_optionally_enclosed_by = '"';
create or replace stage extract_stage;
put file://data/extracted/*.jsonl @extract_stage auto_compress = true overwrite = true;
put file://data/extracted/ground_truth.csv @extract_stage auto_compress = true overwrite = true;

execute immediate $$
declare
  tables array default array_construct('clips','frames','detections','scenes','labels','embeddings','pairs','sources');
  t varchar;
begin
  for i in 0 to array_size(tables) - 1 do
    t := tables[i];
    execute immediate 'create or replace table ' || t || ' (payload variant, _source_file varchar, _loaded_at timestamp_ntz)';
    execute immediate 'copy into ' || t || ' from (select $1, metadata$filename, current_timestamp() from @extract_stage/' || t || '.jsonl.gz) file_format = (format_name = ''jsonl'')';
  end for;
  return 'loaded';
end;
$$;

create or replace table ground_truth (clip_id varchar, source_id varchar, start_seconds varchar, injected_defect varchar,
                                      duplicate_of varchar, _source_file varchar, _loaded_at timestamp_ntz);
copy into ground_truth from (select $1, $2, $3, $4, $5, metadata$filename, current_timestamp() from @extract_stage/ground_truth.csv.gz)
  file_format = (type = csv skip_header = 1 field_optionally_enclosed_by = '"');
