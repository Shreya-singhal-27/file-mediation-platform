from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source
from app.repositories.base_repository import BaseRepository


class SourceRepository(BaseRepository[Source]):

	def __init__(self, db: Session):
		super().__init__(db, Source)

	def get_by_name(self, name: str) -> Source | None:
		statement = select(Source).where(Source.name == name)
		return self.db.scalar(statement)

	def get_active_sources(self) -> list[Source]:
		statement = (
			select(Source)
			.where(Source.is_active.is_(True))
			.order_by(Source.id)
		)
		return list(self.db.scalars(statement).all())
