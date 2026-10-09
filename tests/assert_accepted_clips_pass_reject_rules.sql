-- No accepted clip may have fired a reject rule.
select d.clip_id, q.rule_id
from {{ ref('rpt_clip_decisions') }} as d
join {{ ref('fct_qc_checks') }} as q using (clip_id)
where d.decision = 'accept' and q.fired and q.action = 'reject'
