"""
Stage 2 — Row-level quality rules for taxi batches.

Pure functions: a batch (pandas DataFrame, canonical column names) goes in,
(valid rows, rejected rows, per-rule violation counts) come out. No DB, no files.
"""

import pandas as pd

# Rules are data: name -> function returning the "row passes this rule" T/F column.
# split_valid_rejected derives both the combined mask and the per-rule counts from
# this single definition, so the counts can never disagree with the actual split.
RULES = {
    "pickup_before_dropoff": lambda df: df["pickup_datetime"] < df["dropoff_datetime"],
    "trip_distance_positive": lambda df: df["trip_distance"] > 0,
    "fare_amount_non_negative": lambda df: df["fare_amount"] >= 0,
    # Null passenger_count means the vendor did not report it (2.3% of Jan 2023
    # rows): missing != invalid, so nulls pass and only reported values are checked.
    "passenger_count_sane": lambda df: (
        df["passenger_count"].between(1, 6) | df["passenger_count"].isna()
    ),
}


def split_valid_rejected(batch):
    """Split a batch into (valid, rejected, {rule_name: violations in this batch})."""

    rule_results = pd.DataFrame({name: fn(batch) for name, fn in RULES.items()})
    batch_counts = {name: int(n) for name, n in (~rule_results).sum().items()}
    is_valid = rule_results.all(axis=1)

    return batch[is_valid], batch[~is_valid], batch_counts
