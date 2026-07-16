"""Tests for the transmission module and the pipeline orchestration layer."""

from __future__ import annotations

import csv
from pathlib import Path

from app.models.destination import Destination
from app.models.filter_rule import FilterRule
from app.models.job import Job
from app.models.mapping_rule import MappingRule
from app.models.pipeline import Pipeline
from app.models.role import Role
from app.models.source import Source
from app.models.user import User
from app.services.pipeline.pipeline_engine import PipelineEngine
from app.services.transmission.base_transmitter import TransmissionTarget
from app.services.transmission.transmission_manager import TransmissionManager, TransmissionRetryPolicy
from app.utils.file_utils import FileUtils


class FakeJobService:
	"""Minimal job service used to validate orchestration without a database."""

	def __init__(self) -> None:
		self.created_jobs: list[Job] = []
		self.updated_jobs: list[Job] = []

	def create_job(self, pipeline: Pipeline, user: User, input_filename: str) -> Job:
		job = Job(
			pipeline_id=pipeline.id,
			started_by_id=user.id,
			status="RUNNING",
			current_stage="ACQUISITION",
			input_filename=input_filename,
		)
		self.created_jobs.append(job)
		return job

	def update_job(self, job: Job) -> Job:
		self.updated_jobs.append(job)
		return job


class FakeAuditService:
	"""Captures audit events generated during pipeline execution."""

	def __init__(self) -> None:
		self.events: list[dict[str, str]] = []

	def record_pipeline_event(self, user_id: int, pipeline_name: str, stage: str, details: str) -> None:
		self.events.append(
			{
				"user_id": str(user_id),
				"pipeline_name": pipeline_name,
				"stage": stage,
				"details": details,
			}
		)


def test_local_transmission_manager_copies_and_archives(tmp_path: Path) -> None:
	"""Local transmission should copy the file, archive the source, and record a checksum."""
	source_file = tmp_path / "output.csv"
	source_file.write_text("msisdn,status\n123,active\n", encoding="utf-8")
	destination_dir = tmp_path / "destination"
	archive_dir = tmp_path / "archive"

	manager = TransmissionManager(retry_policy=TransmissionRetryPolicy(attempts=1, delay_seconds=0.0))
	result = manager.transmit_file(
		source_file,
		{
			"destination_type": "LOCAL",
			"config": {
				"destination_directory": str(destination_dir),
				"archive_directory": str(archive_dir),
			},
		},
	)

	assert result.success is True
	assert result.status == "SUCCESS"
	assert (destination_dir / source_file.name).exists()
	assert (archive_dir / source_file.name).exists()
	assert not source_file.exists()
	assert result.checksum == FileUtils.calculate_checksum(archive_dir / source_file.name, algorithm="sha256")
	assert result.attempts == 1


def test_pipeline_engine_processes_file_end_to_end(tmp_path: Path) -> None:
	"""The pipeline engine should acquire, decode, filter, transform, transmit, archive, and audit a file."""
	source_dir = tmp_path / "source"
	source_dir.mkdir()
	source_archive_dir = tmp_path / "source-archive"
	source_rejected_dir = tmp_path / "source-rejected"
	destination_dir = tmp_path / "destination"
	destination_archive_dir = tmp_path / "destination-archive"
	staging_dir = tmp_path / "staging"
	input_file = source_dir / "cdr.csv"

	with open(input_file, "w", newline="", encoding="utf-8") as stream:
		writer = csv.writer(stream)
		writer.writerow(["msisdn", "status", "amount"])
		writer.writerow(["111", "active", "10"])
		writer.writerow(["222", "inactive", "20"])

	source = Source(
		id=1,
		name="LocalSource",
		source_type="LOCAL",
		config={
			"source_path": str(source_dir),
			"archive_path": str(source_archive_dir),
			"rejected_path": str(source_rejected_dir),
			"allowed_extensions": [".csv"],
		},
	)
	destination = Destination(
		id=1,
		name="LocalDestination",
		destination_type="LOCAL",
		config={
			"destination_directory": str(destination_dir),
			"archive_directory": str(destination_archive_dir),
			"staging_directory": str(staging_dir),
			"retry_count": 1,
		},
	)
	pipeline = Pipeline(
		id=1,
		name="CDR Pipeline",
		description="Test pipeline",
		source_id=source.id,
		destination_id=destination.id,
		created_by_id=1,
		decoder_type="CSV",
		output_format="CSV",
	)
	pipeline.source = source
	pipeline.destination = destination
	pipeline.filter_rules = [
		FilterRule(
			id=1,
			pipeline_id=pipeline.id,
			rule_name="ActiveOnly",
			field_name="status",
			operator="=",
			value="active",
			logical_operator=None,
			priority=1,
			is_active=True,
		)
	]
	pipeline.mapping_rules = [
		MappingRule(
			id=1,
			pipeline_id=pipeline.id,
			source_field="msisdn",
			target_field="msisdn",
			transformation_type="COPY",
			default_value=None,
			is_required=True,
		),
		MappingRule(
			id=2,
			pipeline_id=pipeline.id,
			source_field="status",
			target_field="status",
			transformation_type="COPY",
			default_value=None,
			is_required=True,
		),
		MappingRule(
			id=3,
			pipeline_id=pipeline.id,
			source_field="amount",
			target_field="amount",
			transformation_type="COPY",
			default_value=None,
			is_required=True,
		),
	]

	user = User(
		id=99,
		username="tester",
		email="tester@example.com",
		hashed_password="hashed",
		first_name="Test",
		last_name="User",
		role_id=1,
	)

	job_service = FakeJobService()
	audit_service = FakeAuditService()
	engine = PipelineEngine()
	report = engine.execute(pipeline, user, job_service, audit_service)

	assert report.pipeline_id == pipeline.id
	assert report.total_jobs == 1
	assert report.succeeded_jobs == 1
	assert report.failed_jobs == 0
	assert len(report.contexts) == 1

	context = report.contexts[0]
	assert context.completed is True
	assert context.filter_result is not None
	assert context.filter_result.statistics.rejected_records == 1
	assert context.transformed_result is not None
	assert context.transformed_result.statistics.transformed_records == 1
	assert context.transmission_result is not None
	assert context.transmission_result.success is True

	assert not input_file.exists()
	assert (source_archive_dir / input_file.name).exists()
	assert (destination_dir / "cdr.csv").exists()
	assert (destination_archive_dir / "cdr.csv").exists()
	assert job_service.updated_jobs[-1].status == "COMPLETED"
	assert audit_service.events[-1]["stage"] == "COMPLETED"
	assert len(job_service.created_jobs) == 1
