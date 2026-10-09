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
    a.ai_scene_confidence,
    a.ai_scene = sc.expected_scene                                   as ai_scene_matches_source,
    a.ai_scene_confidence < {{ var('min_label_confidence') }}        as needs_human_label,
    case
        when a.ai_scene is null                                       then 'no label'
        when a.ai_scene = sc.expected_scene                           then 'confirmed'
        when a.ai_scene_confidence < {{ var('min_label_confidence') }} then 'low confidence'
        else 'disagrees with source'
    end                                                              as label_status,
    a.contains_people,
    a.max_people_in_frame,
    a.ai_objects,
    c.model_versions
from {{ ref('stg_video__clips') }} as c
left join {{ ref('source_catalog') }} as sc using (source_id)
left join {{ ref('stg_video__sources') }} as src using (source_id)
left join {{ ref('int_clip_signals') }} as s using (clip_id)
left join {{ ref('int_clip_ai_labels') }} as a using (clip_id)
