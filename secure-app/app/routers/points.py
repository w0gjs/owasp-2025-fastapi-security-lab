from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.common.auth import get_current_user
from app.common.audit import record_security_event
from app.core.database import get_db
from app.models.transfer import PointTransfer
from app.models.user import User

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter()


@router.get("/points")
def points_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    transfers = db.execute(
        select(PointTransfer).where(
            or_(PointTransfer.sender_id == user.id, PointTransfer.recipient_id == user.id)
        ).order_by(PointTransfer.id.desc())
    ).scalars().all()
    users = db.scalars(select(User).order_by(User.username)).all()
    return templates.TemplateResponse(
        request,
        "points.html",
        {"user": user, "users": users, "transfers": transfers, "error": None},
    )


@router.post("/points/transfer")
def transfer_points(
    request: Request,
    recipient_username: str = Form(...),
    amount: int = Form(...),
    db: Session = Depends(get_db),
):
    sender = get_current_user(request, db)
    if sender is None:
        return RedirectResponse(url="/login", status_code=303)

    sender = db.scalar(select(User).where(User.id == sender.id).with_for_update())
    recipient = db.scalar(
        select(User).where(User.username == recipient_username).with_for_update()
    )
    if recipient is None:
        return templates.TemplateResponse(
            request,
            "points.html",
            {"user": sender, "users": [], "transfers": [], "error": "받는 사용자를 찾을 수 없습니다."},
            status_code=400,
        )

    if recipient.id == sender.id or amount <= 0 or amount > sender.points:
        record_security_event(
            db,
            request,
            "invalid_point_transfer",
            f"Rejected transfer recipient={recipient.id} amount={amount}",
            sender.id,
        )
        return templates.TemplateResponse(
            request,
            "points.html",
            {
                "user": sender,
                "users": [],
                "transfers": [],
                "error": "송금 금액과 잔액을 확인해주세요.",
            },
            status_code=400,
        )

    sender.points -= amount
    recipient.points += amount
    db.add(PointTransfer(sender_id=sender.id, recipient_id=recipient.id, amount=amount))
    db.commit()
    return RedirectResponse(url="/points", status_code=303)
