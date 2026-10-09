-- The curation decision for every clip, with reasons, plus how it compares to the known defect.
with fired as (
    select
        clip_id,
        max(case when action = 'reject' then 1 else 0 end)  as any_reject,
        {{ string_list('case when fired then rule_name end', 'rule_id') }} as reasons,
        max(matches_clip_id)                                 as duplicate_of
    from {{ ref('fct_qc_checks') }}
    where fired
    group by 1
)

select
    d.clip_id,
    d.source_id,
    d.setting,
    case when f.any_reject = 1 then 'reject' else 'accept' end as decision,
    f.reasons,
    f.duplicate_of,
    d.duration_s,
    d.width_px,
    d.avg_brightness,
    d.median_sharpness,
    d.avg_motion,
    d.expected_scene,
    d.ai_scene,
    d.ai_scene_similarity,
    d.ai_scene_correct,
    d.zero_shot_scene,
    d.zero_shot_correct,
    d.is_label_reference,
    d.contains_people,
    d.ai_objects,
    g.injected_defect,
    case
        when g.injected_defect <> 'none' and f.clip_id is not null then 'caught'
        when g.injected_defect <> 'none' then 'missed'
        when f.clip_id is not null then 'flagged clean clip'
        else 'clean, accepted'
    end                                                      as outcome
from {{ ref('dim_clips') }} as d
left join fired as f using (clip_id)
left join {{ ref('stg_video__ground_truth') }} as g using (clip_id)
