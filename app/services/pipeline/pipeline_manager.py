from __future__ import annotations

from app.business.job_service import JobService
from app.models.pipeline import Pipeline
from app.models.user import User
from app.services.audit.audit_service import AuditService
from app.services.pipeline.pipeline_engine import PipelineEngine


from app.services.pipeline.pipeline_context import PipelineExecutionContext, PipelineRunReport


class PipelineManager:
	"""Application-facing facade over the lower-level pipeline engine."""

	def __init__(self, pipeline_engine: PipelineEngine | None = None) -> None:
		self._pipeline_engine = pipeline_engine or PipelineEngine()

	def run_pipeline(
		self,
		pipeline: Pipeline,
		started_by: User,
		job_service: JobService,
		audit_service: AuditService,
	) -> PipelineRunReport:
		"""Run a configured pipeline and return the execution report."""
		return self._pipeline_engine.execute(pipeline, started_by, job_service, audit_service)

