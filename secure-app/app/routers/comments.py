from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.audit import record_security_event
from app.core.database import get_db
from app.models.comment import Comment
from app.models.post import Post

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter()


@router.post("/posts/{post_id}/comments")
def create_comment(
    request: Request,
    post_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    post = db.get(Post, post_id)
    if post is None or post.is_private:
        raise HTTPException(status_code=404, detail="Post not found")
    if "<script" in content.lower():
        record_security_event(db, request, "xss_payload", "Script markup in comment", user.id)
    db.add(Comment(post_id=post_id, user_id=user.id, content=content[:2000]))
    db.commit()
    return RedirectResponse(url=f"/posts/{post_id}", status_code=303)
