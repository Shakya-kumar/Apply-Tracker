import re

from app.models import CareerProfile, Job

SKILL_CATALOG = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "SQL", "HTML", "CSS",
    "React", "Next.js", "Node.js", "FastAPI", "Django", "Flask", "Spring", "PostgreSQL", "MySQL",
    "MongoDB", "Redis", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux", "Excel",
    "Power BI", "Tableau", "Machine Learning", "Data Analysis", "TensorFlow", "PyTorch", "Figma",
]
TOKEN_RE = re.compile(r"[a-z0-9+#.]+", re.IGNORECASE)


def tokens(value: str) -> set[str]:
    return {token.casefold().strip(".") for token in TOKEN_RE.findall(value)}


def overlap(left: str, right: str) -> float:
    a, b = tokens(left), tokens(right)
    meaningful = {word for word in a if len(word) > 2}
    return len(meaningful & b) / len(meaningful) if meaningful else 0.0


def analyze_match(job: Job, profile: CareerProfile | None) -> dict:
    if profile is None or not (profile.skills or profile.experiences or profile.educations or profile.projects):
        return {"match_score": None, "category": "Add profile", "matched_skills": [], "missing_skills": [], "mandatory_skill_gaps": [], "recommendation": "Complete your career profile to calculate a job match.", "components": {}}

    content = f"{job.title}\n{job.description}".casefold()
    profile_skill_names = {skill.name.casefold() for skill in profile.skills}
    job_skills = [skill for skill in SKILL_CATALOG if skill.casefold() in content]
    matched = [skill for skill in job_skills if skill.casefold() in profile_skill_names]
    missing = [skill for skill in job_skills if skill.casefold() not in profile_skill_names]

    skill_score = len(matched) / len(job_skills) if job_skills else (1.0 if not profile_skill_names else 0.0)
    role_targets = profile.preferred_titles or [experience.position for experience in profile.experiences]
    role_score = max((overlap(target, job.title) for target in role_targets), default=0.0)
    exp_score = 1.0 if profile.experiences else 0.0
    edu_score = 1.0 if profile.educations else 0.0
    location_score = 1.0 if job.work_mode and job.work_mode.casefold() == "remote" and any("remote" in loc.casefold() for loc in profile.preferred_locations) else max((overlap(location, job.location or "") for location in profile.preferred_locations), default=0.0)
    project_hits = sum(1 for project in profile.projects if overlap(" ".join(project.technologies) + " " + (project.description or ""), job.description) > 0)
    project_score = min(1.0, project_hits / max(1, len(profile.projects))) if profile.projects else 0.0

    weights = {"skills": 30, "role": 20, "experience": 15, "education": 10, "location": 10, "salary": 10, "projects": 5}
    parts = {"skills": skill_score, "role": role_score, "experience": exp_score, "education": edu_score, "location": location_score, "salary": 0.5, "projects": project_score}
    score = round(sum(weights[key] * parts[key] for key in weights))
    category = "Excellent" if score >= 85 else "Good" if score >= 70 else "Possible" if score >= 50 else "Low"

    mandatory_lines = [line for line in job.description.splitlines() if re.search(r"\b(required|must[- ]have|mandatory)\b", line, re.IGNORECASE)]
    mandatory_content = " ".join(mandatory_lines).casefold()
    mandatory_gaps = [skill for skill in missing if skill.casefold() in mandatory_content]
    explanation = f"{len(matched)} of {len(job_skills)} recognized job skills overlap with your profile." if job_skills else "The job description contains no recognized skills from the current matching list."
    return {
        "match_score": score,
        "category": category,
        "matched_skills": matched,
        "missing_skills": missing,
        "mandatory_skill_gaps": mandatory_gaps,
        "recommendation": explanation,
        "components": {key: round(parts[key] * 100) for key in parts},
    }
