from fastapi import APIRouter, Depends, HTTPException, status

from app.business.auth_service import AuthService
from app.dependencies import get_auth_service
from app.schemas.auth import (
	AuthResponse,
	LoginRequest,
	Token,
)
from app.schemas.user import UserCreate

router = APIRouter(
	prefix="/auth",
	tags=["Authentication"],
)


@router.post(
	"/login",
	response_model=AuthResponse,
)
def login(
	request: LoginRequest,
	auth_service: AuthService = Depends(
		get_auth_service,
	),
):
	try:
		return auth_service.login(
			request.email,
			request.password,
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=str(exc),
		)


@router.post(
	"/register",
)
def register(
	request: UserCreate,
	auth_service: AuthService = Depends(
		get_auth_service,
	),
):
	try:
		return auth_service.register(request)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		)


@router.post(
	"/refresh",
	response_model=Token,
)
def refresh_token(
	request: Token,
	auth_service: AuthService = Depends(
		get_auth_service,
	),
):
	try:
		return auth_service.refresh_token(
			request.refresh_token,
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail=str(exc),
		)