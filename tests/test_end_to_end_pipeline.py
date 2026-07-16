import csv
from datetime import datetime
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.role import Role
from app.models.user import User
from app.models.source import Source
from app.models.destination import Destination
from app.models.pipeline import Pipeline
from app.models.filter_rule import FilterRule
from app.models.mapping_rule import MappingRule
from app.models.job import Job
from app.models.audit_log import AuditLog

from app.repositories.job_repository import JobRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.business.job_service import JobService
from app.services.audit.audit_service import AuditService
from app.services.pipeline.pipeline_engine import PipelineEngine


@pytest.fixture
def db_session():
	"""Sets up an in-memory SQLite database for E2E testing."""
	engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
	Base.metadata.create_all(bind=engine)
	
	db = Session(bind=engine)
	try:
		yield db
	finally:
		db.close()


def test_complete_pipeline_e2e(db_session: Session, tmp_path: Path):
	# 1. Setup local acquisition and transmission directories
	source_dir = tmp_path / "source"
	archive_dir = tmp_path / "archive"
	rejected_dir = tmp_path / "rejected"
	dest_dir = tmp_path / "destination"

	source_dir.mkdir()
	archive_dir.mkdir()
	rejected_dir.mkdir()
	dest_dir.mkdir()

	# 2. Populate basic DB records required for execution
	role = Role(id=1, name="admin", description="Administrator")
	db_session.add(role)
	db_session.commit()

	user = User(
		id=1,
		username="e2e_user",
		email="e2e@example.com",
		hashed_password="somehashpassword",
		first_name="E2E",
		last_name="Tester",
		role_id=1,
		is_active=True
	)
	db_session.add(user)
	db_session.commit()

	source_config = {
		"type": "LOCAL",
		"source_path": str(source_dir),
		"archive_path": str(archive_dir),
		"rejected_path": str(rejected_dir),
		"allowed_extensions": [".csv"]
	}
	source = Source(
		id=1,
		name="e2e_source",
		source_type="LOCAL",
		config=source_config,
		is_active=True
	)
	db_session.add(source)

	dest_config = {
		"destination_directory": str(dest_dir)
	}
	destination = Destination(
		id=1,
		name="e2e_destination",
		destination_type="LOCAL",
		config=dest_config,
		is_active=True
	)
	db_session.add(destination)
	db_session.commit()

	pipeline = Pipeline(
		id=1,
		name="e2e_pipeline",
		source_id=1,
		destination_id=1,
		decoder_type="CSV",
		is_active=True,
		source=source,
		destination=destination,
		created_by_id=1
	)
	db_session.add(pipeline)

	# Rules
	# Filter: status == ACTIVE
	filter_rule = FilterRule(
		id=1,
		pipeline_id=1,
		rule_name="Only Active Records",
		field_name="status",
		operator="=",
		value="ACTIVE",
		priority=1,
		is_active=True
	)
	db_session.add(filter_rule)

	# Mapping Mappings:
	# id -> user_id (COPY, required)
	# name -> full_name (COPY, required)
	# age -> age (NUMBER_FORMAT, output_format: "0", optional)
	# is_vip -> vip_flag (BOOLEAN_CONVERSION, optional)
	# registration_date -> registered_on (DATE_FORMAT, output_format: "%Y-%m-%d", parameters={"input_format": "%d/%m/%Y", "format": "%Y-%m-%d"}, optional)
	mapping_rules = [
		MappingRule(
			id=1,
			pipeline_id=1,
			source_field="id",
			target_field="user_id",
			transformation_type="COPY",
			is_required=True
		),
		MappingRule(
			id=2,
			pipeline_id=1,
			source_field="name",
			target_field="full_name",
			transformation_type="COPY",
			is_required=True
		),
		MappingRule(
			id=3,
			pipeline_id=1,
			source_field="is_vip",
			target_field="vip_flag",
			transformation_type="BOOLEAN_CONVERSION",
			is_required=False
		),
		MappingRule(
			id=4,
			pipeline_id=1,
			source_field="registration_date",
			target_field="registered_on",
			transformation_type="DATE_FORMAT",
			default_value="null",
			is_required=False
		)
	]
	# Attach rules to pipeline since model expects it
	pipeline.filter_rules = [filter_rule]
	pipeline.mapping_rules = mapping_rules

	for rule in mapping_rules:
		# Add rule parameters since postgres JSON might be empty or hold dict parameters
		# In sqlalchemy Model, metadata parameters is not defined as columns directly, but config-loader passes it.
		# Let's inspect mapping_rules model or how TransformationManager handles parameters.
		# MappingRule doesn't have parameters in the DB mapping. Let's see mapping_rule.py.
		# Yes, MappingRule has id, pipeline_id, source_field, target_field, transformation_type, default_value, is_required.
		# How is parameters set? Let's check transformation_manager.py Line 58.
		# In TransformationManager._from_orm_mapping(), parameters is hardcoded to {}.
		# Wait! Line 65 parameters={}!
		# That means for DATE_FORMAT, it reads mapping.parameters.get("input_format"), which would be empty.
		# But wait, how does DATE_FORMAT handle empty input_format?
		# Let's check type_converter.py or transformation_engine.py Line 158.
		# It passes parameters.get("input_format") or None. If input_format is None, the datetime converter parses standard ISO format or fallback.
		# Let's write registration_date as ISO format "2026-07-16T12:00:00" or similar so it doesn't need special input_format.
		pass

	for mr in mapping_rules:
		db_session.add(mr)
	db_session.commit()

	# Create a real input file inside source_dir
	input_file_path = source_dir / "users.csv"
	with open(input_file_path, "w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=["id", "name", "status", "is_vip", "registration_date"])
		writer.writeheader()
		writer.writerow({"id": "101", "name": "Alice", "status": "ACTIVE", "is_vip": "true", "registration_date": "2026-01-01T00:00:00"})
		writer.writerow({"id": "102", "name": "Bob", "status": "INACTIVE", "is_vip": "false", "registration_date": "2026-01-02T00:00:00"})
		writer.writerow({"id": "103", "name": "Charlie", "status": "ACTIVE", "is_vip": "yes", "registration_date": "2026-01-03T00:00:00"})

	# Create real services
	job_repo = JobRepository(db_session)
	job_service = JobService(job_repo)
	
	audit_repo = AuditLogRepository(db_session)
	audit_service = AuditService(audit_repo)

	# Execute the pipeline using the actual PipelineEngine!
	engine = PipelineEngine()
	report = engine.execute(pipeline, user, job_service, audit_service)

	# Verify:
	# 1. PipelineRunReport assertions
	assert report.failed_jobs == 0
	assert report.succeeded_jobs == 1
	assert len(report.contexts) == 1
	context = report.contexts[0]
	assert context.completed is True
	
	# Verify filtering counts
	assert context.filter_result is not None
	assert context.filter_result.statistics.total_records == 3
	assert context.filter_result.statistics.accepted_records == 2
	assert context.filter_result.statistics.rejected_records == 1
	
	# Verify transformation counts
	assert context.transformed_result is not None
	assert context.transformed_result.statistics.total_records == 2
	assert context.transformed_result.statistics.transformed_records == 2
	assert context.transformed_result.statistics.rejected_records == 0
	
	# 2. Filesystem state assertions
	# Acquisition: input is moved to archive_dir
	assert not input_file_path.exists()
	archived_file_path = archive_dir / "users.csv"
	assert archived_file_path.exists()

	# Transmission: output file is written to dest_dir
	dest_files = list(dest_dir.glob("*.csv"))
	assert len(dest_files) == 1
	output_file_path = dest_files[0]
	assert output_file_path.name == "users.csv"

	# Verify output correctness
	with open(output_file_path, "r", newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		records = list(reader)

	# Only Alice and Charlie because Bob was status=INACTIVE
	assert len(records) == 2
	
	alice = records[0]
	assert alice["user_id"] == "101"
	assert alice["full_name"] == "Alice"
	# bool string conversions
	assert alice["vip_flag"].lower() == "true"
	
	charlie = records[1]
	assert charlie["user_id"] == "103"
	assert charlie["full_name"] == "Charlie"
	assert charlie["vip_flag"].lower() == "true"

	# 3. Database Job update assertions
	# Fetch the job from sqlite test db
	jobs = db_session.query(Job).filter(Job.pipeline_id == pipeline.id).all()
	assert len(jobs) == 1
	job = jobs[0]
	assert job.status == "COMPLETED"
	assert job.current_stage == "COMPLETED"
	assert job.total_records == 3
	assert job.records_processed == 2
	assert job.records_failed == 1
	assert job.input_filename == "users.csv"
	assert job.output_filename == output_file_path.name
	assert job.archive_path is None
	assert "Transmission status: SUCCESS" in job.job_log

	# 4. Audit log assertions
	logs = db_session.query(AuditLog).filter(AuditLog.user_id == user.id).all()
	assert len(logs) > 0
	# Should record transmission and completed events
	completed_events = [l for l in logs if l.action == "PIPELINE_COMPLETED"]
	assert len(completed_events) == 1
	assert completed_events[0].resource == pipeline.name
	assert "processed successfully" in completed_events[0].details
