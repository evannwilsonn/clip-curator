select
    {{ jtext('clip_id') }}                          as clip_id,
    cast({{ jnum('frame_index') }} as integer)      as frame_index,
    {{ jnum('ts_s') }}                              as ts_s,
    {{ jnum('brightness') }}                        as brightness,
    {{ jnum('contrast') }}                          as contrast,
    {{ jnum('sharpness') }}                         as sharpness,
    {{ jnum('pct_clipped_high') }}                  as pct_clipped_high,
    {{ jnum('pct_crushed_low') }}                   as pct_crushed_low,
    {{ jnum('motion') }}                            as motion,
    {{ jtext('dhash') }}                            as dhash
from {{ source('video', 'frames') }}
