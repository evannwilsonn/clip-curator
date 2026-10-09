-- Every extracted clip gets exactly one decision, and every clip was checked by every rule.
select 'decisions' as check_name, (select count(*) from {{ ref('rpt_clip_decisions') }}) as n
where (select count(*) from {{ ref('rpt_clip_decisions') }}) <> (select count(*) from {{ ref('stg_video__clips') }})
union all
select 'rule checks', (select count(*) from {{ ref('fct_qc_checks') }})
where (select count(*) from {{ ref('fct_qc_checks') }})
   <> (select count(*) from {{ ref('stg_video__clips') }}) * (select count(*) from {{ ref('qc_rules') }})
