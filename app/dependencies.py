from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.session import SessionLocal
from app.services.filtering.filter_manager import FilterManager

if TYPE_CHECKING:
	from app.business.auth_service import AuthService
	from app.business.pipeline_service import PipelineService
	from app.services.transformation.transformation_manager import TransformationManager


def get_app_settings() -> Settings:
	return get_settings()


def get_db() -> Generator[Session, None, None]:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def get_auth_service(
	db: Session = Depends(get_db),
) -> "AuthService":
	from app.business.auth_service import AuthService
	from app.repositories.user_repository import UserRepository

	return AuthService(
		UserRepository(db),
	)


def get_pipeline_service(
	db: Session = Depends(get_db),
) -> "PipelineService":
	from app.business.pipeline_service import PipelineService
	from app.repositories.pipeline_repository import PipelineRepository

	return PipelineService(
		PipelineRepository(db),
	)


def get_filter_manager() -> FilterManager:
	return FilterManager()


def get_transformation_manager() -> "TransformationManager":
	from app.services.transformation.transformation_manager import TransformationManager

	return TransformationManager()