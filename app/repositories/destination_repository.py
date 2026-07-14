from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.destination import Destination
from app.repositories.base_repository import BaseRepository


class DestinationRepository(BaseRepository[Destination]):

	def __init__(self, db: Session):
		super().__init__(db, Destination)

	def get_by_name(self, name: str) -> Destination | None:
		statement = select(Destination).where(Destination.name == name)
		return self.db.scalar(statement)

	def get_active_destinations(self) -> list[Destination]:
		statement = (
			select(Destination)
			.where(Destination.is_active.is_(True))
			.order_by(Destination.id)
		)
		return list(self.db.scalars(statement).all())