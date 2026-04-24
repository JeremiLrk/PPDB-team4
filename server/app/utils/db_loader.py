import psycopg
from pathlib import Path
from server.config import config_data

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _resolve_sql_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def load_sql(sql_file_paths: list[str]):
    try:
        with psycopg.connect(
            dbname=config_data['db_name'],
            user=config_data['db_username'],
            password=config_data['db_password'],
            host=config_data['db_host'],
            port=config_data['db_port']
        ) as conn:
            with conn.cursor() as cur:
                for path in sql_file_paths:
                    resolved = _resolve_sql_path(path)
                    print(f"Executing {path}...")
                    with open(resolved, 'r', encoding='utf-8') as f:
                        sql_script = f.read()
                    cur.execute(sql_script)

            conn.commit()

        print("All SQL scripts executed successfully.")

    except Exception as e:
        print(f"Error executing SQL scripts: {e}")
        raise
