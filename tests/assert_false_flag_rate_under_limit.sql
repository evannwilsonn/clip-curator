-- Quality gate: no more than max_false_flag_rate of clean clips may be flagged.
select count(*) as clean, sum(case when decision <> 'accept' then 1 else 0 end) as flagged
from {{ ref('rpt_clip_decisions') }}
where injected_defect = 'none'
having sum(case when decision <> 'accept' then 1 else 0 end) * 1.0 / count(*) > {{ var('max_false_flag_rate') }}
