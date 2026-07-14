from fastapi import APIRouter, Depends, HTTPException, status

from app.business.pipeline_service import PipelineService
from app.core.security import get_current_user
from app.dependencies import get_pipeline_service
from app.schemas.pipeline import (
	PipelineCreate,
	PipelineResponse,
	PipelineUpdate,
)

router = APIRouter(
	prefix="/pipelines",
	tags=["Pipelines"],
)


@router.post(
	"",
	response_model=PipelineResponse,
)
def create_pipeline(
	request: PipelineCreate,
	current_user=Depends(get_current_user),
	service: PipelineService = Depends(
		get_pipeline_service,
	),
):
	try:
		return service.create_pipeline(
			request,
			current_user["user_id"],
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		)


@router.get(
	"",
	response_model=list[PipelineResponse],
)
def list_pipelines(
	service: PipelineService = Depends(
		get_pipeline_service,
	),
):
	return service.get_all_pipelines()


@router.get(
	"/{pipeline_id}",
	response_model=PipelineResponse,
)
def get_pipeline(
	pipeline_id: int,
	service: PipelineService = Depends(
		get_pipeline_service,
	),
):
	try:
		return service.get_pipeline(
			pipeline_id,
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(exc),
		)


@router.put(
	"/{pipeline_id}",
	response_model=PipelineResponse,
)
def update_pipeline(
	pipeline_id: int,
	request: PipelineUpdate,
	service: PipelineService = Depends(
		get_pipeline_service,
	),
):
	try:
		pipeline = service.get_pipeline(
			pipeline_id,
		)

		return service.update_pipeline(
			pipeline,
			request,
		)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		)


@router.delete(
	"/{pipeline_id}",
)
def delete_pipeline(
	pipeline_id: int,
	service: PipelineService = Depends(
		get_pipeline_service,
	),
):
	try:
		pipeline = service.get_pipeline(
			pipeline_id,
		)

		service.delete_pipeline(
			pipeline,
		)

		return {
			"message": "Pipeline deleted successfully."
		}
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=str(exc),
		)