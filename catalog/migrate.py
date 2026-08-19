"""Apply forward-only SQL migrations from `migrations/` in filename order.

Each `*.sql` file is applied exactly once; applied filenames are tracked in a
`schema_migrations` table so re-running is a no-op. Each migration file must
contain a single SQL statement (the v1 catalog migration does).

Usage:
    python -m catalog.migrate [--url "$DEV_POSTGRES_URL"]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from catalog.db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def apply_migrations(url: str | None = None) -> list[str]:
    """Apply any pending migrations; returns the filenames applied this run."""
    applied: list[str] = []
    with connect(url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    filename   text PRIMARY KEY,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
            for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
                cur.execute(
                    "SELECT 1 FROM schema_migrations WHERE filename = %s",
                    (path.name,),
                )
                if cur.fetchone():
                    continue
                sql = path.read_text().strip()
                if sql.endswith(";"):
                    sql = sql[:-1]
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (path.name,),
                )
                applied.append(path.name)
    return applied


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply database migrations.")
    parser.add_argument(
        "--url", default=None, help="PostgreSQL URL (default: DEV_POSTGRES_URL)"
    )
    args = parser.parse_args()
    applied = apply_migrations(args.url)
    if applied:
        for name in applied:
            print(f"applied: {name}")
    else:
        print("no pending migrations")


if __name__ == "__main__":
    main()
