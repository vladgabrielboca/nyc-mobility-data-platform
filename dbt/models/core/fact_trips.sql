{{
    config(
        materialized='incremental',
        incremental_strategy='delete+insert',
        unique_key=['source_year', 'source_month']
    )
}}

select
    trip_id,
    vendor_id,
    pickup_datetime,
    dropoff_datetime,
    trip_duration_minutes,
    pickup_location_id,
    dropoff_location_id,
    rate_code_id,
    payment_type as payment_type_id,
    passenger_count,
    trip_distance,
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

from {{ ref('stg_taxi_trips') }}

{% if is_incremental() %}
    where (source_year, source_month) not in (
        select distinct source_year, source_month
        from {{ this }}
    )
{% endif %}
