# backend/utils/db.py
import os
from dotenv import load_dotenv
import pyodbc

load_dotenv()

def get_db_conn():
    conn_str = (
        f"DRIVER={os.getenv('DB_DRIVER')};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_DATABASE')};"
        f"UID={os.getenv('DB_UID')};"
        f"PWD={os.getenv('DB_PWD')};"
        "TrustServerCertificate=yes;"
        "Timeout=5;"
    )
    return pyodbc.connect(conn_str)
