.PHONY: all setup fetch clips extract load build dashboard serve verify clean

all: fetch clips extract load build dashboard   ## run the whole pipeline end to end

setup:        ## install dependencies (CPU-only PyTorch)
	pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
	pip install -r requirements.txt

fetch:        ## download the 17 CC BY 4.0 source videos + manifest
	python ingest/fetch_sources.py

clips:        ## cut 6-second clips and build the labeled challenge set
	python ingest/build_clips.py

extract:      ## run ffprobe, frame signals, YOLOv8 and CLIP over every clip
	python extract/run_extract.py

load:         ## land the extracted tables in the warehouse (DuckDB)
	python ingest/load_raw.py

build:        ## seed, run and test every dbt model, including the quality gates
	dbt build

dashboard:    ## export the reporting marts and thumbnails for the dashboard
	python dashboard/export_data.py

verify:       ## re-run the AI extraction and confirm the output is byte-for-byte identical
	python scripts/check_reproducible.py

serve:        ## open the dashboard at http://localhost:8000
	cd dashboard && python -m http.server 8000

clean:
	rm -rf target warehouse/*.duckdb data dashboard/data.json
