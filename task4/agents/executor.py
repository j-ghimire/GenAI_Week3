from typing import Any, List, Dict
from tools.db_tools import execute_read


def execute_query(sql: str) -> List[Dict[str, Any]]:
    """Execute a validated read-only SQL query and return rows as list of dicts."""
    results = execute_read(sql)
    return results
