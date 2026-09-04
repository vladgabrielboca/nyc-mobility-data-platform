with source_data as (
    select * from {{ source('raw', 'yellow_taxi_trips') }}
)

select
    vendor_id,
    pickup_datetime::TIMESTAMP,
    dropoff_datetime::TIMESTAMP,
    {{ dbt.datediff("pickup_datetime", "dropoff_datetime", "minute") }} AS trip_duration_minutes,
    passenger_count::INTEGER,
    trip_distance,
    rate_code_id,
    store_and_fwd_flag::BOOLEAN,
    pickup_location_id,
    dropoff_location_id,
    payment_type,
    fare_amount,
    extra,
    mta_tax,
    tip_amount,
    tolls_amount,
    improvement_surcharge,
    total_amount,
    congestion_surcharge,
    airport_fee,
    source_year,
    source_month
from source_data
