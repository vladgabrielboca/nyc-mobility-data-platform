import argparse
from datetime import datetime

from dateutil.relativedelta import relativedelta

from nyc_mobility.common.db import get_connection
from nyc_mobility.orchestration.monthly import run_monthly_ingestion


def policy(year, month):
    print(f"[RUNNER] Running policy for {year}-{month:02d}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                run_monthly_ingestion(cur, year, month)
            except Exception as e:
                print(f"[RUNNER] {year}---{month} failed: {e}")
                return

    print(f"[RUNNER] {year}-{month:02d} completed")


def generate_months(start_str, end_str):
    start_date = datetime.strptime(start_str, "%Y-%m")
    end_date = datetime.strptime(end_str, "%Y-%m")

    current = start_date
    while current <= end_date:
        yield current.year, current.month
        current += relativedelta(months=1)


def runner():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start", type=str, required=True, help="Start date in format YYYY-MM"
    )
    parser.add_argument(
        "--end", type=str, required=True, help="End date in format YYYY-MM"
    )

    args = parser.parse_args()

    print(f"Starting runner for {args.start} to {args.end}")

    for year, month in generate_months(args.start, args.end):
        policy(year, month)

    print("\n[SUCCESS] All months have been processed")


if __name__ == "__main__":
    runner()
    print("Done.")
