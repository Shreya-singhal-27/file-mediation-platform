from app.core.exceptions import (
	BadRequestException,
	ResourceNotFoundException,
)
from app.models.destination import Destination
from app.repositories.destination_repository import DestinationRepository
from app.schemas.destination import (
	DestinationCreate,
	DestinationUpdate,
)


class DestinationService:

	def __init__(
		self,
		destination_repository: DestinationRepository,
	):
		self.destination_repository = destination_repository

	def create_destination(
		self,
		data: DestinationCreate,
	) -> Destination:

		if self.destination_repository.get_by_name(data.name):
			raise BadRequestException(
				"Destination already exists."
			)

		destination = Destination(
			**data.model_dump()
		)

		return self.destination_repository.create(destination)

	def get_destination(
		self,
		destination_id: int,
	) -> Destination:

		destination = self.destination_repository.get_by_id(destination_id)

		if destination is None:
			raise ResourceNotFoundException(
				"Destination"
			)

		return destination

	def get_all_destinations(
		self,
	) -> list[Destination]:

		return self.destination_repository.get_all()

	def get_active_destinations(
		self,
	) -> list[Destination]:

		return self.destination_repository.get_active_destinations()

	def update_destination(
		self,
		destination: Destination,
		data: DestinationUpdate,
	) -> Destination:

		return self.destination_repository.update_from_schema(
			destination,
			data,
		)

	def delete_destination(
		self,
		destination: Destination,
	) -> None:

		self.destination_repository.delete(destination)