from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import User
from schemas import QueryRequest, QueryResponse
from services.agent_service import run_agent
from services.thread_service import ThreadService

router = APIRouter(prefix="/query", tags=["query"])
_thread_service = ThreadService()


@router.post("", response_model=QueryResponse)
async def query(
    data: QueryRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> QueryResponse:
    user_id = current_user.id

    if data.thread_id:
        # Reject if thread belongs to a different user
        await _thread_service.validate_access(session, data.thread_id, user_id)
        thread_id = data.thread_id
    else:
        thread_id = str(uuid4())

    text, thread_id, _ = await run_agent(
        user_id=user_id,
        message=data.message,
        thread_id=thread_id,
    )

    # Persist new thread → owner mapping (no-op if already registered)
    await _thread_service.register(session, thread_id, user_id)

    return QueryResponse(response=text, thread_id=thread_id)
