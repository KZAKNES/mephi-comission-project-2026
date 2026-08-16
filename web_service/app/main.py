from uuid import uuid4

from celery.result import AsyncResult
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.routes_web import router as web_router
from app.core.config import settings
from app.infra.celery_app import celery_app
from app.infra.redis import get_redis

CLIENT_COOKIE_NAME = "web_client_id"
TOKEN_TTL_SECONDS = 60 * 60 * 24

templates = Jinja2Templates(directory="app/templates")

app = FastAPI(
    title="Web Service",
    description="Jinja web interface for JWT-protected LLM consultations.",
    version="0.1.0",
)

app.include_router(web_router)


def get_or_create_client_id(request: Request) -> tuple[str, bool]:
    client_id = request.cookies.get(CLIENT_COOKIE_NAME)
    if client_id:
        return client_id, False
    return str(uuid4()), True


async def read_session_token(client_id: str) -> str | None:
    redis = get_redis()
    token = await redis.get(_token_key(client_id))
    return token if token else None


async def save_session_token(client_id: str, token: str) -> None:
    redis = get_redis()
    await redis.set(_token_key(client_id), token, ex=TOKEN_TTL_SECONDS)


def get_task_state(task_id: str | None) -> dict[str, str | None]:
    if not task_id:
        return {"task_id": None, "task_status": None, "task_result": None}

    task = AsyncResult(task_id, app=celery_app)
    result = task.result if task.ready() else None
    return {
        "task_id": task_id,
        "task_status": task.status,
        "task_result": str(result) if result is not None else None,
    }


async def render_home(
    request: Request,
    *,
    client_id: str,
    new_client: bool = False,
    task_id: str | None = None,
    message: str | None = None,
    error: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    token = await read_session_token(client_id)
    context = {
        "request": request,
        "has_token": token is not None,
        "message": message,
        "error": error,
        **get_task_state(task_id),
    }
    response = templates.TemplateResponse(
        "index.html",
        context,
        status_code=status_code,
    )
    if new_client:
        response.set_cookie(
            CLIENT_COOKIE_NAME,
            client_id,
            httponly=True,
            samesite="lax",
            max_age=TOKEN_TTL_SECONDS,
        )
    return response


def _token_key(client_id: str) -> str:
    return f"session:{client_id}:jwt"
