from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MappingRule(Base):
    __tablename__ = "mapping_rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("pipelines.id"),
        nullable=False,
    )

    source_field: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    target_field: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    transformation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    default_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    pipeline: Mapped["Pipeline"] = relationship(
        back_populates="mapping_rules",
    )

    def __repr__(self):
        return f"<MappingRule({self.source_field} -> {self.target_field})>"