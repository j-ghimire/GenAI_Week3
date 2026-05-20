from agents.llm import LLM
from prompts import SUMMARIZER_PROMPT
import json


class Summarizer:
    def __init__(self, llm: LLM = None):
        self.llm = llm or LLM()

    def summarize(self, original_query: str, results) -> str:
        system = SUMMARIZER_PROMPT
        user = f"Original question:\n{original_query}\n\nResults (JSON):\n{json.dumps(results, default=str, indent=2)}\n\nProvide a concise natural-language answer and a short explanation of what was returned."
        summary = self.llm.generate(system=system, user=user, temperature=0.0, max_tokens=512)
        return summary
