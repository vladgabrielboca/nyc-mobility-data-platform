import os

import psycopg
from dotenv import load_dotenv


def get_connection() -> psycopg.Connection:
    """Return a psycopg connection using settings from the postgres container environment variables."""

    load_dotenv()

    db_user = os.environ.get("POSTGRES_USER")
    db_password = os.environ.get("POSTGRES_PASSWORD")
    db_name = os.environ.get("POSTGRES_DB")
    db_host = os.environ.get("POSTGRES_HOST")
    db_port = os.environ.get("POSTGRES_PORT")

    connection = psycopg.connect(
        user=db_user, password=db_password, dbname=db_name, host=db_host, port=db_port
    )

    return connection
