import respx
from httpx import Response

from app.services.openrouter_client import call_openrouter


@respx.mock
def test_call_openrouter_returns_answer() -> None:
    route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "Test answer"}},
                ],
            },
        )
    )

    answer = call_openrouter([{"role": "user", "content": "Hello"}])

    assert answer == "Test answer"
    assert route.called
