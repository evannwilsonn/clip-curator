-- Objects YOLO found in accepted clips: how often and in how many clips.
select
    t.object_label,
    count(*)                       as detections,
    count(distinct t.clip_id)      as clips,
    avg(t.confidence)              as avg_confidence
from {{ ref('fct_detections') }} as t
join {{ ref('rpt_clip_decisions') }} as d using (clip_id)
where d.decision = 'accept'
group by 1
