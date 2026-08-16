from app.infra.celery_app import celery_app
from app.services.openrouter_client import call_openrouter


@celery_app.task(name="llm_request")
def llm_request(
    prompt: str,
    system: str = "You are a concise LLM consultation assistant.",
    temperature: float = 0.7,
) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    return call_openrouter(messages, temperature=temperature)
