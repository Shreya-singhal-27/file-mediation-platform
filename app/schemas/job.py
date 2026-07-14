from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobBase(BaseModel):
    status: str

    current_stage: str

    input_filename: str | None = None

    output_filename: str | None = None


class JobCreate(BaseModel):
    pipeline_id: int


class JobUpdate(BaseModel):
    status: str | None = None

    current_stage: str | None = None

    output_filename: str | None = None

    records_processed: int | None = None

    records_failed: int | None = None

    total_records: int | None = None

    execution_time_ms: int | None = None

    file_checksum: str | None = None

    archive_path: str | None = None

    error_message: str | None = None

    job_log: str | None = None

    completed_at: datetime | None = None


class JobResponse(JobBase):
    id: int

    pipeline_id: int

    started_by_id: int

    total_records: int

    records_processed: int

    records_failed: int

    execution_time_ms: int | None

    file_checksum: str | None

    archive_path: str | None

    error_message: str | None

    job_log: str | None

    started_at: datetime

    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)