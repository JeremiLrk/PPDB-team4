import psycopg
from server.config import config_data

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
                    print(f"Executing {path}...")
                    with open(path, 'r') as f:
                        sql_script = f.read()
                    cur.execute(sql_script)

            conn.commit()

        print("All SQL scripts executed successfully.")

    except Exception as e:
        print(f"Error executing SQL scripts: {e}")