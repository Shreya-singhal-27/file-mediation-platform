from fastapi import Depends
from sqlalchemy.orm import Session

from app.business.auth_service import AuthService
from app.business.pipeline_service import PipelineService
from app.database.session import SessionLocal
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.user_repository import UserRepository


def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def get_auth_service(
	db: Session = Depends(get_db),
) -> AuthService:
	return AuthService(
		UserRepository(db),
	)


def get_pipeline_service(
	db: Session = Depends(get_db),
) -> PipelineService:
	return PipelineService(
		PipelineRepository(db),
	)