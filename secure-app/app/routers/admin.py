from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.audit import record_security_event
from app.core.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.models.security_event import SecurityEvent

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()


@router.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return templates.TemplateResponse(request, "login.html", {"error": None, "user": None})

    if user.role != "admin":
        record_security_event(db, request, "authorization_failure", "Non-admin accessed /admin", user.id)
        return templates.TemplateResponse(
            request,
            "error_debug.html",
            {
                "user": user,
                "error_type": "AccessDenied",
                "error_message": "접근 권한이 없습니다.",
                "internal_hint": "",
            },
            status_code=403,
        )
    users = db.scalars(select(User).order_by(User.id)).all()
    posts = db.execute(
        select(Post.id, Post.title, User.nickname.label("author"))
        .join(User, Post.user_id == User.id)
        .order_by(Post.id)
    ).all()
    comments = db.execute(
        select(Comment.id, Comment.post_id, User.nickname.label("author"), Comment.content)
        .join(User, Comment.user_id == User.id)
        .order_by(Comment.id)
    ).all()

    return templates.TemplateResponse(
        request,
        "admin.html",
        {"user": user, "users": users, "posts": posts, "comments": comments},
    )


@router.get("/admin/security-events")
def security_events_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return templates.TemplateResponse(request, "login.html", {"error": None, "user": None})

    if user.role != "admin":
        record_security_event(
            db, request, "authorization_failure", "Non-admin accessed security events", user.id
        )
        return RedirectResponse(url="/posts", status_code=303)
    security_events = db.scalars(
        select(SecurityEvent).order_by(SecurityEvent.id.desc()).limit(100)
    ).all()
    return templates.TemplateResponse(
        request,
        "security_events.html",
        {"user": user, "security_events": security_events},
    )
