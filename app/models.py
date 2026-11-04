from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    memberships: Mapped[list["Membership"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_email", "email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_membership_tenant_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32), default="owner", nullable=False)
    tenant: Mapped[Tenant] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship(back_populates="memberships")


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (Index("ix_user_sessions_token_digest", "token_digest"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship(back_populates="sessions")


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(40))
    location: Mapped[str | None] = mapped_column(String(160))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    portfolio_url: Mapped[str | None] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    preferred_titles: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    preferred_locations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    work_modes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    employment_types: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    skills: Mapped[list["ProfileSkill"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    educations: Mapped[list["ProfileEducation"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    experiences: Mapped[list["ProfileExperience"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    projects: Mapped[list["ProfileProject"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class ProfileSkill(Base):
    __tablename__ = "profile_skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(60), default="Other", nullable=False)
    profile: Mapped[CareerProfile] = relationship(back_populates="skills")


class ProfileEducation(Base):
    __tablename__ = "profile_education"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True)
    degree: Mapped[str] = mapped_column(String(160), nullable=False)
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(160))
    graduation_year: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[str | None] = mapped_column(String(40))
    profile: Mapped[CareerProfile] = relationship(back_populates="educations")


class ProfileExperience(Base):
    __tablename__ = "profile_experiences"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(160), nullable=False)
    start_date: Mapped[str | None] = mapped_column(String(20))
    end_date: Mapped[str | None] = mapped_column(String(20))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    profile: Mapped[CareerProfile] = relationship(back_populates="experiences")


class ProfileProject(Base):
    __tablename__ = "profile_projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("career_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    technologies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    profile: Mapped[CareerProfile] = relationship(back_populates="projects")


class MasterResume(Base):
    __tablename__ = "master_resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("user_id", "url", name="uq_job_user_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    work_mode: Mapped[str | None] = mapped_column(String(40))
    employment_type: Mapped[str | None] = mapped_column(String(60))
    salary: Mapped[str | None] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    url: Mapped[str | None] = mapped_column(String(1000))
    source: Mapped[str] = mapped_column(String(80), default="Manual", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    match_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    resume_version_id: Mapped[int | None] = mapped_column(ForeignKey("resume_versions.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(40), default="Discovered", nullable=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    job: Mapped[Job] = relationship()
    resume_version: Mapped["GeneratedResume | None"] = relationship()
    events: Mapped[list["ApplicationEvent"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by=lambda: (ApplicationEvent.created_at, ApplicationEvent.id),
    )


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    previous_status: Mapped[str | None] = mapped_column(String(40))
    new_status: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(40), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    application: Mapped[Application] = relationship(back_populates="events")


class GeneratedResume(Base):
    __tablename__ = "resume_versions"
    __table_args__ = (UniqueConstraint("user_id", "job_id", "version", name="uq_resume_version_user_job_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    docx_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    matched_keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    factual_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    match_score_at_creation: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    job: Mapped[Job] = relationship()


class GoogleOAuthState(Base):
    __tablename__ = "google_oauth_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    service: Mapped[str] = mapped_column(String(30), nullable=False)
    state_digest: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    code_verifier: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConnectedAccount(Base):
    __tablename__ = "connected_accounts"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_connected_account_user_provider"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_email: Mapped[str] = mapped_column(String(320), nullable=False)
    access_token_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    access_token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="connected", nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailEvent(Base):
    __tablename__ = "email_events"
    __table_args__ = (UniqueConstraint("user_id", "provider_message_id", name="uq_email_event_user_message"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider_message_id: Mapped[str] = mapped_column(String(200), nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String(200))
    sender: Mapped[str | None] = mapped_column(String(500))
    subject: Mapped[str | None] = mapped_column(String(1000))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    classification: Mapped[str] = mapped_column(String(40), default="other", nullable=False)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (UniqueConstraint("user_id", "provider_event_id", name="uq_calendar_event_user_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider_event_id: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    organizer: Mapped[str | None] = mapped_column(String(320))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
