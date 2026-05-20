from typing import Dict
from agents.llm import LLM
from prompts import PLANNER_PROMPT


class Planner:
    def __init__(self, llm: LLM = None):
        self.llm = llm or LLM()

    def plan(self, user_query: str, schema: str = "") -> str:
        system = PLANNER_PROMPT
        user = f"Schema:\n{schema}\n\nUser Query:\n{user_query}\n\nProduce a short plan describing which tables and joins and filters to use. Be concise."
        plan = self.llm.generate(system=system, user=user, temperature=0.0, max_tokens=256)
        return plan
