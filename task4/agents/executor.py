from typing import Any, List, Dict
from tools.db_tools import execute_read


def execute_query(sql: str) -> List[Dict[str, Any]]:
    """Execute a validated read-only SQL query and return rows as list of dicts."""
    # Final defensive cleaning - remove any remaining formatting artifacts
    sql = sql.strip()
    
    # Remove all backticks and code block markers
    sql = sql.replace('```', '')
    sql = sql.replace('`', '')
    
    # If SQL contains newlines with non-SQL text, clean it
    lines = []
    for line in sql.split('\n'):
        line = line.strip()
        # Skip empty lines and lines with just 'sql'
        if line and line.lower() != 'sql':
            lines.append(line)
    
    sql = ' '.join(lines)
    
    # Find the start of actual SQL (SELECT or WITH keyword)
    for keyword in ['SELECT', 'WITH', 'select', 'with']:
        if keyword in sql:
            idx = sql.find(keyword)
            if idx > 0:
                sql = sql[idx:]
            break
    
    sql = sql.strip()
    
    # Clean up multiple spaces
    while '  ' in sql:
        sql = sql.replace('  ', ' ')
    
    results = execute_read(sql)
    return results
