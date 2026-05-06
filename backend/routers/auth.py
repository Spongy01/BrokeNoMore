from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])
_service = UserService()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, session: AsyncSession = Depends(get_db)):
    user = await _service.register(session, data.email, data.password)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_db)):
    token = await _service.login(session, data.email, data.password)
    return TokenResponse(access_token=token)


@router.post("/logout", status_code=204)
async def logout():
    # JWT is stateless — instruct the client to discard the token
    pass


@router.post("/forgot-password", status_code=204)
async def forgot_password(
    data: ForgotPasswordRequest, session: AsyncSession = Depends(get_db)
):
    await _service.forgot_password(session, data.email)


@router.post("/reset-password", status_code=204)
async def reset_password(
    data: ResetPasswordRequest, session: AsyncSession = Depends(get_db)
):
    await _service.reset_password(session, data.token, data.new_password)
