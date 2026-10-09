{#- Generic test: every non-null value sits inside a plausible range. Catches unit and parsing errors. -#}
{% test value_between(model, column_name, min_value=none, max_value=none) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and (
    {%- if min_value is not none %} {{ column_name }} < {{ min_value }}{% endif %}
    {%- if min_value is not none and max_value is not none %} or{% endif %}
    {%- if max_value is not none %} {{ column_name }} > {{ max_value }}{% endif %}
  )
{% endtest %}
