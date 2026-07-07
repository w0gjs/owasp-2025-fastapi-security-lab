from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
router = APIRouter()


def generic_error(request: Request):
    return templates.TemplateResponse(
        request,
        "error_debug.html",
        {
            "user": None,
            "error_type": "RequestError",
            "error_message": "요청을 처리할 수 없습니다.",
            "internal_hint": "",
        },
        status_code=404,
    )


@router.get("/debug")
@router.get("/debug/error")
@router.get("/debug/db-error")
@router.get("/debug/path-error")
def debug_disabled(request: Request):
    return generic_error(request)
