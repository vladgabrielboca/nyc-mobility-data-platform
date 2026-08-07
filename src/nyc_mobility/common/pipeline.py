import psycopg

def start_pipeline_run(cursor, run_type: str, year: int, month: int) -> int:
    """Insert a new row with status = 'pending', and returning id."""

    query = """
        INSERT INTO ops.pipeline_run (run_type, year, month, status, started_at)
        VALUES (%s, %s, %s, 'pending', NOW())
        RETURNING id;
    """

    cursor.execute(query, (run_type, year, month))
    return cursor.fetchone()[0]

def mark_pipeline_run_success(cursor, pipeline_id: int) -> None:
    """Update status = 'success', finished_at = NOW()."""

    query = """
        UPDATE op.pipeline_runs
        SET
            status = 'success',
            finished_at = NOW()
        WHERE
            id = %s
    """
    
    cursor.execute(query, (pipeline_id,))

def mark_pipeline_run_failure(cursor, pipeline_id: int) -> None:
    """Update status = 'failed', finished_at = NOW()."""

    query = """
        UPDATE op.pipeline_runs
        SET
            status = 'failed',
            finished_at = NOW()
        WHERE
            id = %s
    """

    cursor.execute(query, (pipeline_id,))