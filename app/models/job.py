from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("pipelines.id"),
        nullable=False,
    )

    started_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # ACQUISITION, DECODING, FILTERING,
    # TRANSFORMATION, TRANSMISSION, COMPLETED, FAILED
    current_stage: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="ACQUISITION",
    )

    input_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    output_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    total_records: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    records_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    records_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    execution_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    file_checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    archive_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    job_log: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    pipeline: Mapped["Pipeline"] = relationship(
        back_populates="jobs",
    )

    started_by: Mapped["User"] = relationship(
        back_populates="jobs",
    )

    def __repr__(self):
        return f"<Job(id={self.id}, status='{self.status}')>"