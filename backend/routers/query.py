from fastapi import APIRouter

from schemas import QueryRequest, QueryResponse
from services.agent_service import run_agent

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(data: QueryRequest) -> QueryResponse:
    text, updated_history = await run_agent(
        user_id=data.user_id,
        message=data.message,
        history=data.history,
    )
    clean_history = [m for m in updated_history if m["role"] != "tool"]
    return QueryResponse(response=text, history=clean_history)
