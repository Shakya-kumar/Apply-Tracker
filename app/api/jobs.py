from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.db import get_db
from app.models import Application, ApplicationEvent, GeneratedResume, Job, User
from app.schemas import APPLICATION_STATUSES, ApplicationCreate, ApplicationEventCreate, ApplicationResponse, ApplicationUpdate, JobCreate, JobResponse

router = APIRouter(tags=["jobs and applications"])


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    q: str | None = Query(default=None, max_length=200),
    saved: bool | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Job).where(Job.user_id == user.id)
    if saved is not None:
        query = query.where(Job.is_saved.is_(saved))
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Job.title.ilike(pattern), Job.company.ilike(pattern), Job.location.ilike(pattern)))
    return list(db.scalars(query.order_by(Job.created_at.desc()).limit(200)).all())


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def add_job(payload: JobCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    values = payload.model_dump()
    values["url"] = values["url"] or None
    job = Job(user_id=user.id, **values)
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A job with this URL is already in your workspace") from None
    db.refresh(job)
    return job


@router.patch("/jobs/{job_id}/saved", response_model=JobResponse)
def set_job_saved(job_id: int, saved: bool, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.scalar(select(Job).where(Job.id == job_id, Job.user_id == user.id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_saved = saved
    db.commit()
    db.refresh(job)
    return job


def find_application(db: Session, application_id: int, user_id: int) -> Application | None:
    return db.scalar(
        select(Application).where(Application.id == application_id, Application.user_id == user_id)
        .options(selectinload(Application.job), selectinload(Application.events), selectinload(Application.resume_version))
        .execution_options(populate_existing=True)
    )


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(Application).where(Application.user_id == user.id).options(
        selectinload(Application.job), selectinload(Application.events), selectinload(Application.resume_version)
    ).order_by(Application.updated_at.desc()).limit(200)
    return list(db.scalars(query).all())


@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.status not in APPLICATION_STATUSES:
        raise HTTPException(status_code=422, detail="Unknown application status")
    job = db.scalar(select(Job).where(Job.id == payload.job_id, Job.user_id == user.id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    resume_version = None
    if payload.resume_version_id is not None:
        resume_version = db.scalar(select(GeneratedResume).where(GeneratedResume.id == payload.resume_version_id, GeneratedResume.user_id == user.id, GeneratedResume.job_id == job.id))
        if resume_version is None:
            raise HTTPException(status_code=404, detail="Resume version not found for this job")
    application = Application(user_id=user.id, job_id=job.id, resume_version_id=resume_version.id if resume_version else None, status=payload.status, notes=payload.notes)
    if payload.status in {"Submitted", "Submission Confirmed", "Submission Unverified"}:
        application.applied_at = datetime.now(timezone.utc)
    db.add(application)
    db.flush()
    db.add(ApplicationEvent(application_id=application.id, previous_status=None, new_status=payload.status, note="Application tracking started", source="user"))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This job is already in your application tracker") from None
    return find_application(db, application.id, user.id)


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
def update_application(application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    application = find_application(db, application_id, user.id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if payload.status is not None:
        if payload.status not in APPLICATION_STATUSES:
            raise HTTPException(status_code=422, detail="Unknown application status")
        if payload.status != application.status:
            previous = application.status
            application.status = payload.status
            db.add(ApplicationEvent(application_id=application.id, previous_status=previous, new_status=payload.status, note="Status updated by you", source="user"))
            if payload.status in {"Submitted", "Submission Confirmed", "Submission Unverified"} and application.applied_at is None:
                application.applied_at = datetime.now(timezone.utc)
    if "notes" in payload.model_fields_set:
        application.notes = payload.notes
    if payload.resume_version_id is not None:
        resume_version = db.scalar(select(GeneratedResume).where(GeneratedResume.id == payload.resume_version_id, GeneratedResume.user_id == user.id, GeneratedResume.job_id == application.job_id))
        if resume_version is None:
            raise HTTPException(status_code=404, detail="Resume version not found for this job")
        application.resume_version_id = resume_version.id
    db.commit()
    return find_application(db, application.id, user.id)


@router.post("/applications/{application_id}/events", response_model=ApplicationResponse)
def add_application_note(application_id: int, payload: ApplicationEventCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    application = find_application(db, application_id, user.id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    db.add(ApplicationEvent(application_id=application.id, previous_status=application.status, new_status=application.status, note=payload.note, source="user"))
    db.commit()
    return find_application(db, application.id, user.id)
