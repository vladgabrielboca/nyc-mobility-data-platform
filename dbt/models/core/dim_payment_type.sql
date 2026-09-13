with payment_codes (payment_type_id, payment_type_name) as (
    values
        (0, 'Unknown'),
        (1, 'Credit card'),
        (2, 'Cash'),
        (3, 'No charge'),
        (4, 'Dispute'),
        (5, 'Unknown'),
        (6, 'Voided')
)

select payment_type_id, payment_type_name from payment_codes
