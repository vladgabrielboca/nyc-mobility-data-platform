-- grain: one row per month

with taxi_trips_monthly_data as (
    select
        date_trunc('month', pickup_datetime) as month,
        count(*) as trips,
        sum(total_amount) as revenue,
        sum(passenger_count) as total_passengers,
        avg(fare_amount) as avg_fare,
        avg(trip_distance) as avg_distance,
        avg(trip_duration_minutes) as avg_duration_minutes,
        sum(tip_amount) as total_tips,
        count(distinct pickup_location_id) as active_zones
    from {{ ref('fact_trips') }}
    group by 1
)

select
    t.month,
    t.trips,
    t.revenue,
    t.total_passengers,
    t.avg_fare,
    t.avg_distance,
    t.avg_duration_minutes,
    t.total_tips,
    t.active_zones,
    d.month_name,
    d.calendar_year
from taxi_trips_monthly_data t
left join {{ ref('dim_date') }} d on d.date_key = t.month::date
