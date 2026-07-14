from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mapping_rule import MappingRule
from app.repositories.base_repository import BaseRepository


class MappingRuleRepository(BaseRepository[MappingRule]):

	def __init__(self, db: Session):
		super().__init__(db, MappingRule)

	def get_by_pipeline_id(
		self,
		pipeline_id: int,
	) -> list[MappingRule]:

		statement = (
			select(MappingRule)
			.where(MappingRule.pipeline_id == pipeline_id)
			.order_by(MappingRule.id)
		)

		return list(self.db.scalars(statement).all())