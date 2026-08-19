"""PostgreSQL connection plumbing for the catalog.

The connection URL is read from the `DEV_POSTGRES_URL` environment variable
(override per call with `url=`). psycopg3 connections are lazy: the real network
connection happens on first use.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from collections.abc import Iterator

import psycopg
from psycopg import Connection

DEFAULT_URL_ENV = "DEV_POSTGRES_URL"


def _resolve_url(url: str | None) -> str:
    resolved = url or os.environ.get(DEFAULT_URL_ENV)
    if not resolved:
        raise RuntimeError(f"{DEFAULT_URL_ENV} is not set; cannot connect to PostgreSQL.")
    return resolved


def get_connection(url: str | None = None, *, autocommit: bool = False) -> Connection:
    """Open a raw psycopg3 connection to PostgreSQL."""
    return psycopg.connect(_resolve_url(url), autocommit=autocommit)


@contextmanager
def connect(url: str | None = None, *, autocommit: bool = False) -> Iterator[Connection]:
    """Connection context manager: commits on success, rolls back on error, always closes."""
    conn = get_connection(url, autocommit=autocommit)
    try:
        yield conn
        if not autocommit:
            conn.commit()
    except BaseException:
        if not autocommit:
            conn.rollback()
        raise
    finally:
        conn.close()
