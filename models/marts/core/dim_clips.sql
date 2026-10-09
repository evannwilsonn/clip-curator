-- One row per clip: file metadata, where it came from, and what the AI models saw.
select
    c.clip_id,
    c.source_id,
    sc.setting,
    sc.expected_scene,
    src.license,
    src.source_url,
    c.file_name,
    c.sha256,
    c.codec,
    c.width_px,
    c.height_px,
    c.fps,
    c.duration_s,
    c.file_bytes,
    s.avg_brightness,
    s.avg_contrast,
    s.median_sharpness,
    s.avg_motion,
    s.avg_clipped_high,
    a.ai_scene,
    a.ai_scene_similarity,
    a.ai_scene_margin,
    a.ai_scene = sc.expected_scene                                   as ai_scene_correct,
    a.zero_shot_scene,
    a.zero_shot_confidence,
    a.zero_shot_scene = sc.expected_scene                            as zero_shot_correct,
    r.clip_id is not null                                            as is_label_reference,
    a.contains_people,
    a.max_people_in_frame,
    a.ai_objects,
    c.model_versions
from {{ ref('stg_video__clips') }} as c
left join {{ ref('source_catalog') }} as sc using (source_id)
left join {{ ref('stg_video__sources') }} as src using (source_id)
left join {{ ref('int_clip_signals') }} as s using (clip_id)
left join {{ ref('int_clip_ai_labels') }} as a using (clip_id)
left join {{ ref('label_references') }} as r using (clip_id)
