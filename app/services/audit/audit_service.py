from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
	"""Persists audit entries for pipeline and platform events."""

	def __init__(self, audit_log_repository: AuditLogRepository):
		self.audit_log_repository = audit_log_repository

	def record_action(
		self,
		user_id: int,
		action: str,
		resource: str,
		details: str | None = None,
		ip_address: str | None = None,
	) -> AuditLog:
		"""Create a durable audit log entry."""
		audit_log = AuditLog(
			user_id=user_id,
			action=action,
			resource=resource,
			details=details,
			ip_address=ip_address,
		)
		return self.audit_log_repository.create(audit_log)

	def record_pipeline_event(
		self,
		user_id: int,
		pipeline_name: str,
		stage: str,
		details: str,
	) -> AuditLog:
		"""Persist a pipeline-specific audit entry."""
		return self.record_action(
			user_id=user_id,
			action=f"PIPELINE_{stage.upper()}",
			resource=pipeline_name,
			details=details,
		)
