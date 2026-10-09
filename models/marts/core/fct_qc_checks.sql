-- One row per clip per rule: did it fire, what was measured, and what the rule does.
select
    k.clip_id,
    k.rule_id,
    r.rule_name,
    r.action,
    r.targets_defect,
    r.threshold,
    k.fired,
    k.observed,
    k.matches_clip_id
from {{ ref('int_clip_rule_checks') }} as k
join {{ ref('qc_rules') }} as r using (rule_id)
