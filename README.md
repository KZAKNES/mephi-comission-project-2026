# Двухсервисная система LLM-консультаций

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

## Тесты

- Auth service:
  - `cd ..\auth_service`
  - `uv run pytest -v`
- Web service:
  - `cd ..\web_service`
  - `uv run pytest -v`
## Пользовательский сценарий

1. Регистрация в Auth Service (`POST /auth/register`, email в формате `surname@email.com`, например `kunin@email.com`).
2. Логин (`POST /auth/login`) — получение JWT.
3. Открыть Web Service, вставить JWT в форму сохранения токена.
4. Отправить prompt через HTML-форму.
5. Web Service валидирует JWT и ставит задачу в очередь Celery (RabbitMQ).
6. Celery worker обращается к OpenRouter, результат сохраняется в Redis.
7. Ответ модели отображается на странице.

## Скриншоты в папке photos
