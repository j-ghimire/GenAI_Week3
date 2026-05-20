import re
from tools.db_tools import execute_read

FORBIDDEN = re.compile(r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|replace)\b", re.I)


class Validator:
    def __init__(self):
        pass

    def validate(self, sql: str) -> (bool, str):
        if not sql or not isinstance(sql, str):
            return False, "No SQL returned from LLM."

        # Detect fallback/non-SQL responses from the LLM
        if sql.strip().upper().startswith("FALLBACK"):
            return False, "LLM returned a fallback or error message instead of SQL."

        # Reject obviously non-SELECT statements and potentially destructive queries
        if FORBIDDEN.search(sql):
            return False, "Query contains forbidden or potentially destructive statements."

        # Lightweight sanity: expect a SELECT or WITH for read-only queries
        if not re.search(r"\b(select|with)\b", sql, re.I):
            return False, "LLM output does not appear to be a read-only SELECT query."

        # Basic syntax check by using EXPLAIN
        try:
            explain_sql = f"EXPLAIN {sql}"
            execute_read(explain_sql)
        except Exception as e:
            return False, f"Syntax or execution error: {e}"

        return True, "OK"
