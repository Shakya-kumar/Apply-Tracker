from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.db import get_db
from app.models import CareerProfile, ProfileEducation, ProfileExperience, ProfileProject, ProfileSkill, User
from app.schemas import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


def load_profile(db: Session, user_id: int) -> CareerProfile | None:
    return db.scalar(
        select(CareerProfile)
        .where(CareerProfile.user_id == user_id)
        .options(
            selectinload(CareerProfile.skills),
            selectinload(CareerProfile.educations),
            selectinload(CareerProfile.experiences),
            selectinload(CareerProfile.projects),
        )
    )


def as_profile(profile: CareerProfile | None) -> ProfileResponse:
    if profile is None:
        return ProfileResponse()
    data = {key: getattr(profile, key) for key in (
        "full_name", "phone", "location", "linkedin_url", "github_url", "portfolio_url", "summary",
        "preferred_titles", "preferred_locations", "work_modes", "employment_types",
    )}
    data["skills"] = [{"name": item.name, "category": item.category} for item in profile.skills]
    data["educations"] = [{"degree": item.degree, "institution": item.institution, "specialization": item.specialization, "graduation_year": item.graduation_year, "score": item.score} for item in profile.educations]
    data["experiences"] = [{"company": item.company, "position": item.position, "start_date": item.start_date, "end_date": item.end_date, "is_current": item.is_current, "description": item.description} for item in profile.experiences]
    data["projects"] = [{"name": item.name, "description": item.description, "technologies": item.technologies, "url": item.url} for item in profile.projects]
    return ProfileResponse.model_validate(data)


@router.get("", response_model=ProfileResponse)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return as_profile(load_profile(db, user.id))


@router.put("", response_model=ProfileResponse)
def save_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = load_profile(db, user.id)
    if profile is None:
        profile = CareerProfile(user_id=user.id)
        db.add(profile)
        db.flush()

    values = payload.model_dump()
    skills = values.pop("skills")
    educations = values.pop("educations")
    experiences = values.pop("experiences")
    projects = values.pop("projects")
    for key, value in values.items():
        setattr(profile, key, value)
    profile.skills = [ProfileSkill(**item) for item in skills]
    profile.educations = [ProfileEducation(**item) for item in educations]
    profile.experiences = [ProfileExperience(**item) for item in experiences]
    profile.projects = [ProfileProject(**item) for item in projects]
    db.commit()
    return as_profile(load_profile(db, user.id))
