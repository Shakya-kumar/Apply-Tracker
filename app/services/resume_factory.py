from html import escape
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate

from app.models import CareerProfile, Job
from app.services.matching import overlap


def ordered_content(profile: CareerProfile, job: Job, email: str, matched_skills: list[str]) -> dict:
    job_text = f"{job.title}\n{job.description}"
    skills = sorted(profile.skills, key=lambda item: (item.name.casefold() not in {name.casefold() for name in matched_skills}, item.name.casefold()))
    experiences = sorted(profile.experiences, key=lambda item: overlap(f"{item.position} {item.description or ''}", job_text), reverse=True)
    projects = sorted(profile.projects, key=lambda item: overlap(f"{item.name} {' '.join(item.technologies)} {item.description or ''}", job_text), reverse=True)
    contacts = [value for value in [profile.location, profile.phone, email, profile.linkedin_url, profile.github_url, profile.portfolio_url] if value]
    return {
        "name": profile.full_name or email,
        "contact": contacts,
        "summary": profile.summary,
        "skills": [item.name for item in skills],
        "experiences": [{"position": item.position, "company": item.company, "start_date": item.start_date, "end_date": "Present" if item.is_current else item.end_date, "description": item.description} for item in experiences],
        "educations": [{"degree": item.degree, "institution": item.institution, "specialization": item.specialization, "graduation_year": item.graduation_year, "score": item.score} for item in profile.educations],
        "projects": [{"name": item.name, "description": item.description, "technologies": item.technologies, "url": item.url} for item in projects],
        "tailored_for": {"title": job.title, "company": job.company},
    }


def _line_items(value: str | None) -> list[str]:
    if not value:
        return []
    return [line.strip(" •-\t") for line in value.splitlines() if line.strip(" •-\t")]


def write_docx(content: dict, path: Path) -> None:
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)
    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9.5)
    normal.paragraph_format.space_after = Pt(2)
    heading = document.add_paragraph()
    heading.alignment = 1
    run = heading.add_run(content["name"])
    run.bold = True
    run.font.name = "Arial"
    run.font.size = Pt(19)
    if content["contact"]:
        line = document.add_paragraph(" | ".join(content["contact"]))
        line.alignment = 1
    for name, values in [
        ("SUMMARY", [content["summary"]] if content["summary"] else []),
        ("SKILLS", [", ".join(content["skills"])] if content["skills"] else []),
    ]:
        if values:
            document.add_heading(name, level=1)
            for value in values:
                document.add_paragraph(value)
    if content["experiences"]:
        document.add_heading("EXPERIENCE", level=1)
        for item in content["experiences"]:
            label = document.add_paragraph()
            label.paragraph_format.space_before = Pt(4)
            run = label.add_run(f"{item['position']} — {item['company']}")
            run.bold = True
            dates = " – ".join(value for value in [item["start_date"], item["end_date"]] if value)
            if dates:
                label.add_run(f"  |  {dates}")
            for bullet in _line_items(item["description"]):
                document.add_paragraph(bullet, style="List Bullet")
    if content["educations"]:
        document.add_heading("EDUCATION", level=1)
        for item in content["educations"]:
            details = [item["degree"], item["specialization"], item["institution"], str(item["graduation_year"]) if item["graduation_year"] else None, item["score"]]
            document.add_paragraph(" | ".join(value for value in details if value))
    if content["projects"]:
        document.add_heading("PROJECTS", level=1)
        for item in content["projects"]:
            paragraph = document.add_paragraph()
            run = paragraph.add_run(item["name"])
            run.bold = True
            if item["technologies"]:
                paragraph.add_run(f" — {', '.join(item['technologies'])}")
            if item["url"]:
                paragraph.add_run(f" — {item['url']}")
            for bullet in _line_items(item["description"]):
                document.add_paragraph(bullet, style="List Bullet")
    for style_name in ("Heading 1", "Heading 2"):
        style = document.styles[style_name]
        style.font.name = "Arial"
        style.font.size = Pt(11)
        style.paragraph_format.space_before = Pt(8)
        style.paragraph_format.space_after = Pt(3)
    document.save(path)


def write_pdf(content: dict, path: Path) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ResumeName", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=21, alignment=TA_CENTER, textColor=colors.HexColor("#173f32"), spaceAfter=3))
    styles.add(ParagraphStyle(name="ResumeContact", parent=styles["Normal"], fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor("#45534a"), spaceAfter=8))
    styles.add(ParagraphStyle(name="ResumeSection", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10, leading=12, textColor=colors.HexColor("#173f32"), spaceBefore=7, spaceAfter=3, keepWithNext=True))
    styles.add(ParagraphStyle(name="ResumeBody", parent=styles["BodyText"], fontSize=9, leading=12, spaceAfter=2))
    styles.add(ParagraphStyle(name="ResumeSubhead", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9.3, leading=12, spaceBefore=4, spaceAfter=1, keepWithNext=True))
    story = [Paragraph(escape(content["name"]), styles["ResumeName"])]
    if content["contact"]:
        story.append(Paragraph(escape("  |  ".join(content["contact"])), styles["ResumeContact"]))
    if content["summary"]:
        story.extend([Paragraph("SUMMARY", styles["ResumeSection"]), Paragraph(escape(content["summary"]).replace("\n", "<br/>"), styles["ResumeBody"])])
    if content["skills"]:
        story.extend([Paragraph("SKILLS", styles["ResumeSection"]), Paragraph(escape(", ".join(content["skills"])), styles["ResumeBody"])])
    if content["experiences"]:
        story.append(Paragraph("EXPERIENCE", styles["ResumeSection"]))
        for item in content["experiences"]:
            title = f"{item['position']} — {item['company']}"
            dates = " – ".join(value for value in [item["start_date"], item["end_date"]] if value)
            story.append(Paragraph(escape(title + (f"  |  {dates}" if dates else "")), styles["ResumeSubhead"]))
            for bullet in _line_items(item["description"]):
                story.append(Paragraph(escape(bullet), styles["ResumeBody"], bulletText="•"))
    if content["educations"]:
        story.append(Paragraph("EDUCATION", styles["ResumeSection"]))
        for item in content["educations"]:
            values = [item["degree"], item["specialization"], item["institution"], str(item["graduation_year"]) if item["graduation_year"] else None, item["score"]]
            story.append(Paragraph(escape(" | ".join(value for value in values if value)), styles["ResumeBody"]))
    if content["projects"]:
        story.append(Paragraph("PROJECTS", styles["ResumeSection"]))
        for item in content["projects"]:
            story.append(Paragraph(escape(item["name"] + (f" — {', '.join(item['technologies'])}" if item["technologies"] else "")), styles["ResumeSubhead"]))
            if item["url"]:
                story.append(Paragraph(escape(item["url"]), styles["ResumeBody"]))
            for bullet in _line_items(item["description"]):
                story.append(Paragraph(escape(bullet), styles["ResumeBody"], bulletText="•"))
    document = SimpleDocTemplate(str(path), pagesize=LETTER, rightMargin=0.65*inch, leftMargin=0.65*inch, topMargin=0.5*inch, bottomMargin=0.5*inch, title=f"{content['name']} - Resume")
    document.build(story)
