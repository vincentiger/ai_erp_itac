# config.py
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# 讀取專案根目錄下的 .env
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ENV_PATH)

# =========
# System
# =========
PORT = int(os.getenv("PORT", "5000"))
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
FLASK_DEBUG = int(os.getenv("FLASK_DEBUG", "0"))
# =========
# Database (MS SQL Server)
# =========
DB_SERVER   = os.getenv("DB_SERVER", "127.0.0.1")
DB_DATABASE = os.getenv("DB_DATABASE", "")
DB_UID      = os.getenv("DB_UID", "")
DB_PWD      = os.getenv("DB_PWD", "")
DB_DRIVER   = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

# driver 有空白與大括號，要 URL encode
odbc_str = (
    f"DRIVER={DB_DRIVER};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_DATABASE};"
    f"UID={DB_UID};"
    f"PWD={DB_PWD};"
    "TrustServerCertificate=yes;"
)

SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_str)
SQLALCHEMY_TRACK_MODIFICATIONS = False




