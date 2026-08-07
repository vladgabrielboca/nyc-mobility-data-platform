"""
This file contains the functions for managing the ingestion manifest table in the database.
"""


def has_successful_ingestion(cursor, source: str, year: int, month: int) -> bool:
    """
    Check if there is a succesful ingestion for the given source, year, and month in the ops.ingestion_manifest table.
    """

    query = """
        SELECT COUNT(*) FROM ops.ingestion_manifest
        WHERE source = %s AND year = %s AND month = %s AND status = 'success'
    """

    cursor.execute(query, (source, year, month))
    count = cursor.fetchone()[0]
    return count > 0


def start_ingestion_attempt(cursor, source: str, year: int, month: int) -> int:
    """
    Start an ingestion attempt having the status = 'pending' and started_at = now()
    """

    query = """
        INSERT INTO ops.ingestion_manifest (source, year, month, status, started_at)
        VALUES (%s, %s, %s, 'pending', NOW())
        RETURNING id;
    """

    cursor.execute(query, (source, year, month))
    return cursor.fetchone()[0]


def mark_ingestion_success(
    cursor, manifest_id: int, file_checksum: str, row_count: int
) -> None:
    """
    Mark given ingestion with 'success' while adding file_checksum and row_count
    """

    query = """
        UPDATE ops.ingestion_manifest
        SET 
            file_checksum = %s,
            row_count = %s,
            status = 'success',
            finished_at = NOW()
        WHERE
            id = %s
    """

    cursor.execute(query, (file_checksum, row_count, manifest_id))


def mark_ingestion_failure(cursor, manifest_id: int, error_message: str) -> None:
    """
    Mark given ingestion with 'failure' while adding an error message
    """

    query = """
        UPDATE ops.ingestion_manifest
        SET
            error_message = %s,
            status = 'failed',
            finished_at = NOW()
        WHERE
            id = %s
    """

    cursor.execute(query, (error_message, manifest_id))
