select
    {{ jtext('clip_id') }}        as clip_id,
    {{ jnum('ts_s') }}            as ts_s,
    {{ jtext('label') }}          as object_label,
    {{ jnum('confidence') }}      as confidence,
    {{ jnum('box_area_pct') }}    as box_area_pct
from {{ source('video', 'detections') }}
