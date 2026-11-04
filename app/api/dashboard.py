from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Application, CalendarEvent, CareerProfile, Job, MasterResume, User
from app.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    jobs_added = db.scalar(select(func.count(Job.id)).where(Job.user_id == user.id)) or 0
    saved_jobs = db.scalar(select(func.count(Job.id)).where(Job.user_id == user.id, Job.is_saved.is_(True))) or 0
    app_count = db.scalar(select(func.count(Application.id)).where(Application.user_id == user.id)) or 0
    submitted_statuses = ["Submitted", "Submission Confirmed", "Submission Unverified", "Under Review", "Assessment Invited", "Assessment Completed", "Interview Scheduled", "Interview Completed", "Rejected", "Offer Received", "Offer Accepted", "Offer Declined"]
    submitted = db.scalar(select(func.count(Application.id)).where(Application.user_id == user.id, Application.status.in_(submitted_statuses))) or 0
    interview_statuses = ["Interview Scheduled", "Interview Completed"]
    interviews = db.scalar(select(func.count(Application.id)).where(Application.user_id == user.id, Application.status.in_(interview_statuses))) or 0
    response_statuses = ["Under Review", "Assessment Invited", "Assessment Completed", "Interview Scheduled", "Interview Completed", "Rejected", "Offer Received", "Offer Accepted", "Offer Declined"]
    responses = db.scalar(select(func.count(Application.id)).where(Application.user_id == user.id, Application.status.in_(response_statuses))) or 0
    profile = db.scalar(select(CareerProfile).where(CareerProfile.user_id == user.id))
    has_resume = db.scalar(select(MasterResume.id).where(MasterResume.user_id == user.id)) is not None
    complete = bool(profile and profile.full_name and (profile.skills or profile.experiences or profile.educations))
    upcoming = db.scalars(select(CalendarEvent).where(CalendarEvent.user_id == user.id, CalendarEvent.starts_at >= func.now()).order_by(CalendarEvent.starts_at).limit(5)).all()
    return DashboardResponse(
        jobs_added=jobs_added,
        saved_jobs=saved_jobs,
        applications=app_count,
        submitted=submitted,
        interviews=interviews,
        response_rate=round(responses / submitted * 100, 1) if submitted else None,
        has_master_resume=has_resume,
        profile_complete=complete,
        upcoming_actions=[{"title": event.summary, "starts_at": event.starts_at, "organizer": event.organizer} for event in upcoming],
    )
