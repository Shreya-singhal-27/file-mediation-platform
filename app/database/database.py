from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_settings


def create_db_engine() -> Engine:
	settings = get_settings()
	return create_engine(
		settings.database_url,
		pool_pre_ping=True,
		future=True,
	)


engine: Engine = create_db_engine()
