select
    {{ jtext('clip_a') }}              as clip_a,
    {{ jtext('clip_b') }}              as clip_b,
    {{ jnum('clip_similarity') }}      as clip_similarity,
    {{ jnum('motion_corr') }}          as motion_corr,
    {{ jnum('brightness_corr') }}      as brightness_corr
from {{ source('video', 'pairs') }}
