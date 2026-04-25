"""
reset_db.py — resets the public DB schema and reapplies schema.sql.

Runs INDEPENDENTLY from the Flask application:
    python -m server.app.utils.reset_db
    python -m server.app.utils.reset_db --no-schema # only DROP/CREATE schema
    python -m server.app.utils.reset_db --help
    python -m server.app.utils.reset_db --schemas <schemas path>

Does not import create_app, Flask or SQLAlchemy — uses psycopg directly,
so can be run before application initialization (e.g. in CI or scripts).
"""

import argparse
import sys
from pathlib import Path

# ── resolve project root so the script works regardless of cwd ───────────────
PROJECT_ROOT = Path(__file__).resolve().parents[3]   # .../PPDB-team4/
SCHEMA_FILE  = PROJECT_ROOT / "server" / "sql" / "schema.sql"


def _get_connection():
    """Opens a raw psycopg connection using server/config.py values."""
    try:
        import psycopg
    except ImportError:
        print("[reset_db] ERROR: psycopg not installed. Run: pip install psycopg", file=sys.stderr)
        sys.exit(1)

    from server.config import config_data

    return psycopg.connect(
        dbname=config_data["db_name"],
        user=config_data["db_username"],
        password=config_data["db_password"],
        host=config_data["db_host"],
        port=config_data["db_port"],
        autocommit=False,
    )


def reset_schema(conn) -> None:
    """Drops and recreates the public schema (wipes all tables and data)."""
    print("[reset_db] Dropping public schema...")
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE")
        cur.execute("CREATE SCHEMA public")
        cur.execute("GRANT ALL ON SCHEMA public TO public")
    conn.commit()
    print("[reset_db] Schema reset complete.")


def apply_schemas(conn, schema_files) -> None:
    """Runs multiple SQL schema files in order."""
    for schema_file in schema_files:
        if not schema_file.exists():
            print(f"[reset_db] ERROR: schema file not found: {schema_file}", file=sys.stderr)
            sys.exit(1)

        sql = schema_file.read_text(encoding="utf-8")
        print(f"[reset_db] Applying {schema_file.relative_to(PROJECT_ROOT)}...")
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print("[reset_db] All schemas applied successfully.")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Reset the PostgreSQL database schema for the PPDB project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python -m server.app.utils.reset_db\n"
            "  python -m server.app.utils.reset_db --schemas schema.sql seed.sql\n"
            "  python -m server.app.utils.reset_db --no-schema\n"
        ),
    )

    parser.add_argument(
        "--no-schema",
        action="store_true",
        help="Skip applying schema.sql after the reset (leaves DB empty).",
    )

    parser.add_argument(
        "--schemas",
        nargs="+",
        help="List of schema files to apply (relative to project root).",
    )

    args = parser.parse_args(argv)

    try:
        conn = _get_connection()
    except Exception as e:
        print(f"[reset_db] ERROR: could not connect to database: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        reset_schema(conn)

        if not args.no_schema:
            if args.schemas:
                schema_files = [PROJECT_ROOT / s for s in args.schemas]
            else:
                schema_files = [SCHEMA_FILE]

            apply_schemas(conn, schema_files)

    except Exception as e:
        conn.rollback()
        print(f"[reset_db] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    print("[reset_db] Done.")


if __name__ == "__main__":
    main()