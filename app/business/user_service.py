from app.core.exceptions import (
	ResourceNotFoundException,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:

	def __init__(
		self,
		user_repository: UserRepository,
	):
		self.user_repository = user_repository

	def get_user(
		self,
		user_id: int,
	) -> User:

		user = self.user_repository.get_by_id(user_id)

		if user is None:
			raise ResourceNotFoundException(
				"User"
			)

		return user

	def get_all_users(
		self,
	) -> list[User]:

		return self.user_repository.get_all()

	def get_total_users(
		self,
	) -> int:

		return self.user_repository.count()

	def update_user(
		self,
		user: User,
		data: UserUpdate,
	) -> User:

		return self.user_repository.update_from_schema(
			user,
			data,
		)

	def delete_user(
		self,
		user: User,
	) -> None:

		self.user_repository.delete(user)