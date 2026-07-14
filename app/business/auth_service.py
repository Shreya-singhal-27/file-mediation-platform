from app.core.exceptions import (
	AuthenticationException,
	BadRequestException,
)
from app.core.jwt_handler import (
	create_access_token,
	create_refresh_token,
	decode_token,
)
from app.core.password import (
	hash_password,
	verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
	AuthResponse,
	Token,
)
from app.schemas.user import UserCreate


class AuthService:

	def __init__(
		self,
		user_repository: UserRepository,
	):
		self.user_repository = user_repository

	def login(
		self,
		email: str,
		password: str,
	) -> AuthResponse:

		user = self.user_repository.get_by_email(email)

		if user is None:
			raise AuthenticationException()

		if not verify_password(
			password,
			user.hashed_password,
		):
			raise AuthenticationException()

		self.user_repository.update_last_login(user)

		payload = {
			"user_id": user.id,
			"email": user.email,
			"role": user.role.name,
		}

		return AuthResponse(
			user_id=user.id,
			username=user.username,
			email=user.email,
			role=user.role.name,
			access_token=create_access_token(payload),
			refresh_token=create_refresh_token(payload),
			token_type="bearer",
		)

	def register(
		self,
		user_data: UserCreate,
	) -> User:

		if self.user_repository.get_by_email(
			user_data.email,
		):
			raise BadRequestException(
				"Email already exists."
			)

		if self.user_repository.get_by_username(
			user_data.username,
		):
			raise BadRequestException(
				"Username already exists."
			)

		user = User(
			username=user_data.username,
			email=user_data.email,
			first_name=user_data.first_name,
			last_name=user_data.last_name,
			hashed_password=hash_password(
				user_data.password,
			),
			role_id=user_data.role_id,
		)

		return self.user_repository.create(user)

	def refresh_token(
		self,
		refresh_token: str,
	) -> Token:

		payload = decode_token(refresh_token)

		if payload is None:
			raise AuthenticationException()

		new_access_token = create_access_token(
			{
				"user_id": payload["user_id"],
				"email": payload["email"],
				"role": payload["role"],
			}
		)

		return Token(
			access_token=new_access_token,
			refresh_token=refresh_token,
			token_type="bearer",
		)