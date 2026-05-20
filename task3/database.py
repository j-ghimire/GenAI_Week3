import os
from typing import Optional, Tuple, List
import psycopg2

DATABASE_URL_ENV = 'DATABASE_URL'


def get_database_url() -> str:
    url = os.environ.get(DATABASE_URL_ENV)
    if not url:
        raise EnvironmentError(f'{DATABASE_URL_ENV} is required')
    return url


def execute_query(sql: str, database_url: Optional[str] = None, fetch: bool = True) -> Tuple[List[str], List[tuple], Optional[str]]:
    url = database_url or get_database_url()
    conn = psycopg2.connect(url)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if fetch and cur.description:
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
            else:
                columns = []
                rows = []
            conn.commit()
            return columns, rows, None
    except Exception as e:
        conn.rollback()
        return [], [], str(e)
    finally:
        conn.close()
