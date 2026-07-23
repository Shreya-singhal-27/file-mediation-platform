from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_pipeline_manager
from app.services.pipeline.pipeline_manager import PipelineManager
from app.business.pipeline_service import PipelineService
from app.core.security import get_current_user
from app.dependencies import get_pipeline_service
from app.schemas.pipeline import (
	PipelineCreate,
	PipelineResponse,
	PipelineUpdate,
)
from app.business.job_service import JobService
from app.business.user_service import UserService
from app.services.audit.audit_service import AuditService
from app.services.pipeline.pipeline_manager import PipelineManager

from app.dependencies import (
	get_audit_service,
	get_job_service,
	get_pipeline_manager,
	get_user_service,
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

@router.post(
	"/{pipeline_id}/run",
)
def run_pipeline(
	pipeline_id: int,
	current_user=Depends(get_current_user),
	pipeline_service: PipelineService = Depends(get_pipeline_service),
	user_service: UserService = Depends(get_user_service),
	pipeline_manager: PipelineManager = Depends(get_pipeline_manager),
	job_service: JobService = Depends(get_job_service),
	audit_service: AuditService = Depends(get_audit_service),
):

	try:
		pipeline = pipeline_service.get_pipeline(
			pipeline_id,
		)

		user = user_service.get_user(
			current_user["user_id"],
		)

		report = pipeline_manager.run_pipeline(
			pipeline=pipeline,
			started_by=user,
			job_service=job_service,
			audit_service=audit_service,
		)

		return {
			"message": "Pipeline executed successfully.",
			"report": report,
		}

	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=str(exc),
		)
		