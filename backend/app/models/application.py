"""Job Application, Status History, and Candidate Blocking Models."""

from typing import Optional, List
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class JobApplication(Base):
    """Candidate application submitted to a job requirement."""

    __tablename__ = "job_application"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    job_requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_requirement.id"), nullable=False, index=True)
    candidate_profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("candidate_profile.id"), nullable=False, index=True)
    applied_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False, index=True)  # 1=APPLIED, 2=SCREENING, 3=INTERVIEW, 4=OFFERED, 5=HIRED, 6=REJECTED, 7=WITHDRAWN
    resume_version_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("resume_version.id"), nullable=True)
    resume_snapshot_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    resume_snapshot_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    eligibility_status: Mapped[str] = mapped_column(String(30), default="ELIGIBLE", nullable=False)
    eligibility_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_letter: Mapped[Optional[str]] = mapped_column(String(8000), nullable=True)
    last_status_changed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    job_requirement: Mapped["JobRequirement"] = relationship("JobRequirement", back_populates="applications")  # noqa: F821
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile")  # noqa: F821
    resume_version: Mapped[Optional["ResumeVersion"]] = relationship("ResumeVersion")  # noqa: F821
    status_history: Mapped[List["ApplicationStatusHistory"]] = relationship(
        "ApplicationStatusHistory", back_populates="job_application", cascade="all, delete-orphan"
    )


class ApplicationStatusHistory(Base):
    """Immutable audit trail of job application status changes."""

    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    job_application_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_application.id"), nullable=False, index=True)
    from_status_code_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    to_status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    changed_by_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False)
    changed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    job_application: Mapped["JobApplication"] = relationship("JobApplication", back_populates="status_history")


class BlockListEntry(Base):
    """Candidate and employer blocklist entity."""

    __tablename__ = "block_list_entry"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    blocker_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    blocked_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True, index=True)
    blocked_organisation_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=True, index=True)
    revoked_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
