import os

import duckdb

from nyc_mobility.common.db import get_connection_string

OUTPUT_DIR = "data/export"


def export_marts():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")

    # Inject the connection string directly
    pg_conn_str = get_connection_string()
    con.execute(f"ATTACH '{pg_conn_str}' AS pg (TYPE POSTGRES, READ_ONLY);")
    con.execute("USE pg;")

    # Get list of tables in marts schema
    tables = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'marts' AND table_type = 'BASE TABLE';
    """).fetchall()

    for (table_name,) in tables:
        print(f"Found table: {table_name}")

    for (table_name,) in tables:
        output_path = os.path.join(OUTPUT_DIR, f"{table_name}.parquet")
        print(f"Exporting marts.{table_name}...")

        # Stream Postgres directly into Snappy-compressed Parquet
        con.execute(f"""
                COPY (SELECT * FROM marts.{table_name})
                TO '{output_path}'
                (FORMAT PARQUET, COMPRESSION 'SNAPPY', ROW_GROUP_SIZE 100000);
            """)

        row = con.execute(f"SELECT count(*) FROM marts.{table_name}").fetchone()
        count = row[0] if row else 0
        print(f"Finished {table_name}: {count} rows")


if __name__ == "__main__":
    export_marts()
