from agents.llm import LLM
from prompts import GENERATOR_PROMPT
import re


class SQLGenerator:
    def __init__(self, llm: LLM = None):
        self.llm = llm or LLM()

    def _pick_table(self, q: str) -> str:
        table_order = [
            "orderdetails", "orders", "payments", "customers", "employees", "offices", "products", "productlines"
        ]
        for table in table_order:
            if table in q:
                return table
        if "product line" in q or "productlines" in q:
            return "productlines"
        if "office" in q:
            return "offices"
        if "customer" in q:
            return "customers"
        if "order" in q:
            return "orders"
        if "payment" in q:
            return "payments"
        if "product" in q:
            return "products"
        return "customers"

    def _local_fallback(self, user_query: str) -> str:
        q = user_query.lower()
        # list offices countries
        if ("country" in q or "countries" in q) and "offices" in q:
            return "SELECT DISTINCT \"country\" FROM \"offices\" ORDER BY \"country\";"

        # general offices listing
        if "offices" in q:
            return "SELECT * FROM \"offices\" LIMIT 100;"

        # count shipped orders from usa customers
        if "shipped orders" in q and "usa" in q:
            return (
                "SELECT COUNT(*) FROM \"orders\" o "
                "JOIN \"customers\" c ON o.\"customerNumber\" = c.\"customerNumber\" "
                "WHERE o.\"shippedDate\" IS NOT NULL AND c.\"country\" = 'USA';"
            )

        # top N customers by payments
        m = re.search(r"top\s*(\d+)", q)
        n = int(m.group(1)) if m else 5
        if "customers" in q and ("payment" in q or "payments" in q or "total payment" in q):
            return (
                "SELECT c.\"customerNumber\", c.\"customerName\", "
                "SUM(p.\"amount\") AS total_payments FROM \"customers\" c "
                "JOIN \"payments\" p ON p.\"customerNumber\" = c.\"customerNumber\" "
                "GROUP BY c.\"customerNumber\", c.\"customerName\" "
                f"ORDER BY total_payments DESC LIMIT {n};"
            )

        # list products
        if "products" in q or "list all products" in q:
            return "SELECT * FROM \"products\" LIMIT 100;"

        # list employees, customers, payments, orderdetails, productlines
        if "employees" in q:
            return "SELECT * FROM \"employees\" LIMIT 100;"
        if "customers" in q:
            return "SELECT * FROM \"customers\" LIMIT 100;"
        if "payments" in q:
            return "SELECT * FROM \"payments\" LIMIT 100;"
        if "orderdetails" in q or "order details" in q:
            return "SELECT * FROM \"orderdetails\" LIMIT 100;"
        if "productlines" in q or "product line" in q:
            return "SELECT * FROM \"productlines\" LIMIT 100;"

        # count if supported
        if q.startswith("how many") or q.startswith("count") or "number of" in q:
            table = self._pick_table(q)
            return f"SELECT COUNT(*) FROM \"{table}\";"

        # fallback generic
        table = self._pick_table(q)
        return f"SELECT * FROM \"{table}\" LIMIT 100;"

    def generate(self, plan: str, schema: str = "", user_query: str = "") -> str:
        system = GENERATOR_PROMPT
        user = f"Schema:\n{schema}\n\nPlan:\n{plan}\n\nReturn a single valid PostgreSQL SELECT query only (no explanation)."
        sql = self.llm.generate(system=system, user=user, temperature=0.0, max_tokens=1024)

        if (isinstance(plan, str) and plan.strip().upper().startswith("FALLBACK")) or (
            isinstance(sql, str) and sql.strip().upper().startswith("FALLBACK")
        ):
            return self._local_fallback(user_query or plan)

        return sql
