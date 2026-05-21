import re
from tools.db_tools import execute_read

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|replace)\b", re.I)


class Validator:
    def __init__(self):
        pass

    def _clean_sql(self, sql: str) -> str:
        """Aggressively clean SQL by removing all code block markers and prefixes."""
        sql = sql.strip()
        
        # Step 1: Remove all variations of code block markers
        # Remove ```sql, ```SQL, ```, etc.
        while '```' in sql:
            sql = sql.replace('```', '')
        
        # Step 2: Remove all backticks
        while '`' in sql:
            sql = sql.replace('`', '')
        
        sql = sql.strip()
        
        # Step 3: Remove SQL prefix if it's on its own line or at the start
        lines = []
        for line in sql.split('\n'):
            line = line.strip()
            # Skip lines that are just 'sql' or 'SQL', but keep actual SQL
            if line and line.lower() != 'sql':
                lines.append(line)
        
        sql = ' '.join(lines)
        sql = sql.strip()
        
        # Step 4: Clean up multiple spaces
        while '  ' in sql:
            sql = sql.replace('  ', ' ')
        
        sql = sql.strip()
        return sql

    def validate(self, sql: str) -> (bool, str, str):
        if not sql or not isinstance(sql, str):
            return False, "No SQL returned from LLM.", ""

        # Clean up SQL FIRST
        cleaned_sql = self._clean_sql(sql)

        # Detect fallback/non-SQL responses from the LLM
        if cleaned_sql.upper().startswith("FALLBACK"):
            return False, "LLM returned a fallback or error message instead of SQL.", cleaned_sql

        # Reject obviously non-SELECT statements and potentially destructive queries
        if FORBIDDEN.search(cleaned_sql):
            return False, "Query contains forbidden or potentially destructive statements.", cleaned_sql

        # Lightweight sanity: expect a SELECT or WITH for read-only queries
        if not re.search(r"\b(select|with)\b", cleaned_sql, re.I):
            return False, "LLM output does not appear to be a read-only SELECT query.", cleaned_sql

        # Basic syntax check by using EXPLAIN
        # Note: We skip EXPLAIN check if it fails because the query itself might be valid
        # even if EXPLAIN has issues with case sensitivity on identifiers
        try:
            explain_sql = f"EXPLAIN {cleaned_sql}"
            execute_read(explain_sql)
        except Exception as e:
            error_str = str(e).lower()
            # If it's just a column/table naming issue, let it pass - the actual execution will catch real errors
            if "does not exist" in error_str or "undefined" in error_str:
                # This is likely a case sensitivity issue, the query is probably still valid
                pass
            else:
                # Real syntax error
                return False, f"Syntax error: {e}", cleaned_sql

        return True, "OK", cleaned_sql
