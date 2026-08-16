from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "web_service",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

celery_app.autodiscover_tasks(["app.tasks"])

# Ensure llm_request is registered when the worker starts.
import app.tasks.llm_tasks  # noqa: E402,F401
