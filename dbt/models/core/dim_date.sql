-- one calendar day

with date_spine as (
    select
        cast(generated_date as date) as date_day
    from generate_series(
        '2023-01-01'::date,
        '2030-12-31'::date,
        interval '1 day'
    ) as generated_date
),

final_date_table as (
    select
        date_day as date_key,
        extract(year from date_day) as calendar_year,

        cast(extract(quarter from date_day) as integer) as calendar_quarter,
        'Q' || cast(extract(quarter from date_day) as integer) as quarter_name,

        cast(extract(month from date_day) as integer) as calendar_month,
        to_char(date_day, 'TMMonth') as month_name,

        cast(extract(day from date_day) as integer) as day_of_month,
        cast(extract(isodow from date_day) as integer) as day_of_week,
        to_char(date_day, 'TMDay') as day_name,

        case
            when cast(extract(isodow from date_day) as integer) IN (6, 7) then true
            else false
        end as is_weekend

    from date_spine
)

select * from final_date_table
