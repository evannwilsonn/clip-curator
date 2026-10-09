-- Frame signals rolled up to one row per clip.
select
    clip_id,
    count(*)                         as frames_sampled,
    avg(brightness)                  as avg_brightness,
    avg(contrast)                    as avg_contrast,
    median(sharpness)                as median_sharpness,
    avg(motion)                      as avg_motion,
    avg(pct_clipped_high)            as avg_clipped_high,
    avg(pct_crushed_low)             as avg_crushed_low
from {{ ref('stg_video__frames') }}
group by 1
