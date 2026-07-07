import json
import hashlib
import hmac
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.core.database import get_db
from app.core.config import get_settings
from app.common.audit import record_security_event
from app.models.post import Post

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter()
settings = get_settings()
MAX_BACKUP_SIZE = 1024 * 1024


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sign_backup(data: dict) -> str:
    return hmac.new(
        settings.backup_signing_key.encode(), canonical_json(data), hashlib.sha256
    ).hexdigest()


@router.get("/posts/backup")
def backup_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "post_backup.html", {"user": user})


@router.get("/posts/export")
def export_posts(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    posts = db.scalars(select(Post).where(Post.user_id == user.id)).all()
    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "posts": [
            {
                "user_id": post.user_id,
                "title": post.title,
                "content": post.content,
                "is_private": post.is_private,
            }
            for post in posts
        ],
    }
    payload = {"data": data, "signature": sign_backup(data)}
    return JSONResponse(
        payload,
        headers={"Content-Disposition": "attachment; filename=posts-backup-signed.json"},
    )


@router.post("/posts/import")
def import_posts(
    request: Request,
    backup_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    if backup_file.content_type not in {"application/json", "text/json"}:
        raise HTTPException(status_code=400, detail="JSON 백업 파일만 허용됩니다.")
    raw_backup = backup_file.file.read(MAX_BACKUP_SIZE + 1)
    if len(raw_backup) > MAX_BACKUP_SIZE:
        raise HTTPException(status_code=413, detail="백업 파일은 1MB 이하여야 합니다.")
    try:
        payload = json.loads(raw_backup)
        data = payload["data"]
        signature = payload["signature"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="올바른 백업 파일이 아닙니다.")

    if not hmac.compare_digest(sign_backup(data), signature):
        record_security_event(db, request, "backup_tampering", "Invalid backup signature", user.id)
        raise HTTPException(status_code=400, detail="백업 파일의 무결성을 확인할 수 없습니다.")

    for item in data.get("posts", []):
        db.add(
            Post(
                user_id=user.id,
                title=str(item["title"])[:200],
                content=str(item["content"])[:10000],
                is_private=bool(item.get("is_private", False)),
            )
        )
    db.commit()
    return RedirectResponse(url="/posts/mine", status_code=303)
