with lookup_table as (
    select * from {{ ref('taxi_zone_lookup') }}
),

final_zone_table as (
    select
        location_id,
        borough,
        zone,
        service_zone,
        borough || ' - ' || zone as zone_label

    from lookup_table
)

select * from final_zone_table
