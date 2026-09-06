-- grain: one row per pickup-dropoff

with route as (
    select
        pickup_location_id,
        dropoff_location_id,
        count(*) as trips,
        sum(total_amount) as revenue,
        avg(trip_duration_minutes) as avg_duration
    from {{ ref('fact_trips') }}
    group by 1, 2
)

select
    r.pickup_location_id,
    r.dropoff_location_id,
    r.trips,
    r.revenue,
    r.avg_duration,
    pz.borough as pickup_borough,
    pz.zone as pickup_zone,
    pz.service_zone as pickup_service_zone,
    pz.zone_label as pickup_zone_label,
    dz.borough as dropoff_borough,
    dz.zone as dropoff_zone,
    dz.service_zone as dropoff_service_zone,
    dz.zone_label as dropoff_zone_label

from route r
left join {{ ref('dim_zone') }} dz on dz.location_id = r.dropoff_location_id
left join {{ ref('dim_zone') }} pz on pz.location_id = r.pickup_location_id
