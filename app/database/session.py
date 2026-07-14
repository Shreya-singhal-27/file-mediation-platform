from sqlalchemy.orm import Session, sessionmaker

from app.database.database import engine


SessionLocal = sessionmaker(
	autocommit=False,
	autoflush=False,
	bind=engine,
	class_=Session,
)
