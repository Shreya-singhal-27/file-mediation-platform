from app.core.exceptions import (
	BadRequestException,
	ResourceNotFoundException,
)
from app.models.source import Source
from app.repositories.source_repository import SourceRepository
from app.schemas.source import (
	SourceCreate,
	SourceUpdate,
)


class SourceService:

	def __init__(
		self,
		source_repository: SourceRepository,
	):
		self.source_repository = source_repository

	def create_source(
		self,
		data: SourceCreate,
	) -> Source:

		if self.source_repository.get_by_name(data.name):
			raise BadRequestException(
				"Source already exists."
			)

		source = Source(
			**data.model_dump()
		)

		return self.source_repository.create(source)

	def get_source(
		self,
		source_id: int,
	) -> Source:

		source = self.source_repository.get_by_id(source_id)

		if source is None:
			raise ResourceNotFoundException(
				"Source"
			)

		return source

	def get_all_sources(
		self,
	) -> list[Source]:

		return self.source_repository.get_all()

	def get_active_sources(
		self,
	) -> list[Source]:

		return self.source_repository.get_active_sources()

	def update_source(
		self,
		source: Source,
		data: SourceUpdate,
	) -> Source:

		return self.source_repository.update_from_schema(
			source,
			data,
		)

	def delete_source(
		self,
		source: Source,
	) -> None:

		self.source_repository.delete(source)