import os
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # default local fallback
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/appdb"

engine = create_engine(DATABASE_URL, future=True)


def execute_read(sql: str, params: dict = None) -> List[Dict[str, Any]]:
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        rows = [dict(row._mapping) for row in result.fetchall()]
    return rows


def get_schema_sql() -> str:
    # Return the seed file contents if present
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(base, ".."))
    path = os.path.join(root, "sql", "seed.sql")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""
