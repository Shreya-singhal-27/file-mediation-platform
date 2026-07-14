from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models.job import Job
from app.repositories.base_repository import BaseRepository


class JobRepository(BaseRepository[Job]):

	def __init__(self, db: Session):
		super().__init__(db, Job)

	def get_by_pipeline(
		self,
		pipeline_id: int,
	) -> list[Job]:

		statement = (
			select(Job)
			.where(Job.pipeline_id == pipeline_id)
			.order_by(desc(Job.started_at))
		)

		return list(self.db.scalars(statement).all())

	def get_latest_job(
		self,
		pipeline_id: int,
	) -> Job | None:

		statement = (
			select(Job)
			.where(Job.pipeline_id == pipeline_id)
			.order_by(desc(Job.started_at))
			.limit(1)
		)

		return self.db.scalar(statement)

	def get_running_jobs(self) -> list[Job]:

		statement = (
			select(Job)
			.where(Job.status == "RUNNING")
		)

		return list(self.db.scalars(statement).all())

	def get_by_id(
		self,
		job_id: int,
	) -> Job | None:

		statement = (
			select(Job)
			.options(
				joinedload(Job.pipeline),
				joinedload(Job.started_by),
			)
			.where(Job.id == job_id)
		)

		return self.db.scalar(statement)

	def complete_job(
		self,
		job: Job,
	) -> Job:

		job.status = "COMPLETED"
		job.current_stage = "COMPLETED"
		job.completed_at = datetime.utcnow()

		self.commit()
		self.refresh(job)

		return job

	def fail_job(
		self,
		job: Job,
		error_message: str,
	) -> Job:

		job.status = "FAILED"
		job.current_stage = "FAILED"
		job.error_message = error_message
		job.completed_at = datetime.utcnow()

		self.commit()
		self.refresh(job)

		return job