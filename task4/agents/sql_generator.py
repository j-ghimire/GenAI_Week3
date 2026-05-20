from agents.llm import LLM
from prompts import GENERATOR_PROMPT
import re


class SQLGenerator:
    def __init__(self, llm: LLM = None):
        self.llm = llm or LLM()

    def _local_fallback(self, user_query: str) -> str:
        q = user_query.lower()
        # top N customers by total payments
        m = re.search(r"top\s*(\d+)", q)
        n = int(m.group(1)) if m else 5
        if "customers" in q and ("payment" in q or "payments" in q or "total payment" in q):
            return (
                "SELECT c.customer_id, (c.first_name || ' ' || c.last_name) AS customer_name, "
                "SUM(p.amount) AS total_payments FROM customers c "
                "JOIN payments p ON p.customer_id = c.customer_id "
                "GROUP BY c.customer_id, customer_name ORDER BY total_payments DESC LIMIT %d;" % n
            )

        # list products
        if "products" in q or "list all products" in q:
            return "SELECT * FROM products LIMIT 100;"

        # generic fallback: try customers table
        return "SELECT * FROM customers LIMIT 50;"

    def generate(self, plan: str, schema: str = "", user_query: str = "") -> str:
        system = GENERATOR_PROMPT
        user = f"Schema:\n{schema}\n\nPlan:\n{plan}\n\nReturn a single valid PostgreSQL SELECT query only (no explanation)."
        sql = self.llm.generate(system=system, user=user, temperature=0.0, max_tokens=1024)

        # If LLM returned a fallback or plan itself is a fallback, use a local heuristic generator
        if (isinstance(plan, str) and plan.strip().upper().startswith("FALLBACK")) or (
            isinstance(sql, str) and sql.strip().upper().startswith("FALLBACK")
        ):
            return self._local_fallback(user_query or plan)

        return sql
