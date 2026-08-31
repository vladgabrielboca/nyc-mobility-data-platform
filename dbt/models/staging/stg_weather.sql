with source_data as (
    select * from {{ source('raw', 'weather_hourly') }}
)

select
    time::timestamp as time,
    temperature_2m,
    precipitation,
    windspeed_10m,
    source_year,
    source_month
from source_data
