from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):

	def __init__(self, db: Session):
		super().__init__(db, Role)

	def get_by_name(self, name: str) -> Role | None:
		statement = select(Role).where(Role.name == name)
		return self.db.scalar(statement)