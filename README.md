#Двухсервисная система LLM-консультаций

## Структура

```text
.
├── auth_service/   # аутентификация, регистрация, выпуск JWT
├── web_service/    # веб-интерфейс, проверка JWT, запросы к OpenRouter
├── photos/         # скриншоты сценариев работы
└── docker-compose.yml
```

## Принцип разделения

`auth_service` отвечает за пользователей, учётные данные и выпуск токенов (JWT).

`web_service` не знает пароли и регистрацию. Он принимает JWT, проверяет подпись и срок действия, после чего предоставляет функциональность LLM-консультаций. Доступ к LLM защищён JWT-аутентификацией, токен выпускается только в Auth Service.

## Технологии

- **FastAPI + uvicorn** — оба сервиса.
- **Jinja2** — серверный HTML-интерфейс Web Service.
- **Celery + RabbitMQ** — асинхронная очередь задач LLM.
- **Redis** — хранение JWT, привязанного к клиентской сессии, и backend результатов Celery.
- **OpenRouter** — внешний LLM API (отдельный клиент, вызывается только в Celery-задаче).

## Локальный запуск

1. Заполните `.env` для каждого сервиса на основе `.env.example`.
2. Поднимите инфраструктуру:
   - `redis` на `127.0.0.1:6379`
   - `rabbitmq` на `127.0.0.1:5672` (UI: `127.0.0.1:15672`)
3. Запустите сервисы:
   - Auth API:
     - `cd auth_service`
     - `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
   - Web Service (Jinja-интерфейс):
     - `cd web_service`
     - `uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload`
   - Celery Worker:
     - `cd web_service`
     - `uv run celery -A app.infra.celery_app.celery_app worker --loglevel=info --pool=solo`
4. Откройте:
   - Swagger Auth Service: `http://127.0.0.1:8000/docs`
   - Web Service: `http://127.0.0.1:8001`
   - RabbitMQ UI: `http://127.0.0.1:15672` (`guest` / `guest`)

## Пользовательский сценарий

1. Регистрация в Auth Service (`POST /auth/register`, email в формате `surname@email.com`, например `kunin@email.com`).
2. Логин (`POST /auth/login`) — получение JWT.
3. Открыть Web Service, вставить JWT в форму сохранения токена.
4. Отправить prompt через HTML-форму.
5. Web Service валидирует JWT и ставит задачу в очередь Celery (RabbitMQ).
6. Celery worker обращается к OpenRouter, результат сохраняется в Redis.
7. Ответ модели отображается на странице.

## Тесты

- Auth Service:
  - `cd auth_service && uv run pytest -q`
- Web Service:
  - `cd web_service && uv run pytest -q`

Тесты не требуют Docker и внешних сервисов (in-memory SQLite, `fakeredis`, подмена `llm_request.delay`).

## Docker Compose

```powershell
docker compose up --build
```

Контейнеры: `auth_service`, `web_service`, `celery_worker`, `redis`, `rabbitmq`.

## Скриншоты в папке photos
