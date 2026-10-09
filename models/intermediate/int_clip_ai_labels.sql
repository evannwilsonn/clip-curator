-- What the models saw in each clip: CLIP's top scene and YOLO's objects.
with top_scene as (
    select clip_id, scene_label, probability
    from {{ ref('stg_video__scenes') }}
    qualify row_number() over (partition by clip_id order by probability desc, scene_label) = 1
),

per_frame_people as (
    select clip_id, ts_s, sum(case when object_label = 'person' then 1 else 0 end) as people
    from {{ ref('stg_video__detections') }}
    group by 1, 2
),

objects as (
    select clip_id, object_label, count(*) as detections
    from {{ ref('stg_video__detections') }}
    group by 1, 2
)

select
    c.clip_id,
    s.scene_label                                          as ai_scene,
    s.probability                                          as ai_scene_confidence,
    coalesce(p.max_people, 0)                              as max_people_in_frame,
    coalesce(p.max_people, 0) > 0                          as contains_people,
    o.object_list                                          as ai_objects
from {{ ref('stg_video__clips') }} as c
left join top_scene as s using (clip_id)
left join (select clip_id, max(people) as max_people from per_frame_people group by 1) as p using (clip_id)
left join (
    select clip_id, {{ string_list('object_label', 'detections desc, object_label') }} as object_list
    from objects group by 1
) as o using (clip_id)
