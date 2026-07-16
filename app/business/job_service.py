from app.models.job import Job
from app.models.pipeline import Pipeline
from app.models.user import User
from app.repositories.job_repository import JobRepository


class JobService:

	def __init__(
		self,
		job_repository: JobRepository,
	):
		self.job_repository = job_repository

	def create_job(
		self,
		pipeline: Pipeline,
		user: User,
		input_filename: str,
	) -> Job:

		job = Job(
			pipeline_id=pipeline.id,
			started_by_id=user.id,
			status="RUNNING",
			current_stage="ACQUISITION",
			input_filename=input_filename,
		)

		return self.job_repository.create(job)

	def get_job(
		self,
		job_id: int,
	) -> Job | None:

		return self.job_repository.get_by_id(job_id)

	def get_latest_job(
		self,
		pipeline_id: int,
	) -> Job | None:

		return self.job_repository.get_latest_job(
			pipeline_id,
		)

	def get_pipeline_jobs(
		self,
		pipeline_id: int,
	) -> list[Job]:

		return self.job_repository.get_by_pipeline(
			pipeline_id,
		)

	def complete_job(
		self,
		job: Job,
	) -> Job:

		return self.job_repository.complete_job(job)

	def update_job(
		self,
		job: Job,
	) -> Job:

		return self.job_repository.update(job)

	def append_job_log(
		self,
		job: Job,
		message: str,
	) -> Job:

		job.job_log = (
			f"{job.job_log}\n{message}" if job.job_log else message
		)

		return self.job_repository.update(job)


	def fail_job(
		self,
		job: Job,
		error_message: str,
	) -> Job:

		return self.job_repository.fail_job(
			job,
			error_message,
		)