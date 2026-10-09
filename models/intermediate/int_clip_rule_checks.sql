-- Every clip checked against every rule in seeds/qc_rules.csv. Thresholds come from the seed.
{%- set t = "max(case when rule_id = '{r}' then threshold end)" %}
with th as (
    select
        {%- for r in ['too_short','low_resolution','black','too_dark','overexposed','blurry','frozen'] %}
        {{ t.format(r=r) }} as t_{{ r }}{{ ',' if not loop.last }}
        {%- endfor %}
    from {{ ref('qc_rules') }}
),

c as (
    select
        m.clip_id,
        m.duration_s,
        m.width_px,
        m.decode_errors,
        m.frames_decoded,
        s.avg_brightness,
        s.avg_contrast,
        s.median_sharpness,
        s.avg_motion,
        s.avg_clipped_high,
        coalesce(m.decode_errors, 0) > 0 or coalesce(m.frames_decoded, 0) = 0 as unreadable
    from {{ ref('stg_video__clips') }} as m
    left join {{ ref('int_clip_signals') }} as s using (clip_id)
),

checks as (
    select clip_id, 'unreadable' as rule_id, unreadable as fired, cast(decode_errors as double) as observed from c
    union all
    select clip_id, 'too_short', not unreadable and duration_s < t_too_short, duration_s from c cross join th
    union all
    select clip_id, 'low_resolution', not unreadable and width_px < t_low_resolution, cast(width_px as double) from c cross join th
    union all
    select clip_id, 'black', not unreadable and avg_brightness < t_black and avg_contrast < 2, avg_brightness from c cross join th
    union all
    select clip_id, 'too_dark', not unreadable and avg_brightness < t_too_dark, avg_brightness from c cross join th
    union all
    select clip_id, 'overexposed', not unreadable and avg_clipped_high > t_overexposed, avg_clipped_high from c cross join th
    union all
    -- a black picture has no edges at all; that's the black rule's job, not a focus problem
    select clip_id, 'blurry', not unreadable and median_sharpness < t_blurry and avg_contrast >= 2, median_sharpness from c cross join th
    union all
    select clip_id, 'frozen', not unreadable and avg_motion < t_frozen and avg_contrast >= 2, avg_motion from c cross join th
    union all
    select c.clip_id, r.rule_id, d.clip_id is not null, d.similarity
    from c
    cross join (select 'exact_duplicate' as rule_id union all select 'near_duplicate') as r
    left join {{ ref('int_duplicate_matches') }} as d on d.clip_id = c.clip_id and d.rule_id = r.rule_id
)

select
    k.clip_id,
    k.rule_id,
    coalesce(k.fired, false) as fired,
    k.observed,
    d.matches_clip_id
from checks as k
left join {{ ref('int_duplicate_matches') }} as d on d.clip_id = k.clip_id and d.rule_id = k.rule_id
