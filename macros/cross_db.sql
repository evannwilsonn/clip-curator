{#- Cross-database helpers: every model runs unchanged on DuckDB (local) and Snowflake. -#}

{# Read a field from a JSON payload column (DuckDB JSON / Snowflake VARIANT) as text #}
{% macro jtext(key, col='payload') -%}{{ return(adapter.dispatch('jtext')(key, col)) }}{%- endmacro %}
{% macro duckdb__jtext(key, col) -%}({{ col }} ->> '{{ key }}'){%- endmacro %}
{% macro snowflake__jtext(key, col) -%}{{ col }}:"{{ key }}"::varchar{%- endmacro %}

{# Same, cast to a number #}
{% macro jnum(key, col='payload') -%}{{ return(adapter.dispatch('jnum')(key, col)) }}{%- endmacro %}
{% macro duckdb__jnum(key, col) -%}try_cast({{ col }} ->> '{{ key }}' as double){%- endmacro %}
{% macro snowflake__jnum(key, col) -%}try_to_double({{ col }}:"{{ key }}"::varchar){%- endmacro %}

{# Comma-separated, ordered list of distinct values #}
{% macro string_list(column, order_by) -%}{{ return(adapter.dispatch('string_list')(column, order_by)) }}{%- endmacro %}
{% macro duckdb__string_list(column, order_by) -%}string_agg({{ column }}, ', ' order by {{ order_by }}){%- endmacro %}
{% macro snowflake__string_list(column, order_by) -%}listagg({{ column }}, ', ') within group (order by {{ order_by }}){%- endmacro %}
