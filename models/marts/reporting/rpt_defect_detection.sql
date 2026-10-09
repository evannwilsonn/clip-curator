-- For each kind of applied defect: how many clips had it and how many the pipeline stopped.
select
    injected_defect,
    count(*)                                                       as clips,
    sum(case when decision <> 'accept' then 1 else 0 end)          as flagged,
    sum(case when decision = 'reject' then 1 else 0 end)           as rejected,
    sum(case when decision = 'review' then 1 else 0 end)           as sent_to_review,
    sum(case when decision <> 'accept' then 1 else 0 end) * 1.0 / count(*) as flag_rate
from {{ ref('rpt_clip_decisions') }}
group by 1
