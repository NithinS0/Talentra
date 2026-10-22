"""Job Requirement, Position, and Reference Models."""

from typing import Optional, List
from decimal import Decimal
from sqlalchemy import BigInteger, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Industry(Base):
    """Industry reference taxonomy."""

    __tablename__ = "industry"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    industry_code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    parent_industry_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class JobRole(Base):
    """Job role reference taxonomy (Software Engineer, Product Manager, etc.)."""

    __tablename__ = "job_role"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    job_role_code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    industry_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class EmploymentType(Base):
    """Employment type taxonomy (Full-time, Part-time, Contract, Internship)."""

    __tablename__ = "employment_type"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkType(Base):
    """Work type taxonomy (On-site, Remote, Hybrid)."""

    __tablename__ = "work_type"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class JobRequirement(Base):
    """Job requisition / job posting entity."""

    __tablename__ = "job_requirement"
    __table_args__ = (
        CheckConstraint("positions_count > 0", name="ck_job_requirement_positions_count_positive"),
        CheckConstraint("salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min", name="ck_job_requirement_salary_range"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    job_role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_role.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    employment_type_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("employment_type.id"), nullable=False, index=True)
    work_type_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("work_type.id"), nullable=False, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False, index=True)  # 1=DRAFT, 2=OPEN, 3=CLOSED, 4=CANCELLED
    publish_state_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False, index=True)  # 1=UNPUBLISHED, 2=PUBLISHED, 3=ARCHIVED
    open_to_consultants: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    positions_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    salary_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    salary_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    salary_currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    application_deadline: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Structured requirements and eligibility criteria
    responsibilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_skills: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_qualifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted_branches: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    min_cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    allow_backlogs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_active_backlogs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_experience_years: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1), nullable=True)
    max_experience_years: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1), nullable=True)
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    required_documents: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="job_requirements")  # noqa: F821
    job_role: Mapped["JobRole"] = relationship("JobRole")
    employment_type: Mapped["EmploymentType"] = relationship("EmploymentType")
    work_type: Mapped["WorkType"] = relationship("WorkType")
    positions: Mapped[List["JobPosition"]] = relationship("JobPosition", back_populates="job_requirement", cascade="all, delete-orphan")
    applications: Mapped[List["JobApplication"]] = relationship("JobApplication", back_populates="job_requirement")  # noqa: F821


class JobPosition(Base):
    """Specific position / headcount allocation under a job requirement."""

    __tablename__ = "job_position"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    job_requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_requirement.id"), nullable=False, index=True)
    position_code: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    headcount: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    filled_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    job_requirement: Mapped["JobRequirement"] = relationship("JobRequirement", back_populates="positions")
