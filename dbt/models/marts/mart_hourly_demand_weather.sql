with trip_demand_per_hour as (
    select
        date_trunc('hour', pickup_datetime) as hour,
        count(*) as trips,
        sum(total_amount) as revenue
    from {{ ref('fact_trips') }}
    group by 1
)

select
    tdph.hour,
    tdph.trips,
    tdph.revenue,
    tdph.revenue / tdph.trips as avg_fare_per_trip,
    fw.temperature_2m,
    fw.precipitation,
    fw.windspeed_10m
from trip_demand_per_hour tdph
left join {{ ref('fact_weather') }} fw on fw.time = tdph.hour
