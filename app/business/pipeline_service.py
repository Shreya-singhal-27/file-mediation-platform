from app.core.exceptions import (
	BadRequestException,
	ResourceNotFoundException,
)
from app.models.pipeline import Pipeline
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.pipeline import (
	PipelineCreate,
	PipelineUpdate,
)


class PipelineService:

	def __init__(
		self,
		pipeline_repository: PipelineRepository,
	):
		self.pipeline_repository = pipeline_repository

	def create_pipeline(
		self,
		data: PipelineCreate,
		created_by_id: int,
	) -> Pipeline:

		if self.pipeline_repository.get_by_name(data.name):
			raise BadRequestException(
				"Pipeline already exists."
			)

		pipeline = Pipeline(
			**data.model_dump(),
			created_by_id=created_by_id,
		)

		return self.pipeline_repository.create(pipeline)

	def get_pipeline(
		self,
		pipeline_id: int,
	) -> Pipeline:

		pipeline = self.pipeline_repository.get_by_id(pipeline_id)

		if pipeline is None:
			raise ResourceNotFoundException(
				"Pipeline"
			)

		return pipeline

	def get_all_pipelines(
		self,
	) -> list[Pipeline]:

		return self.pipeline_repository.get_all()

	def get_active_pipelines(
		self,
	) -> list[Pipeline]:

		return self.pipeline_repository.get_active_pipelines()

	def update_pipeline(
		self,
		pipeline: Pipeline,
		data: PipelineUpdate,
	) -> Pipeline:

		return self.pipeline_repository.update_from_schema(
			pipeline,
			data,
		)

	def delete_pipeline(
		self,
		pipeline: Pipeline,
	) -> None:

		self.pipeline_repository.delete(pipeline)