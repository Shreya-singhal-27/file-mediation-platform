from app.core.exceptions import (
	BadRequestException,
	ResourceNotFoundException,
)
from app.models.role import Role
from app.repositories.role_repository import RoleRepository
from app.schemas.role import (
	RoleCreate,
	RoleUpdate,
)


class RoleService:

	def __init__(
		self,
		role_repository: RoleRepository,
	):
		self.role_repository = role_repository

	def create_role(
		self,
		data: RoleCreate,
	) -> Role:

		if self.role_repository.get_by_name(
			data.name,
		):
			raise BadRequestException(
				"Role already exists."
			)

		role = Role(
			**data.model_dump()
		)

		return self.role_repository.create(role)

	def get_role(
		self,
		role_id: int,
	) -> Role:

		role = self.role_repository.get_by_id(
			role_id,
		)

		if role is None:
			raise ResourceNotFoundException(
				"Role"
			)

		return role

	def get_all_roles(
		self,
	) -> list[Role]:

		return self.role_repository.get_all()

	def get_total_roles(
		self,
	) -> int:

		return self.role_repository.count()

	def update_role(
		self,
		role: Role,
		data: RoleUpdate,
	) -> Role:

		return self.role_repository.update_from_schema(
			role,
			data,
		)

	def delete_role(
		self,
		role: Role,
	) -> None:

		self.role_repository.delete(role)