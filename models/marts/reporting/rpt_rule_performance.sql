-- Each rule scored against the labeled challenge set.
-- Hit: fired on the defect it targets. False alarm: fired on a clip with no applied defect.
with k as (
    select q.*, g.injected_defect
    from {{ ref('fct_qc_checks') }} as q
    join {{ ref('stg_video__ground_truth') }} as g using (clip_id)
)
select
    rule_id,
    rule_name,
    action,
    targets_defect,
    threshold,
    sum(case when fired then 1 else 0 end)                                           as fired,
    sum(case when injected_defect = targets_defect then 1 else 0 end)                as target_clips,
    sum(case when fired and injected_defect = targets_defect then 1 else 0 end)      as hits,
    sum(case when fired and injected_defect = 'none' then 1 else 0 end)              as false_alarms,
    sum(case when fired and injected_defect not in ('none', targets_defect) then 1 else 0 end) as fired_on_other_defects,
    sum(case when fired and injected_defect = targets_defect then 1 else 0 end) * 1.0
        / nullif(sum(case when injected_defect = targets_defect then 1 else 0 end), 0) as recall,
    sum(case when fired and injected_defect = targets_defect then 1 else 0 end) * 1.0
        / nullif(sum(case when fired and injected_defect in ('none', targets_defect) then 1 else 0 end), 0) as precision
from k
group by 1, 2, 3, 4, 5
