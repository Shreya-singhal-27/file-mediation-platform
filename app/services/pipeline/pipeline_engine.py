from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.business.job_service import JobService
from app.models.pipeline import Pipeline
from app.models.source import Source
from app.models.user import User
from app.services.audit.audit_service import AuditService
from app.services.pipeline.pipeline_context import PipelineExecutionContext, PipelineRunReport
from app.services.pipeline.pipeline_executor import PipelineExecutor
from app.utils.file_utils import FileUtils


@dataclass(slots=True)
class PipelineSourceBundle:
	"""Keeps the source metadata together with the temporary configuration path."""

	config_path: Path
	acquisition_manager: Any


class PipelineEngine:
	"""Coordinates acquisition, downstream processing, job updates, and audit logging."""

	def __init__(
		self,
		executor: PipelineExecutor | None = None,
		job_service: JobService | None = None,
		audit_service: AuditService | None = None,
	) -> None:
		self._executor = executor or PipelineExecutor()
		self._job_service = job_service
		self._audit_service = audit_service

	def execute(
		self,
		pipeline: Pipeline,
		started_by: User,
		job_service: JobService,
		audit_service: AuditService,
	) -> PipelineRunReport:
		"""Execute the complete mediation workflow for every acquired file."""
		source_bundle = self._build_acquisition_bundle(pipeline.source)
		report = PipelineRunReport(
			pipeline_id=pipeline.id,
			pipeline_name=pipeline.name,
		)

		try:
			source_bundle.acquisition_manager.connect()
			acquired_files = source_bundle.acquisition_manager.fetch_files()
			report.total_jobs = len(acquired_files)
			for acquired_file in acquired_files:
				context = PipelineExecutionContext(
					pipeline=pipeline,
					started_by=started_by,
					source=pipeline.source,
					destination=pipeline.destination,
					acquired_file=acquired_file,
				)
				job = job_service.create_job(
					pipeline,
					started_by,
					acquired_file.filename,
				)
				context.job = job
				job = self._process_single_file(
					context,
					source_bundle.acquisition_manager,
					job_service,
					audit_service,
					report,
				)
				context.job = job
				report.contexts.append(context)
		finally:
			source_bundle.acquisition_manager.disconnect()
			if source_bundle.config_path.exists():
				source_bundle.config_path.unlink(missing_ok=True)

		return report

	def _process_single_file(
		self,
		context: PipelineExecutionContext,
		acquisition_manager: Any,
		job_service: JobService,
		audit_service: AuditService,
		report: PipelineRunReport,
	) -> Any:
		"""Process one acquired file, updating the job and audit trail on completion."""
		job = context.job
		assert job is not None
		started_at = job.started_at

		context = self._executor.execute(context)
		job.total_records = len(context.decoded_records)
		job.records_processed = len(context.transformed_result.transformed_records) if context.transformed_result else 0
		job.records_failed = max(0, job.total_records - job.records_processed)
		job.output_filename = context.output_file.name if context.output_file else None
		job.job_log = "\n".join(context.logs)

		if context.completed and context.transmission_result and context.transmission_result.success:
			job.current_stage = "COMPLETED"
			job.status = "COMPLETED"
			job.file_checksum = context.transmission_result.checksum
			job.archive_path = str(context.transmission_result.archived_path) if context.transmission_result.archived_path else None
			job.completed_at = self._utcnow()
			if started_at is not None:
				job.execution_time_ms = int((job.completed_at - started_at).total_seconds() * 1000)
			else:
				job.execution_time_ms = None
			job_service.update_job(job)
			acquisition_manager.archive_file(context.acquired_file)
			audit_service.record_pipeline_event(
				context.started_by.id,
				context.pipeline.name,
				"COMPLETED",
				f"File '{context.acquired_file.filename}' processed successfully.",
			)
			report.succeeded_jobs += 1
			return job

		failure_reason = context.error_message or (
			context.transmission_result.error_message if context.transmission_result else "Pipeline execution failed."
		)
		job.current_stage = context.stage if context.stage else "FAILED"
		job.status = "FAILED"
		job.error_message = failure_reason
		job.completed_at = self._utcnow()
		if started_at is not None:
			job.execution_time_ms = int((job.completed_at - started_at).total_seconds() * 1000)
		else:
			job.execution_time_ms = None
		job_service.update_job(job)
		if context.output_file is not None and context.output_file.exists():
			context.output_file.unlink(missing_ok=True)
		try:
			acquisition_manager.reject_file(context.acquired_file, failure_reason)
		except Exception:
			pass
		audit_service.record_pipeline_event(
			context.started_by.id,
			context.pipeline.name,
			"FAILED",
			f"File '{context.acquired_file.filename}' failed: {failure_reason}",
		)
		report.failed_jobs += 1
		report.errors.append(failure_reason)
		return job

	def _build_acquisition_bundle(self, source: Source) -> PipelineSourceBundle:
		"""Create an acquisition manager backed by a temporary JSON config file."""
		from app.services.acquisition.acquisition_manager import AcquisitionManager

		temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json", prefix=f"source-{source.id}-", mode="w", encoding="utf-8")
		try:
			json.dump(source.config, temp_file, ensure_ascii=False, indent=2)
			temp_file.flush()
			config_path = Path(temp_file.name)
		finally:
			temp_file.close()

		manager = AcquisitionManager(source.source_type, config_path=str(config_path))
		return PipelineSourceBundle(
			config_path=config_path,
			acquisition_manager=manager,
		)

	@staticmethod
	def _utcnow() -> datetime:
		"""Return a naive UTC timestamp compatible with the existing database models."""
		return datetime.now(timezone.utc).replace(tzinfo=None)
