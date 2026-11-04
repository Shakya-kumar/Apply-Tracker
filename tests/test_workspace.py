from io import BytesIO

from docx import Document
from pypdf import PdfReader


def create_account(client, email="workspace@example.com"):
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "correct-horse-battery-staple"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_profile_round_trip_and_account_isolation(client):
    headers = create_account(client)
    other_headers = create_account(client, "other@example.com")
    payload = {
        "full_name": "A. User", "location": "Bengaluru", "preferred_titles": ["Engineer"],
        "skills": [{"name": "Python", "category": "Programming"}],
        "educations": [{"degree": "BSc", "institution": "Example University", "graduation_year": 2024}],
        "experiences": [{"company": "Example Co", "position": "Intern", "is_current": False}],
        "projects": [{"name": "Portfolio", "technologies": ["Python"]}],
    }
    saved = client.put("/api/v1/profile", json=payload, headers=headers)
    assert saved.status_code == 200
    assert saved.json()["skills"][0]["name"] == "Python"
    assert client.get("/api/v1/profile", headers=other_headers).json()["full_name"] is None


def test_jobs_applications_timeline_and_dashboard_are_database_backed(client):
    headers = create_account(client)
    job = client.post("/api/v1/jobs", headers=headers, json={"title": "Analyst", "company": "Example Co", "url": "https://example.com/jobs/1", "description": "Analyze data"})
    assert job.status_code == 201
    saved = client.patch(f"/api/v1/jobs/{job.json()['id']}/saved?saved=true", headers=headers)
    assert saved.json()["is_saved"] is True
    app = client.post("/api/v1/applications", headers=headers, json={"job_id": job.json()["id"]})
    assert app.status_code == 201
    app_id = app.json()["id"]
    updated = client.patch(f"/api/v1/applications/{app_id}", headers=headers, json={"status": "Interview Scheduled"})
    assert updated.status_code == 200
    assert updated.json()["events"][-1]["previous_status"] == "Discovered"
    noted = client.post(f"/api/v1/applications/{app_id}/events", headers=headers, json={"note": "Call with the hiring manager"})
    assert noted.json()["events"][-1]["note"] == "Call with the hiring manager"
    metrics = client.get("/api/v1/dashboard", headers=headers).json()
    assert metrics["jobs_added"] == 1
    assert metrics["saved_jobs"] == 1
    assert metrics["applications"] == 1
    assert metrics["interviews"] == 1


def test_master_resume_docx_upload_and_private_download(client):
    headers = create_account(client)
    buffer = BytesIO()
    document = Document()
    document.add_paragraph("Verified Sample Candidate")
    document.add_paragraph("Resume text for extraction.")
    document.save(buffer)
    response = client.post("/api/v1/resume", headers=headers, files={"file": ("resume.docx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert response.status_code == 201
    assert response.json()["text_extracted"] is True
    text = client.get("/api/v1/resume/extracted-text", headers=headers).json()["text"]
    assert "Verified Sample Candidate" in text
    assert client.get("/api/v1/resume/download", headers=headers).status_code == 200
    other_headers = create_account(client, "private@example.com")
    assert client.get("/api/v1/resume", headers=other_headers).status_code == 404


def test_integration_status_is_explicit_about_unconfigured_providers(client):
    headers = create_account(client)
    items = client.get("/api/v1/integrations/status", headers=headers).json()["items"]
    gmail = next(item for item in items if item["id"] == "gmail")
    assert gmail["connected"] is False
    assert gmail["status"] == "setup_required"
    assert client.post("/api/v1/integrations/google/start?service=gmail", headers=headers).status_code == 503


def test_manual_jobs_without_urls_and_blank_profile_match(client):
    headers = create_account(client)
    first = client.post("/api/v1/jobs", headers=headers, json={"title": "Analyst", "company": "One", "description": "Analyze data"})
    second = client.post("/api/v1/jobs", headers=headers, json={"title": "Analyst", "company": "Two", "description": "Analyze data"})
    assert first.status_code == second.status_code == 201
    client.put("/api/v1/profile", headers=headers, json={})
    result = client.get(f"/api/v1/jobs/{first.json()['id']}/match", headers=headers)
    assert result.json()["match_score"] is None


def test_rule_match_resume_exports_and_application_resume_reference(client):
    headers = create_account(client)
    profile = {
        "full_name": "Verified Candidate", "skills": [{"name": "Python", "category": "Programming"}, {"name": "FastAPI", "category": "Framework"}],
        "preferred_titles": ["Backend engineer"], "experiences": [{"company": "Example Co", "position": "Backend intern", "description": "Built Python services", "is_current": False}],
    }
    assert client.put("/api/v1/profile", headers=headers, json=profile).status_code == 200
    job = client.post("/api/v1/jobs", headers=headers, json={"title": "Backend engineer", "company": "Example Labs", "description": "Required skills: Python, FastAPI, React"}).json()
    match = client.get(f"/api/v1/jobs/{job['id']}/match", headers=headers)
    assert match.status_code == 200
    assert "Python" in match.json()["matched_skills"]
    assert "React" in match.json()["missing_skills"]
    version = client.post(f"/api/v1/jobs/{job['id']}/resume-versions", headers=headers)
    assert version.status_code == 201
    version_id = version.json()["id"]
    pdf = client.get(f"/api/v1/resume-versions/{version_id}/download?format=pdf", headers=headers)
    assert pdf.status_code == 200
    assert PdfReader(BytesIO(pdf.content)).pages[0].extract_text().find("Verified Candidate") >= 0
    docx = client.get(f"/api/v1/resume-versions/{version_id}/download?format=docx", headers=headers)
    assert docx.status_code == 200
    app = client.post("/api/v1/applications", headers=headers, json={"job_id": job["id"], "resume_version_id": version_id})
    assert app.status_code == 201
    assert app.json()["resume_version"]["id"] == version_id
    assert app.json()["resume_version"]["version"] == 1
