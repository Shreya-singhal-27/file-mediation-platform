from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):

	def __init__(self, db: Session):
		super().__init__(db, User)

	def get_by_email(self, email: str) -> User | None:
		statement = select(User).where(User.email == email)
		return self.db.scalar(statement)

	def get_by_username(self, username: str) -> User | None:
		statement = select(User).where(User.username == username)
		return self.db.scalar(statement)

	def update_last_login(self, user: User) -> User:
		user.last_login = datetime.utcnow()
		self.commit()
		self.refresh(user)
		return user