-- The accepted dataset never contains two byte-identical files.
select c.sha256, count(*) as copies
from {{ ref('rpt_clip_decisions') }} as d
join {{ ref('dim_clips') }} as c using (clip_id)
where d.decision = 'accept'
group by 1
having count(*) > 1
