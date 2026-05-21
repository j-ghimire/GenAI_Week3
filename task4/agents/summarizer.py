from agents.llm import LLM
from prompts import SUMMARIZER_PROMPT
import json


class Summarizer:
    def __init__(self, llm: LLM = None):
        self.llm = llm or LLM()

    def _local_summary(self, original_query: str, results) -> str:
        if results is None:
            return "No results were returned."
        if isinstance(results, list):
            if len(results) == 0:
                return "No rows matched the query."
            if len(results) == 1 and isinstance(results[0], dict):
                row = results[0]
                if len(row) == 1:
                    key, value = next(iter(row.items()))
                    return f"The query returned a single value: {value}."
                return f"The query returned one row with columns: {', '.join(row.keys())}."
            if all(isinstance(row, dict) for row in results):
                keys = results[0].keys()
                return f"The query returned {len(results)} rows with columns: {', '.join(keys)}."
            return f"The query returned {len(results)} items."
        if isinstance(results, dict):
            return f"The query returned a single record with keys: {', '.join(results.keys())}."
        return f"The query returned: {results}."

    def summarize(self, original_query: str, results) -> str:
        system = SUMMARIZER_PROMPT
        user = f"Original question:\n{original_query}\n\nResults (JSON):\n{json.dumps(results, default=str, indent=2)}\n\nProvide a concise natural-language answer and a short explanation of what was returned."
        summary = self.llm.generate(system=system, user=user, temperature=0.0, max_tokens=512)
        if isinstance(summary, str) and summary.strip().upper().startswith("FALLBACK"):
            return self._local_summary(original_query, results)
        return summary
