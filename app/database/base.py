from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so SQLAlchemy registers them
from app.models.role import Role
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.source import Source
from app.models.destination import Destination
from app.models.pipeline import Pipeline
from app.models.filter_rule import FilterRule
from app.models.mapping_rule import MappingRule
from app.models.job import Job