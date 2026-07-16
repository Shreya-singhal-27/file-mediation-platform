from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_filter_manager
from app.schemas.filtering import FilterCondition, FilterGroup, FilterResult
from app.services.filtering.filter_manager import FilterManager


class FilterExecutionRequest(BaseModel):
	"""Represents a filtering execution request submitted by the API layer."""

	records: list[dict[str, Any]] = Field(default_factory=list)
	rules: list[FilterCondition | FilterGroup] = Field(default_factory=list)


router = APIRouter(prefix="/filtering", tags=["Filtering"])


@router.post("/evaluate", response_model=FilterResult)
def evaluate_filters(
	request: FilterExecutionRequest,
	filter_manager: FilterManager = Depends(get_filter_manager),
) -> FilterResult:
	"""Evaluate decoded records against the configured filter rules."""
	try:
		return filter_manager.filter_records(request.records, request.rules)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		) from exc

