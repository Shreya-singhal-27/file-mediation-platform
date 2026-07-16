from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.base_repository import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
	"""Repository for persisting audit log entries."""

	def __init__(self, db: Session):
		super().__init__(db, AuditLog)

	def get_by_user_id(self, user_id: int) -> list[AuditLog]:
		"""Return audit entries created by a user."""
		statement = select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc())
		return list(self.db.scalars(statement).all())
