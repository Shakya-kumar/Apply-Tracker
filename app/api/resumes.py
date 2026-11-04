import hashlib
import io
import uuid
import zipfile
from pathlib import Path

from docx import Document
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.config import settings
from app.db import get_db
from app.models import MasterResume, User
from app.schemas import ResumeResponse

router = APIRouter(prefix="/resume", tags=["resumes"])
MAX_RESUME_BYTES = 8 * 1024 * 1024


def extract_text(file_bytes: bytes, file_type: str) -> str:
    try:
        if file_type == "pdf":
            reader = PdfReader(io.BytesIO(file_bytes), strict=True)
            if reader.is_encrypted:
                raise HTTPException(status_code=422, detail="Password-protected PDF files are not supported")
            text = "\n".join((page.extract_text() or "") for page in reader.pages[:60])
        else:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise HTTPException(status_code=422, detail="This file is not a valid DOCX document")
            document = Document(io.BytesIO(file_bytes))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            for table in document.tables:
                text += "\n" + "\n".join(" | ".join(cell.text for cell in row.cells) for row in table.rows)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="We couldn’t read this resume. Try another PDF or DOCX file") from None
    return text[:100_000]


def get_resume(db: Session, user_id: int) -> MasterResume | None:
    return db.scalar(select(MasterResume).where(MasterResume.user_id == user_id))


def resume_response(resume: MasterResume) -> ResumeResponse:
    return ResumeResponse(file_name=resume.file_name, file_type=resume.file_type, uploaded_at=resume.uploaded_at, text_extracted=bool(resume.extracted_text.strip()))


@router.get("", response_model=ResumeResponse)
def resume_info(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = get_resume(db, user.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="No master resume has been uploaded")
    return resume_response(resume)


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    filename = Path(file.filename or "resume").name
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(status_code=415, detail="Upload a PDF or DOCX resume")
    contents = await file.read(MAX_RESUME_BYTES + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="The selected file is empty")
    if len(contents) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="Resume files must be 8 MB or smaller")
    file_type = extension[1:]
    if file_type == "pdf" and not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The file content does not look like a PDF")
    if file_type == "docx" and not zipfile.is_zipfile(io.BytesIO(contents)):
        raise HTTPException(status_code=415, detail="The file content does not look like a DOCX document")

    text = extract_text(contents, file_type)
    directory = Path(settings.upload_dir).resolve() / str(user.id)
    directory.mkdir(parents=True, exist_ok=True)
    stored_path = directory / f"{uuid.uuid4().hex}.{file_type}"
    stored_path.write_bytes(contents)

    resume = get_resume(db, user.id)
    old_path = resume.storage_path if resume else None
    if resume is None:
        resume = MasterResume(user_id=user.id, file_name=filename, storage_path=str(stored_path), file_type=file_type, sha256=hashlib.sha256(contents).hexdigest(), extracted_text=text)
        db.add(resume)
    else:
        resume.file_name = filename
        resume.storage_path = str(stored_path)
        resume.file_type = file_type
        resume.sha256 = hashlib.sha256(contents).hexdigest()
        resume.extracted_text = text
    try:
        db.commit()
    except Exception:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise
    if old_path and old_path != str(stored_path):
        Path(old_path).unlink(missing_ok=True)
    db.refresh(resume)
    return resume_response(resume)


@router.get("/extracted-text")
def get_extracted_text(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = get_resume(db, user.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="No master resume has been uploaded")
    return {"text": resume.extracted_text}


@router.get("/download")
def download_resume(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = get_resume(db, user.id)
    if resume is None or not Path(resume.storage_path).is_file():
        raise HTTPException(status_code=404, detail="Master resume file not found")
    return FileResponse(resume.storage_path, filename=resume.file_name, media_type="application/pdf" if resume.file_type == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    resume = get_resume(db, user.id)
    if resume is None:
        return
    stored_path = resume.storage_path
    db.delete(resume)
    db.commit()
    Path(stored_path).unlink(missing_ok=True)
