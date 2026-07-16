from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.models.destination import Destination
from app.models.job import Job
from app.models.pipeline import Pipeline
from app.models.source import Source
from app.models.user import User
from app.schemas.acquisition import AcquiredFile
from app.services.filtering.filter_engine import FilterResult
from app.services.transformation.transformation_manager import TransformationResult
from app.services.transmission.base_transmitter import TransmissionResult


@dataclass(slots=True)
class PipelineExecutionContext:
	"""Holds the state for processing a single acquired file through the pipeline."""

	pipeline: Pipeline
	started_by: User
	source: Source
	destination: Destination
	acquired_file: AcquiredFile
	job: Job | None = None
	stage: str = "ACQUISITION"
	decoded_records: list[dict[str, Any]] = field(default_factory=list)
	filter_result: FilterResult | None = None
	transformed_result: TransformationResult | None = None
	transmission_result: TransmissionResult | None = None
	output_file: Path | None = None
	logs: list[str] = field(default_factory=list)
	completed: bool = False
	error_message: str | None = None


@dataclass(slots=True)
class PipelineRunReport:
	"""Summarizes a complete pipeline run across one or more files."""

	pipeline_id: int
	pipeline_name: str
	total_jobs: int = 0
	succeeded_jobs: int = 0
	failed_jobs: int = 0
	contexts: list[PipelineExecutionContext] = field(default_factory=list)
	errors: list[str] = field(default_factory=list)
