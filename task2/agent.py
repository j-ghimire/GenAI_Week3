import os
import psycopg2
from urllib.parse import urlparse


def get_database_url() -> str:
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError('DATABASE_URL environment variable is required to execute queries.')
    return database_url


class DatabaseAgent:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or get_database_url()

    def execute(self, sql: str):
        conn = psycopg2.connect(self.database_url)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                if cursor.description:
                    columns = [col.name for col in cursor.description]
                    rows = cursor.fetchall()
                    return columns, rows
                return [], []
        finally:
            conn.close()
