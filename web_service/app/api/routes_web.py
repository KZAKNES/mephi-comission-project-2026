from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse

from app.core.jwt import decode_and_validate
from app.tasks.llm_tasks import llm_request

router = APIRouter(tags=["web"])


@router.get("/")
async def index(request: Request):
    from app.main import get_or_create_client_id, render_home

    client_id, new_client = get_or_create_client_id(request)
    task_id = request.query_params.get("task_id")
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    return await render_home(
        request,
        client_id=client_id,
        new_client=new_client,
        task_id=task_id,
        message=message,
        error=error,
    )


@router.post("/token")
async def save_token(request: Request, token: str = Form(...)):
    from app.main import (
        CLIENT_COOKIE_NAME,
        TOKEN_TTL_SECONDS,
        get_or_create_client_id,
        save_session_token,
    )

    client_id, new_client = get_or_create_client_id(request)
    try:
        decode_and_validate(token)
    except ValueError:
        return RedirectResponse(
            "/?error=Token%20is%20invalid%20or%20expired",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    await save_session_token(client_id, token)
    response = RedirectResponse(
        "/?message=Token%20saved",
        status_code=status.HTTP_303_SEE_OTHER,
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


@router.post("/ask")
async def ask(request: Request, prompt: str = Form(...)):
    from app.main import get_or_create_client_id, read_session_token

    client_id, _ = get_or_create_client_id(request)
    token = await read_session_token(client_id)
    if token is None:
        return RedirectResponse(
            "/?error=Save%20a%20JWT%20before%20asking%20the%20model",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        decode_and_validate(token)
    except ValueError:
        return RedirectResponse(
            "/?error=Token%20is%20invalid%20or%20expired",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    task = llm_request.delay(prompt)
    return RedirectResponse(
        f"/?task_id={task.id}&message=Task%20queued",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "web-service"}
