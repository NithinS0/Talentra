"""Candidate Profile, Contact, Academic History, Resumes, and Documents Models."""

from typing import Optional, List
from decimal import Decimal
from datetime import date
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Text,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CandidateProfile(Base):
    """Candidate profile containing personal details and public CA-series actor ID."""

    __tablename__ = "candidate_profile"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), unique=True, nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String(7), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=False)
    headline: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    profile_visibility_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    completion_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    
    # Extended personal & professional information
    profile_photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    profile_photo_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_country_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("country.id"), nullable=True)
    preferred_roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_locations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_employment_types: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_graduation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    availability_status: Mapped[str] = mapped_column(String(50), default="AVAILABLE", nullable=False)
    is_public_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    consent_placement_rules: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    consent_share_with_employers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="candidate_profile")  # noqa: F821
    contact: Mapped[Optional["CandidateContact"]] = relationship(
        "CandidateContact", back_populates="candidate_profile", uselist=False, cascade="all, delete-orphan"
    )
    education_records: Mapped[List["CandidateEducation"]] = relationship(
        "CandidateEducation", back_populates="candidate_profile", cascade="all, delete-orphan", order_by="CandidateEducation.start_year.desc()"
    )
    resumes: Mapped[List["CandidateResume"]] = relationship(
        "CandidateResume", back_populates="candidate_profile", cascade="all, delete-orphan", order_by="CandidateResume.id.desc()"
    )
    documents: Mapped[List["CandidateDocument"]] = relationship(
        "CandidateDocument", back_populates="candidate_profile", cascade="all, delete-orphan", order_by="CandidateDocument.id.desc()"
    )
    skills: Mapped[List["CandidateSkill"]] = relationship(
        "CandidateSkill", back_populates="candidate_profile", cascade="all, delete-orphan"
    )
    projects: Mapped[List["CandidateProject"]] = relationship(
        "CandidateProject", back_populates="candidate_profile", cascade="all, delete-orphan"
    )
    work_experiences: Mapped[List["CandidateWorkExperience"]] = relationship(
        "CandidateWorkExperience", back_populates="candidate_profile", cascade="all, delete-orphan"
    )
    certifications: Mapped[List["CandidateCertification"]] = relationship(
        "CandidateCertification", back_populates="candidate_profile", cascade="all, delete-orphan"
    )


class CandidateContact(Base):
    """Candidate contact information with foreign key reference to country."""

    __tablename__ = "candidate_contact"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id"), unique=True, nullable=False, index=True
    )
    email_address: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    phone_e164: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    phone_country_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("country.id"), nullable=True)
    city_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    address_line_1: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="contact")
    country: Mapped[Optional["Country"]] = relationship("Country")  # noqa: F821


class CandidateEducation(Base):
    """Candidate education record supporting Class 10, Class 12, Diploma, UG, and PG."""

    __tablename__ = "candidate_education"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id"), nullable=False, index=True
    )
    qualification_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    education_level: Mapped[str] = mapped_column(String(50), default="UNDERGRADUATE", nullable=False)  # CLASS_10, CLASS_12, DIPLOMA, UNDERGRADUATE, POSTGRADUATE
    institution_name: Mapped[str] = mapped_column(String(250), nullable=False)
    board_or_university: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    field_of_study: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    stream_specialization: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="COMPLETED", nullable=False)  # PURSUING, COMPLETED, INCOMPLETE
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    start_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grading_system: Mapped[str] = mapped_column(String(30), default="PERCENTAGE", nullable=False)  # PERCENTAGE, CGPA_10, CGPA_4, MARKS
    grade_value: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    score_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    max_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    has_backlogs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_backlogs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    historical_backlogs_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    document_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    document_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="education_records")
    semesters: Mapped[List["CandidateEducationSemester"]] = relationship(
        "CandidateEducationSemester", back_populates="education", cascade="all, delete-orphan", order_by="CandidateEducationSemester.semester_number.asc()"
    )


class CandidateEducationSemester(Base):
    """Semester-wise grade and marksheet record linked to a college/diploma education."""

    __tablename__ = "candidate_education_semester"
    __table_args__ = (
        UniqueConstraint("candidate_education_id", "semester_number", name="uq_candidate_education_semester_num"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_education_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_education.id", ondelete="CASCADE"), nullable=False, index=True
    )
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    semester_number: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_term: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    result_status: Mapped[str] = mapped_column(String(30), default="PASS", nullable=False)  # PASS, FAIL, AWAITED, ARREAR, SUPPLEMENTARY
    sgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    credits_registered: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    credits_earned: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_backlog: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    backlog_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    grade_sheet_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    grade_sheet_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    grade_sheet_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    grade_sheet_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    education: Mapped["CandidateEducation"] = relationship("CandidateEducation", back_populates="semesters")
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile")


class CandidateDocument(Base):
    """Metadata repository for uploaded candidate documents (marksheets, certificates, photos)."""

    __tablename__ = "candidate_document"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    linked_entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linked_entity_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="documents")


class CandidateResume(Base):
    """Candidate resume container."""

    __tablename__ = "candidate_resume"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_title: Mapped[str] = mapped_column(String(180), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="resumes")
    versions: Mapped[List["ResumeVersion"]] = relationship(
        "ResumeVersion", back_populates="candidate_resume", cascade="all, delete-orphan", order_by="ResumeVersion.version_number.desc()"
    )


class ResumeVersion(Base):
    """Specific version and storage object reference of a candidate resume."""

    __tablename__ = "resume_version"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_resume_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_resume.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    language_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf", nullable=False)
    target_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_resume: Mapped["CandidateResume"] = relationship("CandidateResume", back_populates="versions")


class CandidateCertification(Base):
    """Professional certifications and verified credentials."""

    __tablename__ = "candidate_certification"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuing_organisation: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    credential_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credential_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    document_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="certifications")


class CandidateSkill(Base):
    """Candidate technical and professional skill."""

    __tablename__ = "candidate_skill"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    skill_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    proficiency_level: Mapped[str] = mapped_column(String(50), default="INTERMEDIATE", nullable=False)
    years_experience: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="skills")


class CandidateProject(Base):
    """Academic, personal, or open-source project created by candidate."""

    __tablename__ = "candidate_project"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_name: Mapped[str] = mapped_column(String(180), nullable=False)
    role_description: Mapped[str] = mapped_column(String(240), nullable=False)
    technologies: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    project_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    outcome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="projects")


class CandidateWorkExperience(Base):
    """Internship and work experience history."""

    __tablename__ = "candidate_work_experience"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("candidate_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employer_name: Mapped[str] = mapped_column(String(180), nullable=False)
    job_title: Mapped[str] = mapped_column(String(180), nullable=False)
    job_role_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="work_experiences")
