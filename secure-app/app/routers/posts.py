from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.audit import record_security_event
from app.core.database import get_db
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()


@router.get("/posts")
def posts_list(
    request: Request,
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    if keyword and any(marker in keyword.lower() for marker in ("<script", "' or", "--")):
        record_security_event(
            db,
            request,
            "suspicious_search",
            "Potential injection payload in search",
            current_user.id if current_user else None,
        )
    statement = (
        select(
            Post.id,
            Post.title,
            Post.content,
            Post.is_private,
            Post.created_at,
            User.nickname.label("author"),
        )
        .join(User, Post.user_id == User.id)
        .where(Post.is_private.is_(False))
    )
    if keyword:
        escaped = keyword.replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        statement = statement.where(
            or_(Post.title.ilike(pattern, escape="\\"), Post.content.ilike(pattern, escape="\\"))
        )
    posts = db.execute(statement.order_by(Post.id.desc())).all()

    return templates.TemplateResponse(
        request,
        "posts.html",
        {"posts": posts, "user": current_user, "keyword": keyword or ""},
    )


@router.get("/posts/new")
def new_post_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "post_new.html", {"user": user})


@router.post("/posts/new")
def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    is_private: bool = Form(False),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Login required")

    if "<script" in content.lower() or "<script" in title.lower():
        record_security_event(db, request, "xss_payload", "Script markup in post", user.id)
    post = Post(user_id=user.id, title=title[:200], content=content[:10000], is_private=is_private)
    db.add(post)
    db.commit()
    target = "/posts/mine" if is_private else f"/posts/{post.id}"
    return RedirectResponse(url=target, status_code=303)


@router.get("/posts/mine")
def my_posts(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    posts = db.execute(
        select(Post.id, Post.title, Post.is_private, Post.created_at)
        .where(Post.user_id == user.id)
        .order_by(Post.id.desc())
    ).all()
    return templates.TemplateResponse(
        request,
        "my_posts.html",
        {"user": user, "posts": posts},
    )


@router.get("/posts/{post_id}")
def post_detail(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.execute(
        select(
            Post.id, Post.title, Post.content, Post.created_at, User.nickname.label("author")
        )
        .join(User, Post.user_id == User.id)
        .where(Post.id == post_id, Post.is_private.is_(False))
    ).first()
    comments = db.execute(
        select(Comment.id, Comment.content, User.nickname.label("author"))
        .join(User, Comment.user_id == User.id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.id.desc())
    ).all()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse(
        request,
        "post_detail.html",
        {"post": post, "comments": comments, "user": get_current_user(request, db)},
    )


@router.get("/posts/private/{post_id}")
def private_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)

    post = db.execute(
        select(
            Post.id, Post.title, Post.content, Post.created_at, User.nickname.label("author")
        )
        .join(User, Post.user_id == User.id)
        .where(
            Post.id == post_id,
            Post.user_id == current_user.id,
            Post.is_private.is_(True),
        )
    ).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse(
        request,
        "private_post.html",
        {"post": post, "user": current_user},
    )


@router.post("/posts/{post_id}/delete")
def delete_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    current_user = get_current_user(request, db)
    if current_user is None:
        return RedirectResponse(url="/login", status_code=303)

    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id and current_user.role != "admin":
        record_security_event(
            db,
            request,
            "authorization_failure",
            f"Unauthorized delete attempt for post={post_id}",
            current_user.id,
        )
        raise HTTPException(status_code=403, detail="Not allowed")

    db.execute(delete(Comment).where(Comment.post_id == post_id))
    db.execute(delete(Post).where(Post.id == post_id))
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)
