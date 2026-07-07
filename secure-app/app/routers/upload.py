from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.audit import record_security_event
from app.core.database import get_db
from app.models.upload import UploadFileRecord
from app.models.user import User

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".txt": "text/plain",
}


@router.get("/upload")
def upload_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    uploads = db.execute(
        select(
            UploadFileRecord.id,
            UploadFileRecord.original_filename,
            UploadFileRecord.file_size,
            UploadFileRecord.created_at,
            User.nickname.label("uploader"),
        )
        .join(User, UploadFileRecord.user_id == User.id)
        .order_by(UploadFileRecord.id.desc())
    ).all()
    return templates.TemplateResponse(
        request,
        "upload.html",
        {"user": user, "uploads": uploads},
    )


@router.post("/upload")
def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    original_filename = Path(file.filename or "unnamed").name
    suffix = Path(original_filename).suffix.lower()
    expected_type = ALLOWED_TYPES.get(suffix)
    if expected_type is None or file.content_type != expected_type:
        record_security_event(
            db,
            request,
            "upload_rejected",
            f"Rejected upload filename={original_filename} type={file.content_type}",
            user.id,
        )
        raise HTTPException(status_code=400, detail="허용되지 않는 파일 형식입니다.")

    content = file.file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        record_security_event(
            db, request, "upload_rejected", "Rejected oversized upload", user.id
        )
        raise HTTPException(status_code=413, detail="파일은 5MB 이하여야 합니다.")

    stored_filename = f"{uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / stored_filename
    destination.write_bytes(content)

    record = UploadFileRecord(
        user_id=user.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(destination),
        content_type=expected_type,
        file_size=len(content),
    )
    db.add(record)
    db.commit()
    return RedirectResponse(url="/upload", status_code=303)


@router.get("/download/{upload_id}")
def download_file(request: Request, upload_id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    record = db.get(UploadFileRecord, upload_id)
    if record is None or not Path(record.file_path).is_file():
        return RedirectResponse(url="/upload", status_code=303)

    return FileResponse(
        path=record.file_path,
        filename=record.original_filename,
        media_type="application/octet-stream",
    )
