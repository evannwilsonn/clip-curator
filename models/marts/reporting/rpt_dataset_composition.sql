-- What the accepted dataset contains, by setting, using the AI labels.
select
    setting,
    count(*)                                                                  as accepted_clips,
    sum(duration_s) / 60.0                                                    as minutes,
    avg(case when contains_people then 1.0 else 0.0 end)                      as share_with_people,
    avg(case when ai_scene_matches_source then 1.0 else 0.0 end)              as ai_label_accuracy,
    sum(case when needs_human_label then 1 else 0 end)                        as needs_human_label
from {{ ref('rpt_clip_decisions') }}
where decision = 'accept'
group by 1
