with payment_codes as (
    select distinct payment_type
    from {{ ref('stg_taxi_trips') }}
)

select
    payment_type as payment_type_id,
    case payment_type
        when 1 then 'Credit card'
        when 2 then 'Cash'
        when 3 then 'No charge'
        when 4 then 'Dispute'
        when 5 then 'Unknown'
        when 6 then 'Voided'
        else 'Unknown'
    end as payment_type_name
from payment_codes
