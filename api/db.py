import sqlite3
import pandas as pd

DB_PATH = "db/database.db"


def fetch_data(query: str, db_path: str = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def execute_sql(query: str, db_path: str = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()
