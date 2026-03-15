import psycopg
from server.config import config_data

def load_sql(sql_file_path: str):
    try:
        with open(sql_file_path, 'r') as f:
            sql_script = f.read()
        with psycopg.connect(
                dbname=config_data['db_name'],
                user=config_data['db_username'],
                password=config_data['db_password'],
                host=config_data['db_host'],
                port=config_data['db_port']
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql_script)
                conn.commit()
        print("SQL script executed successfully.")
    except Exception as e:
        print(f"Error executing SQL script: {e}")