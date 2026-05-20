from fastapi import FastAPI
from pydantic import BaseModel
from graph.workflow import run_workflow

app = FastAPI()


class QueryRequest(BaseModel):
    query: str


@app.post("/query")
def query_endpoint(req: QueryRequest):
    state = run_workflow(req.query)
    return {
        "user_query": state.user_query,
        "plan": state.plan,
        "generated_sql": state.generated_sql,
        "is_valid_sql": state.is_valid_sql,
        "execution_results": state.execution_results,
        "final_answer": state.final_answer,
        "errors": state.errors,
    }
