from uuid import uuid4

from fastapi import APIRouter

from schemas import QueryRequest, QueryResponse
from services.agent_service import run_agent

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(data: QueryRequest) -> QueryResponse:
    thread_id = data.thread_id or str(uuid4())
    text, thread_id, _ = await run_agent(
        user_id=data.user_id,
        message=data.message,
        thread_id=thread_id,
    )
    return QueryResponse(response=text, thread_id=thread_id)
