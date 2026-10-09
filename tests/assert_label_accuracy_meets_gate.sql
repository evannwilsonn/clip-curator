-- Quality gate: few-shot scene labels must match what the source video shows at least min_label_accuracy of the time.
select method, accuracy
from {{ ref('rpt_label_quality') }}
where method like 'few-shot%'
  and accuracy < {{ var('min_label_accuracy') }}
