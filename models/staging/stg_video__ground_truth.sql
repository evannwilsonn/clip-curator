select
    trim(clip_id)                         as clip_id,
    trim(injected_defect)                 as injected_defect,
    nullif(trim(duplicate_of), '')        as duplicate_of
from {{ source('video', 'ground_truth') }}
