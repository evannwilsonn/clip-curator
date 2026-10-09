-- What the accepted dataset contains, by setting.
select
    setting,
    count(*)                                                                  as accepted_clips,
    sum(duration_s) / 60.0                                                    as minutes,
    avg(case when contains_people then 1.0 else 0.0 end)                      as share_with_people,
    {{ string_list('distinct ai_scene', 'ai_scene') }}                        as scenes
from {{ ref('rpt_clip_decisions') }}
where decision = 'accept'
group by 1
