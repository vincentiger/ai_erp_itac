import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    conn_str = (
        f"DRIVER={os.getenv('DB_DRIVER')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_UID')};"
        f"PWD={os.getenv('DB_PWD')};"
        "Timeout=5;"
    )
    return pyodbc.connect(conn_str)
