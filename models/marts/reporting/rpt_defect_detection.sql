-- For each kind of applied defect: how many clips had it and how many the pipeline stopped.
select
    injected_defect,
    count(*)                                                       as clips,
    sum(case when decision = 'reject' then 1 else 0 end)           as rejected,
    sum(case when decision = 'reject' then 1 else 0 end) * 1.0 / count(*) as reject_rate
from {{ ref('rpt_clip_decisions') }}
group by 1
