# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
End-to-End Pipeline Runner
===========================
This script demonstrates the COMPLETE pipeline flow:

  1. Create directories (source, archive, rejected, destination)
  2. Place a sample CSV input file in the source directory
  3. Seed DB with: user, source config, destination config, pipeline,
     filter rules, and mapping rules
  4. Execute the pipeline programmatically
  5. Verify: output file, archived input, job record, audit log

Usage:
    cd c:\\Users\\hp\\Desktop\\file-mediation-platform
    venv\\Scripts\\python.exe scripts\\run_pipeline_e2e.py
"""

import csv
import json
import os
import shutil
import tempfile
from pathlib import Path

# ── Directories ─────────────────────────────
BASE_DIR = Path(tempfile.gettempdir()) / "file_mediation_e2e"
SOURCE_DIR = BASE_DIR / "source"
ARCHIVE_DIR = BASE_DIR / "archive"
REJECTED_DIR = BASE_DIR / "rejected"
DESTINATION_DIR = BASE_DIR / "destination"

for d in (SOURCE_DIR, ARCHIVE_DIR, REJECTED_DIR, DESTINATION_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Create sample CSV input file ────────────
INPUT_FILENAME = "employees.csv"
INPUT_PATH = SOURCE_DIR / INPUT_FILENAME

SAMPLE_DATA = [
    {"emp_id": "E001", "full_name": "Alice Johnson",  "department": "Engineering", "salary": "85000", "status": "ACTIVE"},
    {"emp_id": "E002", "full_name": "Bob Williams",   "department": "Marketing",   "salary": "62000", "status": "ACTIVE"},
    {"emp_id": "E003", "full_name": "Charlie Brown",  "department": "Engineering", "salary": "91000", "status": "INACTIVE"},
    {"emp_id": "E004", "full_name": "Diana Martinez", "department": "HR",          "salary": "58000", "status": "ACTIVE"},
    {"emp_id": "E005", "full_name": "Eve Davis",      "department": "Engineering", "salary": "95000", "status": "ACTIVE"},
    {"emp_id": "E006", "full_name": "Frank Wilson",   "department": "Marketing",   "salary": "45000", "status": "ACTIVE"},
]

with open(INPUT_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["emp_id", "full_name", "department", "salary", "status"])
    writer.writeheader()
    writer.writerows(SAMPLE_DATA)

print(f"\n{'='*60}")
print(f"  INPUT FILE CREATED")
print(f"{'='*60}")
print(f"  Location : {INPUT_PATH}")
print(f"  Records  : {len(SAMPLE_DATA)}")
print(f"\n  Contents:")
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    for line in f:
        print(f"    {line.rstrip()}")


# ── DB Setup ────────────────────────────────
print(f"\n{'='*60}")
print(f"  SETTING UP DATABASE")
print(f"{'='*60}")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DB_URL = "postgresql+psycopg2://postgres:postgres123@localhost:5432/file_mediation"
engine = create_engine(DB_URL)


def db_execute(sql, **params):
    with engine.connect() as conn:
        conn.execute(text(sql), params)
        conn.commit()


def db_query(sql, **params):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params)
        return [dict(zip(result.keys(), row)) for row in result.fetchall()]


# Clean previous test runs
db_execute("DELETE FROM audit_logs WHERE resource = 'e2e_test_pipeline'")
db_execute("DELETE FROM jobs WHERE pipeline_id IN (SELECT id FROM pipelines WHERE name = 'e2e_test_pipeline')")
db_execute("DELETE FROM filter_rules WHERE pipeline_id IN (SELECT id FROM pipelines WHERE name = 'e2e_test_pipeline')")
db_execute("DELETE FROM mapping_rules WHERE pipeline_id IN (SELECT id FROM pipelines WHERE name = 'e2e_test_pipeline')")
db_execute("DELETE FROM pipelines WHERE name = 'e2e_test_pipeline'")
db_execute("DELETE FROM sources WHERE name = 'e2e_local_source'")
db_execute("DELETE FROM destinations WHERE name = 'e2e_local_dest'")
db_execute("DELETE FROM users WHERE email = 'e2e_runner@example.com'")

# 1. Create test user
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_pw = pwd_context.hash("E2EPassword123!")

db_execute("""
    INSERT INTO users (username, email, first_name, last_name, hashed_password, role_id, is_active, created_at, updated_at)
    VALUES ('e2e_runner', 'e2e_runner@example.com', 'E2E', 'Runner', :hpw, 2, true, NOW(), NOW())
""", hpw=hashed_pw)

user_row = db_query("SELECT id FROM users WHERE email = 'e2e_runner@example.com'")[0]
user_id = user_row["id"]
print(f"  [OK] User created (id={user_id})")

# 2. Create source
source_config = {
    "type": "LOCAL",
    "source_path": str(SOURCE_DIR),
    "archive_path": str(ARCHIVE_DIR),
    "rejected_path": str(REJECTED_DIR),
    "allowed_extensions": [".csv"],
}

db_execute("""
    INSERT INTO sources (name, source_type, config, is_active, created_at, updated_at)
    VALUES ('e2e_local_source', 'LOCAL', CAST(:cfg AS jsonb), true, NOW(), NOW())
""", cfg=json.dumps(source_config))

source_id = db_query("SELECT id FROM sources WHERE name = 'e2e_local_source'")[0]["id"]
print(f"  [OK] Source created (id={source_id}), reading from: {SOURCE_DIR}")

# 3. Create destination
dest_config = {
    "destination_directory": str(DESTINATION_DIR),
}

db_execute("""
    INSERT INTO destinations (name, destination_type, config, is_active, created_at, updated_at)
    VALUES ('e2e_local_dest', 'LOCAL', CAST(:cfg AS jsonb), true, NOW(), NOW())
""", cfg=json.dumps(dest_config))

dest_id = db_query("SELECT id FROM destinations WHERE name = 'e2e_local_dest'")[0]["id"]
print(f"  [OK] Destination created (id={dest_id}), writing to: {DESTINATION_DIR}")

# 4. Create pipeline
db_execute("""
    INSERT INTO pipelines (name, description, source_id, destination_id, created_by_id,
                          is_active, decoder_type, output_format, archive_enabled, retry_count,
                          created_at, updated_at)
    VALUES ('e2e_test_pipeline', 'Full E2E test pipeline', :sid, :did, :uid,
            true, 'CSV', 'CSV', true, 3, NOW(), NOW())
""", sid=source_id, did=dest_id, uid=user_id)

pipeline_id = db_query("SELECT id FROM pipelines WHERE name = 'e2e_test_pipeline'")[0]["id"]
print(f"  [OK] Pipeline created (id={pipeline_id})")

# 5. Create filter rules (keep only ACTIVE employees with salary >= 50000)
db_execute("""
    INSERT INTO filter_rules (pipeline_id, rule_name, field_name, operator, value, priority, is_active, created_at)
    VALUES (:pid, 'Active Only', 'status', '=', 'ACTIVE', 1, true, NOW())
""", pid=pipeline_id)
db_execute("""
    INSERT INTO filter_rules (pipeline_id, rule_name, field_name, operator, value, priority, is_active, created_at)
    VALUES (:pid, 'Min Salary', 'salary', '>=', '50000', 2, true, NOW())
""", pid=pipeline_id)
print(f"  [OK] Filter rules created (status=ACTIVE, salary>=50000)")

# 6. Create mapping rules (rename & transform fields)
mapping_rules = [
    ("emp_id",      "employee_id",     "COPY",       True),
    ("full_name",   "name",            "COPY",       True),
    ("department",  "dept",            "COPY",       False),
    ("salary",      "annual_salary",   "COPY",       False),
    ("status",      "is_active",       "COPY",       False),
]

for src, tgt, ttype, required in mapping_rules:
    db_execute("""
        INSERT INTO mapping_rules (pipeline_id, source_field, target_field, transformation_type, is_required, created_at)
        VALUES (:pid, :src, :tgt, :tt, :req, NOW())
    """, pid=pipeline_id, src=src, tgt=tgt, tt=ttype, req=required)

print(f"  [OK] Mapping rules created ({len(mapping_rules)} field mappings)")


# ── Execute Pipeline ────────────────────────
print(f"\n{'='*60}")
print(f"  EXECUTING PIPELINE")
print(f"{'='*60}")

from sqlalchemy.orm import Session as SASession, joinedload

# Build a proper SQLAlchemy session to load ORM objects
from app.database.session import SessionLocal
from app.models.pipeline import Pipeline
from app.models.user import User
from app.models.source import Source
from app.models.destination import Destination
from app.repositories.job_repository import JobRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.business.job_service import JobService
from app.services.audit.audit_service import AuditService
from app.services.pipeline.pipeline_engine import PipelineEngine

session = SessionLocal()

try:
    # Load full ORM objects with relationships
    pipeline = session.query(Pipeline).options(
        joinedload(Pipeline.source),
        joinedload(Pipeline.destination),
        joinedload(Pipeline.filter_rules),
        joinedload(Pipeline.mapping_rules),
        joinedload(Pipeline.created_by),
    ).filter(Pipeline.id == pipeline_id).one()

    user = session.query(User).filter(User.id == user_id).one()

    print(f"  Pipeline : {pipeline.name}")
    print(f"  Source   : {pipeline.source.name} ({pipeline.source.source_type})")
    print(f"  Dest     : {pipeline.destination.name} ({pipeline.destination.destination_type})")
    print(f"  Filters  : {len(pipeline.filter_rules)} active rules")
    print(f"  Mappings : {len(pipeline.mapping_rules)} field mappings")
    print(f"  Input    : {INPUT_PATH}")
    print()

    # Create services
    job_repo = JobRepository(session)
    audit_repo = AuditLogRepository(session)
    job_service = JobService(job_repo)
    audit_service = AuditService(audit_repo)

    # Run!
    pipeline_engine = PipelineEngine()
    report = pipeline_engine.execute(pipeline, user, job_service, audit_service)

    print(f"\n  Pipeline execution completed!")
    print(f"  Total jobs      : {report.total_jobs}")
    print(f"  Succeeded       : {report.succeeded_jobs}")
    print(f"  Failed          : {report.failed_jobs}")

    if report.errors:
        print(f"  Errors:")
        for err in report.errors:
            print(f"    - {err}")
finally:
    session.close()


# ── Verify Results ──────────────────────────
print(f"\n{'='*60}")
print(f"  VERIFICATION")
print(f"{'='*60}")

passed = 0
failed = 0

def check(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  [PASS] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}  ->  {detail}")
        failed += 1


# 1. Output file exists in destination
output_files = list(DESTINATION_DIR.glob("*.csv"))
check("Output CSV exists in destination", len(output_files) >= 1, f"found {len(output_files)} files")

if output_files:
    output_path = output_files[0]
    print(f"\n  Output file: {output_path}")

    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        output_records = list(reader)

    print(f"  Output records: {len(output_records)}")
    print(f"\n  Output contents:")
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            print(f"    {line.rstrip()}")

    # Expected: Alice (85k, ACTIVE), Bob (62k, ACTIVE), Diana (58k, ACTIVE), Eve (95k, ACTIVE)
    # Rejected: Charlie (INACTIVE), Frank (45k < 50k)
    # NOTE: The filter engine rejects on first failing rule. This means records
    # must pass ALL rules to be accepted. The exact count depends on filter
    # behavior (short-circuit reject on first fail):
    # - Charlie fails status=ACTIVE -> rejected
    # - Frank: salary=45000 fails >=50000 -> rejected
    # So 4 records should pass.

    check("4 output records (filtered from 6)", len(output_records) == 4,
          f"got {len(output_records)}")

    if output_records:
        # Check field renaming happened
        first_record = output_records[0]
        check("Field 'employee_id' exists (renamed from emp_id)", "employee_id" in first_record,
              list(first_record.keys()))
        check("Field 'name' exists (renamed from full_name)", "name" in first_record,
              list(first_record.keys()))
        check("Field 'dept' exists (renamed from department)", "dept" in first_record,
              list(first_record.keys()))
        check("Field 'annual_salary' exists (renamed from salary)", "annual_salary" in first_record,
              list(first_record.keys()))

        output_ids = [r.get("employee_id") for r in output_records]
        check("Alice (E001) in output", "E001" in output_ids, output_ids)
        check("Bob (E002) in output", "E002" in output_ids, output_ids)
        check("Diana (E004) in output", "E004" in output_ids, output_ids)
        check("Eve (E005) in output", "E005" in output_ids, output_ids)
        check("Charlie (E003) NOT in output (INACTIVE)", "E003" not in output_ids, output_ids)
        check("Frank (E006) NOT in output (salary<50k)", "E006" not in output_ids, output_ids)


# 2. Input file archived
archive_files = list(ARCHIVE_DIR.glob("*.csv"))
check("Input file archived", len(archive_files) >= 1, f"found {len(archive_files)} in archive")
check("Input file removed from source", not INPUT_PATH.exists(), "still in source dir")


# 3. Job record in DB
jobs = db_query("""
    SELECT id, status, current_stage, input_filename, output_filename,
           total_records, records_processed, records_failed, execution_time_ms,
           file_checksum, job_log
    FROM jobs WHERE pipeline_id = :pid ORDER BY id DESC LIMIT 1
""", pid=pipeline_id)

check("Job record exists in DB", len(jobs) >= 1)
if jobs:
    job = jobs[0]
    check("Job status is COMPLETED", job["status"] == "COMPLETED", job["status"])
    check("Job stage is COMPLETED", job["current_stage"] == "COMPLETED", job["current_stage"])
    check("Input filename recorded", job["input_filename"] == INPUT_FILENAME, job["input_filename"])
    check("Output filename recorded", job["output_filename"] is not None, job["output_filename"])
    check("Total records = 6", job["total_records"] == 6, job["total_records"])
    check("Records processed = 4", job["records_processed"] == 4, job["records_processed"])
    check("Records failed = 2", job["records_failed"] == 2, job["records_failed"])
    check("Execution time recorded", job["execution_time_ms"] is not None, job["execution_time_ms"])
    check("File checksum recorded", job["file_checksum"] is not None)

    if job["job_log"]:
        print(f"\n  Job Log:")
        for line in job["job_log"].split("\n"):
            print(f"    {line}")


# 4. Audit log
audits = db_query("""
    SELECT action, resource, details FROM audit_logs
    WHERE resource = 'e2e_test_pipeline' ORDER BY id DESC LIMIT 5
""")
check("Audit log entry exists", len(audits) >= 1)
if audits:
    latest = audits[0]
    check("Audit action is PIPELINE_COMPLETED", latest["action"] == "PIPELINE_COMPLETED", latest["action"])
    check("Audit resource is pipeline name", latest["resource"] == "e2e_test_pipeline")
    print(f"\n  Audit Log:")
    for a in audits:
        print(f"    [{a['action']}] {a['details']}")


# ── Summary ─────────────────────────────────
print(f"\n{'='*60}")
print(f"  RESULTS:  {passed} passed, {failed} failed")
print(f"{'='*60}")

print(f"\n  KEY PATHS:")
print(f"    Input (source)       : {SOURCE_DIR}")
print(f"    Output (destination) : {DESTINATION_DIR}")
print(f"    Archived input       : {ARCHIVE_DIR}")
print(f"    Rejected files       : {REJECTED_DIR}")

# Cleanup temp dir option
print(f"\n  To clean up temp files: delete {BASE_DIR}")

sys.exit(1 if failed else 0)
