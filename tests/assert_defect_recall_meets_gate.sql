-- Quality gate: the rules must stop at least min_defect_recall of the clips with a known defect.
select count(*) as defective, sum(case when decision <> 'accept' then 1 else 0 end) as flagged
from {{ ref('rpt_clip_decisions') }}
where injected_defect <> 'none'
having sum(case when decision <> 'accept' then 1 else 0 end) * 1.0 / count(*) < {{ var('min_defect_recall') }}
