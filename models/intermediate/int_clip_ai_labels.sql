-- What the models saw in each clip.
--   ai_scene:          few-shot CLIP label (nearest scene centroid built from the labeled reference clips)
--   zero_shot_scene:   CLIP's zero-shot pick from text prompts alone, kept as a baseline to compare against
--   objects / people:  YOLOv8 detections
with few_shot as (
    select
        clip_id,
        scene_label,
        similarity,
        similarity - lead(similarity) over (partition by clip_id order by similarity desc, scene_label) as margin,
        row_number() over (partition by clip_id order by similarity desc, scene_label) as rn
    from {{ ref('stg_video__labels') }}
),

zero_shot as (
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
    f.scene_label                                          as ai_scene,
    f.similarity                                           as ai_scene_similarity,
    f.margin                                               as ai_scene_margin,
    z.scene_label                                          as zero_shot_scene,
    z.probability                                          as zero_shot_confidence,
    coalesce(p.max_people, 0)                              as max_people_in_frame,
    coalesce(p.max_people, 0) > 0                          as contains_people,
    o.object_list                                          as ai_objects
from {{ ref('stg_video__clips') }} as c
left join few_shot as f on f.clip_id = c.clip_id and f.rn = 1
left join zero_shot as z on z.clip_id = c.clip_id
left join (select clip_id, max(people) as max_people from per_frame_people group by 1) as p on p.clip_id = c.clip_id
left join (
    select clip_id, {{ string_list('object_label', 'detections desc, object_label') }} as object_list
    from objects group by 1
) as o on o.clip_id = c.clip_id
