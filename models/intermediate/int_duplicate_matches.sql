-- Clips that repeat an earlier clip. The earliest clip_id in a group is the one kept.
with exact as (
    select
        clip_id,
        first_value(clip_id) over (partition by sha256 order by clip_id) as matches_clip_id,
        'exact_duplicate' as rule_id,
        1.0 as similarity
    from {{ ref('stg_video__clips') }}
    where sha256 is not null
),

near as (
    select
        p.clip_b              as clip_id,
        p.clip_a              as matches_clip_id,
        'near_duplicate'      as rule_id,
        p.clip_similarity     as similarity
    from {{ ref('stg_video__pairs') }} as p
    join {{ ref('stg_video__clips') }} as a on a.clip_id = p.clip_a
    join {{ ref('stg_video__clips') }} as b on b.clip_id = p.clip_b
    cross join (select threshold from {{ ref('qc_rules') }} where rule_id = 'near_duplicate') as r
    where a.sha256 <> b.sha256
      and p.clip_similarity >= r.threshold
      and p.motion_corr >= {{ var('near_dupe_motion_corr') }}
      and p.brightness_corr >= {{ var('near_dupe_brightness_corr') }}
)

select clip_id, matches_clip_id, rule_id, similarity from exact where clip_id <> matches_clip_id
union all
select clip_id, matches_clip_id, rule_id, similarity
from near
qualify row_number() over (partition by clip_id order by similarity desc) = 1
