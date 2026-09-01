select
    t.pickup_datetime::date as pickup_date_key,
    t.pickup_location_id as pickup_zone_id,
    t.dropoff_location_id as dropoff_zone_id,
    t.payment_type as payment_type_id,
    t.trip_distance,
    t.fare_amount,
    t.dropoff_datetime - t.pickup_datetime as trip_duration,
    t.vendor_id,
    t.source_year,
    t.source_month

from {{ ref('stg_taxi_trips') }} as t
