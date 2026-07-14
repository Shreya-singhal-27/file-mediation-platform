from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.filter_rule import FilterRule
from app.repositories.base_repository import BaseRepository


class FilterRuleRepository(BaseRepository[FilterRule]):

	def __init__(self, db: Session):
		super().__init__(db, FilterRule)

	def get_by_pipeline_id(
		self,
		pipeline_id: int,
	) -> list[FilterRule]:

		statement = (
			select(FilterRule)
			.where(FilterRule.pipeline_id == pipeline_id)
			.order_by(FilterRule.priority)
		)

		return list(self.db.scalars(statement).all())

	def get_active_rules(
		self,
		pipeline_id: int,
	) -> list[FilterRule]:

		statement = (
			select(FilterRule)
			.where(
				FilterRule.pipeline_id == pipeline_id,
				FilterRule.is_active.is_(True),
			)
			.order_by(FilterRule.priority)
		)

		return list(self.db.scalars(statement).all())