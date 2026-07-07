import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.core.database import get_db
from app.models.post import Post

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter()


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
    payload = {
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
    # A08 실습: 백업 파일에 서명이나 무결성 검증값을 포함하지 않는다.
    return JSONResponse(payload, headers={"Content-Disposition": "attachment; filename=posts-backup.json"})


@router.post("/posts/import")
def import_posts(
    request: Request,
    backup_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    payload = json.load(backup_file.file)
    for item in payload.get("posts", []):
        # A08 Software or Data Integrity Failures 실습:
        # 서명/체크섬과 소유자 필드를 검증하지 않고 외부 JSON을 신뢰한다.
        db.add(
            Post(
                user_id=item.get("user_id", user.id),
                title=item["title"],
                content=item["content"],
                is_private=bool(item.get("is_private", False)),
            )
        )
    db.commit()
    return RedirectResponse(url="/posts/mine", status_code=303)
