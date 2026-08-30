import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

# True once real connection details are present, so the app can fall back
# to the in-memory repositories when they're not (e.g. a fresh checkout with
# no .env yet).
HAS_DATABASE = all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD])
