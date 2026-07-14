from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.pipeline import Pipeline
from app.repositories.base_repository import BaseRepository


class PipelineRepository(BaseRepository[Pipeline]):

	def __init__(self, db: Session):
		super().__init__(db, Pipeline)

	def get_by_id(self, pipeline_id: int) -> Pipeline | None:
		statement = (
			select(Pipeline)
			.options(
				joinedload(Pipeline.source),
				joinedload(Pipeline.destination),
				joinedload(Pipeline.created_by),
			)
			.where(Pipeline.id == pipeline_id)
		)
		return self.db.scalar(statement)

	def get_by_name(self, name: str) -> Pipeline | None:
		statement = select(Pipeline).where(Pipeline.name == name)
		return self.db.scalar(statement)

	def get_all(self) -> list[Pipeline]:
		statement = (
			select(Pipeline)
			.options(
				joinedload(Pipeline.source),
				joinedload(Pipeline.destination),
			)
			.order_by(Pipeline.id)
		)
		return list(self.db.scalars(statement).all())

	def get_active_pipelines(self) -> list[Pipeline]:
		statement = (
			select(Pipeline)
			.where(Pipeline.is_active.is_(True))
			.order_by(Pipeline.id)
		)
		return list(self.db.scalars(statement).all())