from uuid import uuid4

import psycopg
from psycopg.types.json import Jsonb

from rag_hopital.config import settings


def init_schema():
    """Create ETL logging tables if they do not exist."""

    with psycopg.connect(settings.postgres_url) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_runs (
                run_id UUID PRIMARY KEY,
                stage TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running',
                started_at TIMESTAMPTZ DEFAULT NOW(),
                finished_at TIMESTAMPTZ,
                configuration JSONB,
                summary JSONB,
                error_message TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS etl_events (
                id BIGSERIAL PRIMARY KEY,
                run_id UUID REFERENCES etl_runs(run_id),
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                step TEXT NOT NULL,
                status TEXT NOT NULL,
                document TEXT,
                input_count INTEGER,
                output_count INTEGER,
                details JSONB,
                error_message TEXT
            )
        """)


def start_run(stage, configuration=None):
    """Register a new ETL execution."""

    init_schema()
    run_id = str(uuid4())

    with psycopg.connect(settings.postgres_url) as conn:
        conn.execute(
            """
            INSERT INTO etl_runs
                (run_id, stage, configuration)
            VALUES (%s, %s, %s)
            """,
            (run_id, stage, Jsonb(configuration or {})),
        )

    return run_id


def log_event(
    run_id,
    step,
    status,
    document=None,
    input_count=None,
    output_count=None,
    details=None,
    error_message=None,
):
    """Record a processing event."""

    with psycopg.connect(settings.postgres_url) as conn:
        conn.execute(
            """
            INSERT INTO etl_events
            (run_id, step, status, document,
             input_count, output_count, details, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                step,
                status,
                document,
                input_count,
                output_count,
                Jsonb(details or {}),
                error_message,
            ),
        )


def finish_run(run_id, status, summary=None, error_message=None):
    """Record the outcome of an ETL execution."""

    with psycopg.connect(settings.postgres_url) as conn:
        conn.execute(
            """
            UPDATE etl_runs
            SET status = %s,
                finished_at = NOW(),
                summary = %s,
                error_message = %s
            WHERE run_id = %s
            """,
            (
                status,
                Jsonb(summary or {}),
                error_message,
                run_id,
            ),
        )