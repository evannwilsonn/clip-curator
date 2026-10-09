select
    {{ jtext('clip_id') }}        as clip_id,
    {{ jtext('scene_label') }}    as scene_label,
    {{ jnum('probability') }}     as probability
from {{ source('video', 'scenes') }}
