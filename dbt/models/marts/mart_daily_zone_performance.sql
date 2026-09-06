-- grain: one row per date and pickup zone

with taxi_trips_data as (
    select
        pickup_datetime::date as date_key,
        pickup_location_id,
        count(*) as trips,
        sum(passenger_count) as passengers,
        sum(total_amount) as revenue,
        avg(trip_distance) as avg_distance
    from {{ ref('fact_trips') }}
    group by 1, 2
)

select
    ttd.date_key,
    ttd.pickup_location_id,
    ttd.trips,
    ttd.passengers,
    ttd.revenue,
    ttd.avg_distance,
    dz.borough,
    dz.zone,
    dz.service_zone,
    dz.zone_label
from taxi_trips_data ttd
left join {{ ref('dim_zone') }} dz on ttd.pickup_location_id = dz.location_id
