select clip_id, ts_s, object_label, confidence, box_area_pct from {{ ref('stg_video__detections') }}
