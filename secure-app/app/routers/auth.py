from pathlib import Path
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.audit import record_security_event
from app.common.passwords import hash_password, verify_password
from app.models.user import User

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()


@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"user": None})


@router.post("/register")
def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    nickname: str = Form(...),
    db: Session = Depends(get_db),
):
    if (
        len(password) < 10
        or not any(char.isupper() for char in password)
        or not any(char.islower() for char in password)
        or not any(char.isdigit() for char in password)
    ):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 10 characters and include upper, lower, and digit.",
        )
    try:
        db.add(
            User(
                username=username,
                password=hash_password(password),
                nickname=nickname,
                role="user",
            )
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already exists")

    return RedirectResponse(url="/login", status_code=303)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None, "user": None})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.username == username))
    now = datetime.utcnow()

    if user is not None and user.locked_until and user.locked_until > now:
        record_security_event(db, request, "login_blocked", "Locked account login attempt", user.id)
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "로그인할 수 없습니다. 잠시 후 다시 시도해주세요.", "user": None},
            status_code=429,
        )

    if user is None or not verify_password(password, user.password):
        if user is not None:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
            db.commit()
        record_security_event(
            db,
            request,
            "login_failure",
            f"Failed login for username={username[:50]}",
            user.id if user else None,
        )
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "아이디 또는 비밀번호를 확인해주세요.", "user": None},
            status_code=401,
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    return RedirectResponse(url="/posts", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
