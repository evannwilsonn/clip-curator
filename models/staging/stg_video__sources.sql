select
    {{ jtext('source_id') }}   as source_id,
    {{ jtext('url') }}         as source_url,
    {{ jtext('license') }}     as license,
    cast({{ jnum('bytes') }} as bigint) as source_bytes,
    {{ jtext('sha256') }}      as sha256
from {{ source('video', 'sources') }}
