from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id"),
        nullable=False,
    )

    destination_id: Mapped[int] = mapped_column(
        ForeignKey("destinations.id"),
        nullable=False,
    )

    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Cron expression for APScheduler
    schedule: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ASN1, CSV, PIPE, FIXED_WIDTH
    decoder_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CSV",
    )

    # CSV, JSON, XML
    output_format: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="CSV",
    )

    archive_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    source: Mapped["Source"] = relationship(
        back_populates="pipelines",
    )

    destination: Mapped["Destination"] = relationship(
        back_populates="pipelines",
    )

    created_by: Mapped["User"] = relationship(
        back_populates="pipelines",
    )

    jobs: Mapped[List["Job"]] = relationship(
        back_populates="pipeline",
    )

    filter_rules: Mapped[List["FilterRule"]] = relationship(
        back_populates="pipeline",
    )

    mapping_rules: Mapped[List["MappingRule"]] = relationship(
        back_populates="pipeline",
    )

    def __repr__(self):
        return f"<Pipeline(name='{self.name}')>"