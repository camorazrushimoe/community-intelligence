"""Shared pytest fixtures."""

import os

import psycopg
import pytest

from catalog.migrate import apply_migrations


@pytest.fixture
def db_connection():
    """A live PostgreSQL connection with the catalog schema applied.

    Skips the test when ``DEV_POSTGRES_URL`` is unset or the database is
    unreachable, so the unit suite still runs without a database while
    integration tests exercise the real Postgres when it is available.
    """
    url = os.environ.get("DEV_POSTGRES_URL")
    if not url:
        pytest.skip("DEV_POSTGRES_URL not set")

    try:
        conn = psycopg.connect(url, autocommit=True)
        conn.execute("SELECT 1")
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"PostgreSQL unavailable: {exc}")

    try:
        apply_migrations(url)
        yield conn
    finally:
        conn.close()
