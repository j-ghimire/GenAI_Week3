from typing import Any, Dict, List, Optional
import logging

from fastapi import Body, FastAPI
from pydantic import BaseModel
from graph.workflow import run_workflow

app = FastAPI()
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)


class QueryRequest(BaseModel):
    query: Optional[str] = None
    question: Optional[str] = None


class AgentRequest(BaseModel):
    question: str


class AgentResponse(BaseModel):
    sql: Optional[str] = ""
    result: Optional[object] = None
    summary: Optional[str] = ""
    status: str = "failure"
    errors: List[str] = []


@app.post("/query")
def query_endpoint(req: Dict[str, Any] = Body(...)):
    user_query = req.get("query") or req.get("question")
    if not user_query:
        return {
            "user_query": None,
            "plan": None,
            "generated_sql": None,
            "is_valid_sql": False,
            "execution_results": [],
            "final_answer": None,
            "errors": ["Missing query text in request payload. Use either 'query' or 'question'."],
        }

    state = run_workflow(user_query)
    return {
        "user_query": state.user_query,
        "plan": state.plan,
        "generated_sql": state.generated_sql,
        "is_valid_sql": state.is_valid_sql,
        "execution_results": state.execution_results,
        "final_answer": state.final_answer,
        "errors": state.errors,
    }


@app.post("/agent/sql", response_model=AgentResponse)
def agent_sql_endpoint(req: AgentRequest):
    logging.info("Received /agent/sql request: %s", req.question)
    state = run_workflow(req.question)

    status = "success" if state.is_valid_sql and not state.errors else "failure"
    result = state.execution_results
    if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict) and len(result[0]) == 1:
        result = next(iter(result[0].values()))

    return AgentResponse(
        sql=state.generated_sql or "",
        result=result,
        summary=state.final_answer or "",
        status=status,
        errors=state.errors,
    )
