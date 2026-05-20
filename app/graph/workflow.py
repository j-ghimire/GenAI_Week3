from dataclasses import dataclass, field
from typing import Any, List, Optional
from agents.llm import LLM
from agents.planner import Planner
from agents.sql_generator import SQLGenerator
from agents.validator import Validator
from agents.executor import execute_query
from agents.summarizer import Summarizer
from tools.db_tools import get_schema_sql


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


def run_workflow(user_query: str) -> WorkflowState:
    state = WorkflowState(user_query=user_query)

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
        return state

    # SQL generation + validation loop
    for _ in range(2):
        try:
            state.generated_sql = generator.generate(state.plan, schema=state.schema, user_query=state.user_query)
        except Exception as e:
            state.errors.append(f"Generator error: {e}")
            return state

        valid, msg = validator.validate(state.generated_sql)
        state.is_valid_sql = valid
        if valid:
            break
        else:
            state.errors.append(f"Validation failed: {msg}")
            # feed back into generator via expanded plan
            state.plan += f"\n-- Validation error: {msg} -- Please produce a corrected SELECT-only query."

    if not state.is_valid_sql:
        return state

    # Execute
    try:
        state.execution_results = execute_query(state.generated_sql)
    except Exception as e:
        state.errors.append(f"Execution error: {e}")
        return state

    # Summarize
    try:
        state.final_answer = summarizer.summarize(state.user_query, state.execution_results)
    except Exception as e:
        state.errors.append(f"Summarizer error: {e}")

    return state
