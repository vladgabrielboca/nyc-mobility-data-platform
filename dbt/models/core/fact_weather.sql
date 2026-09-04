select
    time,
    time::date as date_key,
    cast(extract(hour from time) as integer) as hour,
    temperature_2m,
    precipitation,
    windspeed_10m,
    source_year,
    source_month
from {{ ref('stg_weather') }}
