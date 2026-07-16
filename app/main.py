from contextlib import asynccontextmanager

import app.models  # noqa: F401 — register SQLAlchemy mappers before any DB use

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.filtering import router as filtering_router
from app.api.pipeline import router as pipeline_router
from app.api.transform import router as transformation_router
from app.config import Settings, get_settings
from app.core.logger import configure_logger
from app.dependencies import get_app_settings, get_db
from app.database.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
	settings = get_settings()
	configure_logger(settings)
	with engine.connect() as connection:
		connection.execute(text("SELECT 1"))
	yield
	engine.dispose()


settings = get_settings()
app = FastAPI(
	title=settings.app_name,
	version=settings.app_version,
	debug=settings.debug,
	lifespan=lifespan,
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.cors_origins,
	allow_credentials=settings.cors_allow_credentials,
	allow_methods=settings.cors_allow_methods,
	allow_headers=settings.cors_allow_headers,
)

app.include_router(
    auth_router,
    prefix=settings.api_v1_prefix,
)
app.include_router(filtering_router, prefix=settings.api_v1_prefix)
app.include_router(pipeline_router, prefix=settings.api_v1_prefix)
app.include_router(transformation_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
def health_check(
	db: Session = Depends(get_db),
	app_settings: Settings = Depends(get_app_settings),
) -> dict:
	db.execute(text("SELECT 1"))
	return {
		"status": "ok",
		"service": app_settings.app_name,
		"environment": app_settings.environment,
	}
