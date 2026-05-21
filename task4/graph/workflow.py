import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional
from agents.llm import LLM
from agents.planner import Planner
from agents.sql_generator import SQLGenerator
from agents.validator import Validator
from agents.executor import execute_query
from agents.summarizer import Summarizer
from tools.db_tools import get_schema_sql


def _get_log_path() -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(root, "log.json")


def _append_log(entry: dict) -> None:
    path = _get_log_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        else:
            data = []
    except Exception:
        data = []

    data.append(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


@dataclass
class WorkflowState:
    user_query: str
    schema: str = ""
    plan: Optional[str] = None
    generated_sql: Optional[str] = None
    is_valid_sql: bool = False
    execution_results: Optional[List[dict]] = field(default_factory=list)
    final_answer: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    execution_time: Optional[float] = None


def run_workflow(user_query: str) -> WorkflowState:
    state = WorkflowState(user_query=user_query)
    start_time = time.perf_counter()

    # load schema
    state.schema = get_schema_sql()

    llm = LLM()
    planner = Planner(llm=llm)
    generator = SQLGenerator(llm=llm)
    validator = Validator()
    summarizer = Summarizer(llm=llm)

    # Planning
    try:
        state.plan = planner.plan(user_query, schema=state.schema)
    except Exception as e:
        state.errors.append(f"Planner error: {e}")
        state.execution_time = time.perf_counter() - start_time
        _append_log({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_query": user_query,
            "plan": state.plan,
            "generated_sql": state.generated_sql,
            "is_valid_sql": state.is_valid_sql,
            "execution_results": state.execution_results,
            "final_answer": state.final_answer,
            "errors": state.errors,
            "status": "failure",
            "execution_time": state.execution_time,
        })
        return state

    # SQL generation + validation loop
    for attempt in range(1, 4):
        try:
            state.generated_sql = generator.generate(state.plan, schema=state.schema, user_query=state.user_query)
        except Exception as e:
            state.errors.append(f"Generator error: {e}")
            state.execution_time = time.perf_counter() - start_time
            _append_log({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user_query": user_query,
                "plan": state.plan,
                "generated_sql": state.generated_sql,
                "is_valid_sql": state.is_valid_sql,
                "execution_results": state.execution_results,
                "final_answer": state.final_answer,
                "errors": state.errors,
                "status": "failure",
                "execution_time": state.execution_time,
                "attempt": attempt,
            })
            return state

        valid, msg, cleaned_sql = validator.validate(state.generated_sql)
        state.is_valid_sql = valid
        # Always use cleaned SQL regardless of validation result
        if cleaned_sql:
            state.generated_sql = cleaned_sql
        if valid:
            break
        state.errors.append(f"Validation failed: {msg}")
        state.plan += f"\n-- Validation error: {msg} -- Please produce a corrected SELECT-only query."
        if attempt == 3:
            state.execution_time = time.perf_counter() - start_time
            _append_log({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "user_query": user_query,
                "plan": state.plan,
                "generated_sql": state.generated_sql,
                "is_valid_sql": state.is_valid_sql,
                "execution_results": state.execution_results,
                "final_answer": state.final_answer,
                "errors": state.errors,
                "status": "failure",
                "execution_time": state.execution_time,
                "attempt": attempt,
            })
            return state

    # Execute
    try:
        query_start = time.perf_counter()
        state.execution_results = execute_query(state.generated_sql)
        state.execution_time = time.perf_counter() - query_start
    except Exception as e:
        state.errors.append(f"Execution error: {e}")
        state.execution_time = time.perf_counter() - start_time
        _append_log({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_query": user_query,
            "plan": state.plan,
            "generated_sql": state.generated_sql,
            "is_valid_sql": state.is_valid_sql,
            "execution_results": state.execution_results,
            "final_answer": state.final_answer,
            "errors": state.errors,
            "status": "failure",
            "execution_time": state.execution_time,
            "attempt": attempt,
        })
        return state

    # Summarize
    try:
        state.final_answer = summarizer.summarize(state.user_query, state.execution_results)
    except Exception as e:
        state.errors.append(f"Summarizer error: {e}")

    state.execution_time = time.perf_counter() - start_time
    _append_log({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "user_query": user_query,
        "plan": state.plan,
        "generated_sql": state.generated_sql,
        "is_valid_sql": state.is_valid_sql,
        "execution_results": state.execution_results,
        "final_answer": state.final_answer,
        "errors": state.errors,
        "status": "success" if not state.errors else "failure",
        "execution_time": state.execution_time,
        "attempts": attempt,
    })

    return state
