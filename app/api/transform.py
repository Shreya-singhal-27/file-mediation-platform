from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_transformation_manager
from app.schemas.transformation import OutputSchema, TransformationFieldMapping, TransformationResult
from app.services.transformation.transformation_manager import TransformationManager


class TransformationExecutionRequest(BaseModel):
	"""Represents a transformation execution request submitted by the API layer."""

	records: list[dict[str, Any]] = Field(default_factory=list)
	mappings: list[TransformationFieldMapping] = Field(default_factory=list)
	output_schema: OutputSchema | None = None


router = APIRouter(prefix="/transformations", tags=["Transformation"])


@router.post("/execute", response_model=TransformationResult)
def execute_transformation(
	request: TransformationExecutionRequest,
	transformation_manager: TransformationManager = Depends(get_transformation_manager),
) -> TransformationResult:
	"""Transform decoded records into the configured output structure."""
	try:
		return transformation_manager.transform_records(
			request.records,
			request.mappings,
			request.output_schema,
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		) from exc

