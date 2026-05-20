import os
import json
import re
from typing import Dict, Any, Optional

try:
    from prompts.templates import (
        DECOMPOSE_PROMPT,
        GENERATION_PROMPT,
        FIX_PROMPT,
        SCHEMA_CONTEXT,
        DECOMPOSE_HINTS,
        DECOMPOSE_RETRY_HINTS,
        GENERATION_HINTS,
        FIX_HINTS,
    )
except ImportError:
    from task3.prompts.templates import (
        DECOMPOSE_PROMPT,
        GENERATION_PROMPT,
        FIX_PROMPT,
        SCHEMA_CONTEXT,
        DECOMPOSE_HINTS,
        DECOMPOSE_RETRY_HINTS,
        GENERATION_HINTS,
        FIX_HINTS,
    )

AI_API_KEY = os.environ.get("AI_API_KEY") or os.environ.get("OPENAI_API_KEY")
AI_PROVIDER = os.environ.get("AI_PROVIDER")
if not AI_PROVIDER:
    if AI_API_KEY and AI_API_KEY.startswith("AIza"):
        AI_PROVIDER = "google"
    else:
        AI_PROVIDER = "openai"
AI_PROVIDER = AI_PROVIDER.lower()
AI_MODEL = os.environ.get("AI_MODEL", "gpt-4o-mini" if AI_PROVIDER == "openai" else "gemini-2.5-flash")
MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() in ("1", "true", "yes")


def _call_llm_real(prompt: str, max_tokens: int = 800, temperature: float = 0.0) -> str:
    if not AI_API_KEY:
        raise RuntimeError("AI_API_KEY or OPENAI_API_KEY not set")

    if AI_PROVIDER == "google":
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("requests package is required for Google AI Studio support") from exc

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{AI_MODEL}:generateContent"
        headers = {
            "x-goog-api-key": AI_API_KEY,
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        try:
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(f"Google AI Studio request failed: {response.status_code} {response.text}") from exc

        data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Google AI Studio returned no text candidate")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Google AI Studio response missing content parts")
        return "".join([part.get("text", "") for part in parts]).strip()

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is required when MOCK_MODE is disabled") from exc

    client = OpenAI(api_key=AI_API_KEY)
    resp = client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    message = resp.choices[0].message
    if hasattr(message, "content"):
        return message.content.strip()
    return message["content"].strip()




def _mock_decompose(question: str) -> Dict[str, Any]:
    q = question.lower()
    tables = []
    mapping = {
        "product": "products",
        "products": "products",
        "customer": "customers",
        "customers": "customers",
        "order": "orders",
        "orders": "orders",
        "payment": "payments",
        "employee": "employees",
        "office": "offices",
    }
    for k, v in mapping.items():
        if k in q and v not in tables:
            tables.append(v)
    if not tables:
        tables = ["products"]

    columns = []
    if "price" in q or "buyprice" in q:
        columns = ["productName", "buyPrice"]
    elif "country" in q:
        columns = ["customerName", "country"]
    else:
        columns = ["*"]

    filters = []
    m = re.search(r"(>=|<=|>|<)\s*(\d+)", q)
    if m:
        operator = m.group(1)
        value = m.group(2)
        if "price" in q or "buyprice" in q:
            field = "buyPrice"
        elif "quantity" in q or "quantityordered" in q:
            field = "quantityOrdered"
        elif "order" in q and "date" not in q:
            field = "orderNumber"
        else:
            field = "customerNumber"
        filters.append(f"{field} {operator} {value}")
    m2 = re.search(r"\bin\s+([a-zA-Z_][a-zA-Z0-9_]*)", q)
    if m2:
        # not a robust parse; placeholder for equality to a string value
        filters.append(f"{m2.group(1)} = '{m2.group(1)}'")

    return {
        "intent": question,
        "tables": tables,
        "columns": columns,
        "filters": filters,
        "joins": [],
    }


def _mock_generate_sql(decomp: Dict[str, Any]) -> str:
    cols_list = decomp.get("columns") or decomp.get("Columns") or ["*"]
    if isinstance(cols_list, str):
        cols_list = [cols_list]
    cols = ", ".join(cols_list)
    table = (decomp.get("tables") or decomp.get("Tables") or ["products"])[0]
    sql = f"SELECT {cols} FROM {table}"
    filters = decomp.get("filters") or decomp.get("Filters") or []
    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " LIMIT 100"
    return sql


def _mock_fix_sql(sql: str, error: str) -> str:
    # Very simple mock: if missing LIMIT mention, add LIMIT 100
    if "syntax" in error.lower() and not sql.strip().lower().endswith(";"):
        return sql + ";"
    if "column" in error.lower():
        # remove quoted parts or replace with *
        return re.sub(r"SELECT\s+.+\s+FROM", "SELECT * FROM", sql, flags=re.IGNORECASE)
    # default: return original
    return sql


def _call_llm(prompt: str, max_tokens: int = 800, temperature: float = 0.0) -> str:
    if MOCK_MODE:
        low = prompt.lower()
        if "json extractor" in low or "return a json object" in low or ("schema:" in low and "question:" in low):
            m = re.search(r"question:\s*(.*?)(?:\n\s*\n|$)", prompt, flags=re.IGNORECASE | re.DOTALL)
            question = m.group(1).strip() if m else prompt
            return json.dumps(_mock_decompose(question))
        if "postgresql" in low and "select query" in low or "decomposition json" in low or "generate" in low:
            m = re.search(r"\{.*\}", prompt, flags=re.DOTALL)
            if m:
                try:
                    decomp = json.loads(m.group(0))
                    return _mock_generate_sql(decomp)
                except Exception:
                    return _mock_generate_sql({})
            return _mock_generate_sql({})
        if "a sql execution failed" in low or "failed with error" in low or "error:" in low:
            m = re.search(r"Original SQL:\s*(.*?)\n\n", prompt, flags=re.IGNORECASE | re.DOTALL)
            original = m.group(1).strip() if m else ""
            m2 = re.search(r"error:\s*(.*?)\n\n", prompt, flags=re.IGNORECASE | re.DOTALL)
            error = m2.group(1).strip() if m2 else ""
            return _mock_fix_sql(original, error)
        return ""
    return _call_llm_real(prompt, max_tokens=max_tokens, temperature=temperature)


def _clean_sql_response(text: str) -> str:
    cleaned = text.strip()
    # Remove markdown code fences and optional language hints
    cleaned = re.sub(r'^```(?:sql)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.IGNORECASE)
    # Remove leading/trailing backticks if present
    if cleaned.startswith('`') and cleaned.endswith('`'):
        cleaned = cleaned[1:-1].strip()
    return cleaned.strip().rstrip(';')


def _extract_json_substring(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r'^```(?:json|sql)?\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.IGNORECASE)
    if cleaned.startswith('`') and cleaned.endswith('`'):
        cleaned = cleaned[1:-1].strip()

    brace_count = 0
    start_idx = None
    end_idx = None
    for idx, ch in enumerate(cleaned):
        if ch == '{':
            if start_idx is None:
                start_idx = idx
            brace_count += 1
        elif ch == '}':
            if brace_count > 0:
                brace_count -= 1
                if brace_count == 0 and start_idx is not None:
                    end_idx = idx
                    break
    if start_idx is not None and end_idx is not None:
        return cleaned[start_idx:end_idx + 1]
    return cleaned


def decompose(question: str, schema: str = SCHEMA_CONTEXT) -> Dict[str, Any]:
    prompt = DECOMPOSE_PROMPT.format(schema=schema, question=question) + "\n" + DECOMPOSE_HINTS
    text = _call_llm(prompt, max_tokens=400)
    retry_text = None
    try:
        return json.loads(text)
    except Exception as exc:
        fallback = _extract_json_substring(text)
        if fallback != text:
            try:
                return json.loads(fallback)
            except Exception:
                pass

        retry_prompt = prompt + "\n" + DECOMPOSE_RETRY_HINTS
        retry_text = _call_llm(retry_prompt, max_tokens=400)
        try:
            return json.loads(retry_text)
        except Exception:
            retry_fallback = _extract_json_substring(retry_text)
            if retry_fallback != retry_text:
                try:
                    return json.loads(retry_fallback)
                except Exception:
                    pass

        raise ValueError(
            f"LLM decomposition did not return valid JSON. Raw model output:\n{text}\n\nRetry output:\n{retry_text}"
        ) from exc


def generate_sql(decomposition: Dict[str, Any], schema: str = SCHEMA_CONTEXT) -> str:
    prompt = GENERATION_PROMPT.format(decomposition=json.dumps(decomposition), schema=schema) + "\n" + GENERATION_HINTS
    sql = _call_llm(prompt, max_tokens=800)
    return _clean_sql_response(sql)


def fix_sql(original_sql: str, error: str, decomposition: Optional[Dict[str, Any]] = None, schema: str = SCHEMA_CONTEXT) -> Optional[str]:
    prompt = FIX_PROMPT.format(sql=original_sql, error=error, schema=schema) + "\n" + FIX_HINTS
    sql = _call_llm(prompt, max_tokens=800)
    sql = _clean_sql_response(sql)
    if not sql:
        return None
    return sql
