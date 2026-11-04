from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    email_verified_at: datetime | None


class SkillInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(default="Other", max_length=60)


class EducationInput(BaseModel):
    degree: str = Field(min_length=1, max_length=160)
    institution: str = Field(min_length=1, max_length=200)
    specialization: str | None = Field(default=None, max_length=160)
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    score: str | None = Field(default=None, max_length=40)


class ExperienceInput(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    position: str = Field(min_length=1, max_length=160)
    start_date: str | None = Field(default=None, max_length=20)
    end_date: str | None = Field(default=None, max_length=20)
    is_current: bool = False
    description: str | None = None


class ProjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None
    technologies: list[str] = Field(default_factory=list, max_length=40)
    url: str | None = Field(default=None, max_length=500)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, max_length=160)
    linkedin_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    portfolio_url: str | None = Field(default=None, max_length=500)
    summary: str | None = Field(default=None, max_length=3000)
    preferred_titles: list[str] = Field(default_factory=list, max_length=30)
    preferred_locations: list[str] = Field(default_factory=list, max_length=30)
    work_modes: list[str] = Field(default_factory=list, max_length=5)
    employment_types: list[str] = Field(default_factory=list, max_length=10)
    skills: list[SkillInput] = Field(default_factory=list, max_length=100)
    educations: list[EducationInput] = Field(default_factory=list, max_length=30)
    experiences: list[ExperienceInput] = Field(default_factory=list, max_length=50)
    projects: list[ProjectInput] = Field(default_factory=list, max_length=50)


class ProfileResponse(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    work_mode: str | None = Field(default=None, max_length=40)
    employment_type: str | None = Field(default=None, max_length=60)
    salary: str | None = Field(default=None, max_length=120)
    description: str = Field(default="", max_length=30000)
    url: str | None = Field(default=None, max_length=1000)
    source: str = Field(default="Manual", max_length=80)
    is_saved: bool = False


class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    match_score: float | None
    created_at: datetime


APPLICATION_STATUSES = [
    "Discovered", "Saved", "Viewed", "Application Started", "Resume Prepared", "Ready for Review",
    "Submitted", "Submission Confirmed", "Submission Unverified", "Under Review", "Assessment Invited",
    "Assessment Completed", "Interview Scheduled", "Interview Completed", "Rejected", "Offer Received",
    "Offer Accepted", "Offer Declined", "Withdrawn", "Closed",
]


class ApplicationCreate(BaseModel):
    job_id: int
    resume_version_id: int | None = None
    status: str = "Discovered"
    notes: str | None = Field(default=None, max_length=10000)


class ApplicationUpdate(BaseModel):
    status: str | None = None
    notes: str | None = Field(default=None, max_length=10000)
    resume_version_id: int | None = None


class ApplicationEventCreate(BaseModel):
    note: str = Field(min_length=1, max_length=5000)


class ApplicationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    previous_status: str | None
    new_status: str
    note: str | None
    source: str
    created_at: datetime


class ApplicationResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    matched_keywords: list[str]
    created_at: datetime


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    applied_at: datetime | None
    notes: str | None
    resume_version_id: int | None
    resume_version: ApplicationResumeResponse | None
    created_at: datetime
    job: JobResponse
    events: list[ApplicationEventResponse]


class DashboardResponse(BaseModel):
    jobs_added: int
    saved_jobs: int
    applications: int
    submitted: int
    interviews: int
    response_rate: float | None
    has_master_resume: bool
    profile_complete: bool
    upcoming_actions: list[dict]


class ResumeResponse(BaseModel):
    file_name: str
    file_type: str
    uploaded_at: datetime
    text_extracted: bool


class MatchResponse(BaseModel):
    match_score: int | None
    category: str
    matched_skills: list[str]
    missing_skills: list[str]
    mandatory_skill_gaps: list[str]
    recommendation: str
    components: dict[str, int]


class GeneratedResumeResponse(BaseModel):
    id: int
    version: int
    job_id: int
    job_title: str
    company: str
    matched_keywords: list[str]
    match_score_at_creation: float | None
    created_at: datetime
