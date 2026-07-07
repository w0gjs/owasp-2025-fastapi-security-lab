from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import get_settings
from app.common.security_headers import build_security_headers
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.comments import router as comments_router
from app.routers.errors import router as errors_router
from app.routers.posts import router as posts_router
from app.routers.points import router as points_router
from app.routers.backup import router as backup_router
from app.routers.upload import router as upload_router

BASE_DIR = Path(__file__).resolve().parent.parent

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    debug=settings.debug,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="strict",
    max_age=1800,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

app.include_router(auth_router)
app.include_router(backup_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(admin_router)
app.include_router(errors_router)
app.include_router(upload_router)
app.include_router(points_router)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    for name, value in build_security_headers().items():
        response.headers[name] = value
    return response
