-- How accurate the AI scene labels are, measured on every readable clip that wasn't used as a
-- labeled reference (references can't grade themselves). Few-shot is what the dataset uses;
-- zero-shot (text prompts only) is shown as the baseline it replaced.
with graded as (
    select *
    from {{ ref('rpt_clip_decisions') }}
    where not is_label_reference
      and ai_scene is not null
      and injected_defect in ('none', 'exact_dupe', 'near_dupe')
)
select
    'few-shot (references)'                                                as method,
    count(*)                                                               as clips_graded,
    sum(case when ai_scene_correct then 1 else 0 end)                      as correct,
    avg(case when ai_scene_correct then 1.0 else 0.0 end)                  as accuracy
from graded
union all
select
    'zero-shot (text prompts)',
    count(*),
    sum(case when zero_shot_correct then 1 else 0 end),
    avg(case when zero_shot_correct then 1.0 else 0.0 end)
from graded
