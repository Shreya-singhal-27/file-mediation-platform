from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.filtering import router as filtering_router
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

app.include_router(filtering_router)


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
