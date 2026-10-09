select
    {{ jtext('clip_a') }}              as clip_a,
    {{ jtext('clip_b') }}              as clip_b,
    {{ jnum('clip_similarity') }}      as clip_similarity,
    {{ jnum('aligned_diff') }}         as aligned_diff,
    {{ jnum('alignment_ratio') }}      as alignment_ratio
from {{ source('video', 'pairs') }}
