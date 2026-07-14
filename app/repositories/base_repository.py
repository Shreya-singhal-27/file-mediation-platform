from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
	"""
	Generic repository providing common CRUD operations.
	"""

	def __init__(
		self,
		db: Session,
		model: type[ModelType],
	):
		self.db = db
		self.model = model

	def create(
		self,
		obj: ModelType,
	) -> ModelType:
		self.db.add(obj)
		self.db.commit()
		self.db.refresh(obj)
		return obj

	def get_by_id(
		self,
		obj_id: int,
	) -> ModelType | None:
		return self.db.get(self.model, obj_id)

	def get_all(
		self,
	) -> list[ModelType]:
		statement = (
			select(self.model)
			.order_by(self.model.id)
		)
		return list(self.db.scalars(statement).all())

	def update(
		self,
		obj: ModelType,
	) -> ModelType:
		self.db.commit()
		self.db.refresh(obj)
		return obj

	def update_from_schema(
		self,
		obj: ModelType,
		schema: Any,
	) -> ModelType:
		"""
		Update a model using values from a Pydantic schema.
		Only explicitly supplied fields are updated.
		"""

		for key, value in schema.model_dump(
			exclude_unset=True,
		).items():
			setattr(obj, key, value)

		self.db.commit()
		self.db.refresh(obj)

		return obj

	def delete(
		self,
		obj: ModelType,
	) -> None:
		self.db.delete(obj)
		self.db.commit()

	def exists(
		self,
		obj_id: int,
	) -> bool:
		return self.get_by_id(obj_id) is not None

	def count(
		self,
	) -> int:
		statement = (
			select(func.count())
			.select_from(self.model)
		)
		return self.db.scalar(statement) or 0

	def commit(
		self,
	) -> None:
		self.db.commit()

	def rollback(
		self,
	) -> None:
		self.db.rollback()

	def refresh(
		self,
		obj: ModelType,
	) -> None:
		self.db.refresh(obj)