-- pq.read_schema('data/raw/taxi/2023/01/trips.parquet')
-- VendorID: int64
-- tpep_pickup_datetime: timestamp[us]
-- tpep_dropoff_datetime: timestamp[us]
-- passenger_count: double
-- trip_distance: double
-- RatecodeID: double
-- store_and_fwd_flag: string
-- PULocationID: int64
-- DOLocationID: int64
-- payment_type: int64
-- fare_amount: double
-- extra: double
-- mta_tax: double
-- tip_amount: double
-- tolls_amount: double
-- improvement_surcharge: double
-- total_amount: double
-- congestion_surcharge: double
-- airport_fee: double


CREATE TABLE IF NOT EXISTS raw.yellow_taxi_trips (
    vendor_id BIGINT,
    pickup_datetime TIMESTAMP,
    dropoff_datetime TIMESTAMP,
    passenger_count DOUBLE PRECISION,
    trip_distance DOUBLE PRECISION,
    rate_code_id DOUBLE PRECISION,
    store_and_fwd_flag TEXT,
    pickup_location_id BIGINT,
    dropoff_location_id BIGINT,
    payment_type BIGINT,
    fare_amount DOUBLE PRECISION,
    extra DOUBLE PRECISION,
    mta_tax DOUBLE PRECISION,
    tip_amount DOUBLE PRECISION,
    tolls_amount DOUBLE PRECISION,
    improvement_surcharge DOUBLE PRECISION,
    total_amount DOUBLE PRECISION,
    congestion_surcharge DOUBLE PRECISION,
    airport_fee DOUBLE PRECISION,
    source_year INTEGER,
    source_month INTEGER,
    loaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.weather_hourly (
    time TEXT,
    temperature_2m DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    windspeed_10m DOUBLE PRECISION,
    source_year INTEGER,
    source_month INTEGER,
    loaded_at TIMESTAMPTZ DEFAULT NOW()
);
