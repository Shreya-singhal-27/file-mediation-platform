from sqlalchemy.orm import Session, configure_mappers, sessionmaker

import app.models  # noqa: F401 — register all SQLAlchemy mappers before sessions are used

from app.database.database import engine

configure_mappers()

SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine,
	class_=Session,
)
