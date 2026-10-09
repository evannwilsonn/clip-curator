-- Few-shot scene scores: similarity of each clip to every scene's reference centroid.
select
    {{ jtext('clip_id') }}        as clip_id,
    {{ jtext('scene_label') }}    as scene_label,
    {{ jnum('similarity') }}      as similarity
from {{ source('video', 'labels') }}
