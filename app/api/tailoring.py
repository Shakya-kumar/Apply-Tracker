import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.profile import load_profile
from app.auth import get_current_user
from app.core.config import settings
from app.db import get_db
from app.models import GeneratedResume, Job, User
from app.schemas import GeneratedResumeResponse, MatchResponse
from app.services.matching import analyze_match
from app.services.resume_factory import ordered_content, write_docx, write_pdf

router = APIRouter(tags=["matching and resume studio"])


def get_job(db: Session, job_id: int, user_id: int) -> Job:
    job = db.scalar(select(Job).where(Job.id == job_id, Job.user_id == user_id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/match", response_model=MatchResponse)
def match_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = get_job(db, job_id, user.id)
    profile = load_profile(db, user.id)
    result = analyze_match(job, profile)
    job.match_score = result["match_score"]
    db.commit()
    return result


def serialize_resume(version: GeneratedResume) -> GeneratedResumeResponse:
    return GeneratedResumeResponse(
        id=version.id,
        version=version.version,
        job_id=version.job_id,
        job_title=version.job.title,
        company=version.job.company,
        matched_keywords=version.matched_keywords,
        match_score_at_creation=version.match_score_at_creation,
        created_at=version.created_at,
    )


@router.get("/jobs/{job_id}/resume-versions", response_model=list[GeneratedResumeResponse])
def list_resume_versions(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    get_job(db, job_id, user.id)
    versions = db.scalars(select(GeneratedResume).where(GeneratedResume.job_id == job_id, GeneratedResume.user_id == user.id).order_by(GeneratedResume.version.desc())).all()
    return [serialize_resume(item) for item in versions]


@router.post("/jobs/{job_id}/resume-versions", response_model=GeneratedResumeResponse, status_code=status.HTTP_201_CREATED)
def generate_resume_version(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = get_job(db, job_id, user.id)
    profile = load_profile(db, user.id)
    if profile is None or not profile.full_name or not (profile.skills or profile.experiences or profile.educations or profile.projects):
        raise HTTPException(status_code=409, detail="Complete your name and at least one verified career detail before generating a tailored resume")

    match = analyze_match(job, profile)
    content = ordered_content(profile, job, user.email, match["matched_skills"])
    version_number = (db.scalar(select(func.max(GeneratedResume.version)).where(GeneratedResume.user_id == user.id, GeneratedResume.job_id == job.id)) or 0) + 1
    directory = Path(settings.upload_dir).resolve() / str(user.id) / "generated"
    directory.mkdir(parents=True, exist_ok=True)
    stem = uuid.uuid4().hex
    docx_path, pdf_path = directory / f"{stem}.docx", directory / f"{stem}.pdf"
    try:
        write_docx(content, docx_path)
        write_pdf(content, pdf_path)
        version = GeneratedResume(
            user_id=user.id,
            job_id=job.id,
            version=version_number,
            docx_path=str(docx_path),
            pdf_path=str(pdf_path),
            matched_keywords=match["matched_skills"],
            factual_snapshot=content,
            match_score_at_creation=match["match_score"],
        )
        db.add(version)
        db.commit()
        db.refresh(version)
    except Exception:
        db.rollback()
        docx_path.unlink(missing_ok=True)
        pdf_path.unlink(missing_ok=True)
        raise
    return serialize_resume(version)


@router.get("/resume-versions/{version_id}/download")
def download_resume_version(
    version_id: int,
    file_format: str = Query(alias="format", pattern="^(pdf|docx)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    version = db.scalar(select(GeneratedResume).where(GeneratedResume.id == version_id, GeneratedResume.user_id == user.id))
    if version is None:
        raise HTTPException(status_code=404, detail="Resume version not found")
    path = Path(version.pdf_path if file_format == "pdf" else version.docx_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Generated file not found")
    job = get_job(db, version.job_id, user.id)
    filename = f"ApplyTrack-{job.company}-{job.title}-v{version.version}.{file_format}".replace("/", "-").replace("\\", "-")
    media_type = "application/pdf" if file_format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path, filename=filename, media_type=media_type)
