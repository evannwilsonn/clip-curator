select
    {{ jtext('clip_id') }}                       as clip_id,
    split_part({{ jtext('clip_id') }}, '__', 1)  as source_id,
    {{ jtext('file') }}                          as file_name,
    {{ jtext('sha256') }}                        as sha256,
    {{ jtext('codec') }}                         as codec,
    cast({{ jnum('width') }} as integer)         as width_px,
    cast({{ jnum('height') }} as integer)        as height_px,
    {{ jnum('fps') }}                            as fps,
    {{ jnum('duration_s') }}                     as duration_s,
    cast({{ jnum('bytes') }} as bigint)          as file_bytes,
    cast({{ jnum('decode_error_lines') }} as integer) as decode_errors,
    cast({{ jnum('frames_decoded') }} as integer)     as frames_decoded,
    cast({{ jnum('frames_sampled') }} as integer)     as frames_sampled,
    {{ jtext('model_versions') }}                as model_versions,
    _loaded_at
from {{ source('video', 'clips') }}
