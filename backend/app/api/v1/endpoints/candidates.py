"""Candidate Profile, Academic History, Resumes, and Document Management Endpoints."""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.candidate import (
    CandidateProfileResponse,
    CandidateProfileUpdateRequest,
    ProfileCompletenessResponse,
    EducationCreateRequest,
    EducationUpdateRequest,
    EducationResponse,
    SemesterCreateUpdateRequest,
    SemesterResponse,
    CandidateResumeResponse,
    CandidateDocumentResponse,
    SkillCreateRequest,
    SkillResponse,
    ProjectCreateRequest,
    ProjectResponse,
    CertificationCreateRequest,
    CertificationResponse,
    WorkExperienceCreateRequest,
    WorkExperienceResponse,
)
from app.schemas.application import ApplicationListResponse
from app.services.application_service import list_candidate_applications
from app.services.candidate_service import (
    get_candidate_profile_by_user_id,
    get_candidate_profile_by_id,
    update_candidate_profile,
    calculate_profile_completeness,
    upload_profile_photo,
    delete_profile_photo,
    get_profile_photo_file,
    add_education,
    update_education,
    delete_education,
    upload_education_document,
    get_education_document_file,
    add_or_update_semester,
    delete_semester,
    upload_semester_gradesheet,
    get_semester_gradesheet_file,
    upload_resume,
    set_default_resume,
    delete_resume,
    get_resume_version_file,
    upload_candidate_document,
    list_candidate_documents,
    delete_candidate_document,
    get_candidate_document_file,
    add_skill,
    delete_skill,
    add_project,
    delete_project,
    add_certification,
    delete_certification,
    add_work_experience,
    delete_work_experience,
    CandidateNotFoundError,
)
from app.services.storage_service import StorageError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["Candidates"])


# -----------------------------------------------------------------------------
# Profile & Completeness
# -----------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Get Current Candidate Profile",
    description="Returns the profile and contact details of the currently authenticated Candidate. Requires CANDIDATE role.",
)
def get_my_candidate_profile(
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Retrieve authenticated candidate's profile."""
    profile = get_candidate_profile_by_user_id(db, user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile record not found.",
        )
    return profile


@router.put(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Update Current Candidate Profile",
    description="Update personal details, headline, location, links, preferences, and visibility.",
)
def update_my_candidate_profile(
    request: CandidateProfileUpdateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Update profile endpoint."""
    try:
        return update_candidate_profile(db, user.id, request)
    except CandidateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/me/completeness",
    response_model=ProfileCompletenessResponse,
    summary="Get Profile Completeness Checklist",
    description="Returns dynamic completeness score and checklist of missing sections.",
)
def get_my_profile_completeness(
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Retrieve completeness checklist."""
    profile = get_candidate_profile_by_user_id(db, user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate profile not found.")
    return calculate_profile_completeness(db, profile.id)


@router.post(
    "/me/photo",
    summary="Upload Profile Photo",
    description="Upload a photo image (JPEG, PNG, WebP) to the candidate vault.",
)
async def upload_photo(
    file: UploadFile = File(...),
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Upload photo endpoint."""
    file_bytes = await file.read()
    try:
        photo_url = upload_profile_photo(
            db=db,
            user_id=user.id,
            file_bytes=file_bytes,
            filename=file.filename or "profile.jpg",
            content_type=file.content_type or "image/jpeg",
        )
        return {"photo_url": photo_url}
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/me/photo",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Profile Photo",
)
def remove_photo(
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Remove photo endpoint."""
    delete_profile_photo(db, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{candidate_id}/photo",
    summary="Download Profile Photo",
    description="Retrieve public/authorized candidate profile photo binary.",
)
def get_photo(
    candidate_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve profile photo stream."""
    try:
        file_bytes, filename, mime_type = get_profile_photo_file(db, candidate_id)
        return Response(content=file_bytes, media_type=mime_type, headers={"Cache-Control": "public, max-age=86400"})
    except CandidateNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found.")


@router.get(
    "/{candidate_id}",
    response_model=CandidateProfileResponse,
    summary="View Candidate Profile (Authorized View)",
    description="View candidate details respecting visibility and tenant boundaries.",
)
def get_candidate_profile_by_id_endpoint(
    candidate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get candidate profile by ID."""
    profile = get_candidate_profile_by_id(db, candidate_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    return profile


# -----------------------------------------------------------------------------
# Academic Education
# -----------------------------------------------------------------------------

@router.post(
    "/me/education",
    response_model=EducationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Academic Qualification",
)
def add_my_education(
    request: EducationCreateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Add education record."""
    try:
        return add_education(db, user.id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put(
    "/me/education/{education_id}",
    response_model=EducationResponse,
    summary="Update Academic Qualification",
)
def update_my_education(
    education_id: int,
    request: EducationUpdateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Update education record."""
    try:
        return update_education(db, user.id, education_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/me/education/{education_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Academic Qualification",
)
def delete_my_education(
    education_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete education record."""
    try:
        delete_education(db, user.id, education_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/me/education/{education_id}/document",
    response_model=EducationResponse,
    summary="Upload Academic Document / Marksheet",
)
async def upload_education_doc(
    education_id: int,
    file: UploadFile = File(...),
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Upload education marksheet file."""
    file_bytes = await file.read()
    try:
        return upload_education_document(
            db=db,
            user_id=user.id,
            education_id=education_id,
            file_bytes=file_bytes,
            filename=file.filename or "marksheet.pdf",
            content_type=file.content_type or "application/pdf",
        )
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/me/education/{education_id}/document",
    summary="Download Academic Document",
)
def download_education_doc(
    education_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Download marksheet."""
    try:
        file_bytes, filename, mime_type = get_education_document_file(db, education_id, user.id)
        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Semester Grade Sheets
# -----------------------------------------------------------------------------

@router.post(
    "/me/education/{education_id}/semesters",
    response_model=SemesterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add or Update Semester Record",
)
def add_or_update_my_semester(
    education_id: int,
    request: SemesterCreateUpdateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Add or update semester."""
    try:
        return add_or_update_semester(db, user.id, education_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/me/education/{education_id}/semesters/{semester_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Semester Record",
)
def delete_my_semester(
    education_id: int,
    semester_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete semester."""
    try:
        delete_semester(db, user.id, education_id, semester_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/me/education/{education_id}/semesters/{semester_number}/gradesheet",
    response_model=SemesterResponse,
    summary="Upload Semester Grade Sheet",
)
async def upload_semester_sheet(
    education_id: int,
    semester_number: int,
    file: UploadFile = File(...),
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Upload semester gradesheet."""
    file_bytes = await file.read()
    try:
        return upload_semester_gradesheet(
            db=db,
            user_id=user.id,
            education_id=education_id,
            semester_number=semester_number,
            file_bytes=file_bytes,
            filename=file.filename or f"sem_{semester_number}_gradesheet.pdf",
            content_type=file.content_type or "application/pdf",
        )
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/me/education/{education_id}/semesters/{semester_number}/gradesheet",
    summary="Download Semester Grade Sheet",
)
def download_semester_sheet(
    education_id: int,
    semester_number: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Download semester gradesheet."""
    try:
        file_bytes, filename, mime_type = get_semester_gradesheet_file(db, education_id, semester_number, user.id)
        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Resumes
# -----------------------------------------------------------------------------

@router.post(
    "/me/resumes",
    response_model=CandidateResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Resume File",
)
async def upload_my_resume(
    file: UploadFile = File(...),
    title: str = Form(default="Primary Resume"),
    target_role: Optional[str] = Form(default=None),
    is_default: bool = Form(default=False),
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Upload resume endpoint."""
    file_bytes = await file.read()
    try:
        return upload_resume(
            db=db,
            user_id=user.id,
            resume_title=title,
            target_role=target_role,
            is_default=is_default,
            file_bytes=file_bytes,
            filename=file.filename or "resume.pdf",
            content_type=file.content_type or "application/pdf",
        )
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/me/resumes/{resume_id}/default",
    response_model=CandidateResumeResponse,
    summary="Set Resume as Default",
)
def set_default_my_resume(
    resume_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Set default resume."""
    try:
        return set_default_resume(db, user.id, resume_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete(
    "/me/resumes/{resume_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Resume",
)
def delete_my_resume(
    resume_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete resume."""
    try:
        delete_resume(db, user.id, resume_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/me/resumes/{version_id}/download",
    summary="Download Resume Version",
)
def download_resume_version(
    version_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Download resume version."""
    try:
        file_bytes, filename, mime_type = get_resume_version_file(db, version_id, user.id)
        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Document Vault
# -----------------------------------------------------------------------------

@router.get(
    "/me/documents",
    response_model=List[CandidateDocumentResponse],
    summary="List Candidate Documents",
)
def list_my_documents(
    category: Optional[str] = Query(default=None),
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """List private documents."""
    return list_candidate_documents(db, user.id, category)


@router.post(
    "/me/documents",
    response_model=CandidateDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Supporting Document",
)
async def upload_my_document(
    file: UploadFile = File(...),
    category: str = Form(default="OTHER"),
    title: str = Form(default="Document"),
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Upload document endpoint."""
    file_bytes = await file.read()
    try:
        return upload_candidate_document(
            db=db,
            user_id=user.id,
            category=category,
            title=title,
            file_bytes=file_bytes,
            filename=file.filename or "document.pdf",
            content_type=file.content_type or "application/pdf",
        )
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/me/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Document",
)
def delete_my_document(
    document_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete document endpoint."""
    try:
        delete_candidate_document(db, user.id, document_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/me/documents/{document_id}/download",
    summary="Download Document",
)
def download_my_document(
    document_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Download document endpoint."""
    try:
        file_bytes, filename, mime_type = get_candidate_document_file(db, document_id, user.id)
        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Skills CRUD
# -----------------------------------------------------------------------------

@router.post(
    "/me/skills",
    response_model=SkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Skill",
)
def add_my_skill(
    request: SkillCreateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Add skill endpoint."""
    try:
        return add_skill(db, user.id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete(
    "/me/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Skill",
)
def delete_my_skill(
    skill_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete skill endpoint."""
    try:
        delete_skill(db, user.id, skill_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Projects CRUD
# -----------------------------------------------------------------------------

@router.post(
    "/me/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Project",
)
def add_my_project(
    request: ProjectCreateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Add project endpoint."""
    return add_project(db, user.id, request)


@router.delete(
    "/me/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
)
def delete_my_project(
    project_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete project endpoint."""
    try:
        delete_project(db, user.id, project_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Certifications CRUD
# -----------------------------------------------------------------------------

@router.post(
    "/me/certifications",
    response_model=CertificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Certification",
)
def add_my_certification(
    request: CertificationCreateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Add certification endpoint."""
    return add_certification(db, user.id, request)


@router.delete(
    "/me/certifications/{cert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Certification",
)
def delete_my_certification(
    cert_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete certification endpoint."""
    try:
        delete_certification(db, user.id, cert_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# Work Experience CRUD
# -----------------------------------------------------------------------------

@router.post(
    "/me/work-experience",
    response_model=WorkExperienceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Work Experience",
)
def add_my_work_experience(
    request: WorkExperienceCreateRequest,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Add work experience endpoint."""
    return add_work_experience(db, user.id, request)


@router.delete(
    "/me/work-experience/{experience_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Work Experience",
)
def delete_my_work_experience(
    experience_id: int,
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Delete work experience endpoint."""
    try:
        delete_work_experience(db, user.id, experience_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/me/applications",
    response_model=ApplicationListResponse,
    summary="List My Applications",
    description="Returns all job applications submitted by the current candidate.",
)
def get_my_candidate_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """List current candidate's submitted applications."""
    return list_candidate_applications(db, user, page=page, page_size=page_size)

