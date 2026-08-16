import httpx

from app.core.config import settings

Message = dict[str, str]


class OpenRouterError(Exception):
    pass


class OpenRouterClient:
    def __init__(
        self,
        api_key: str = settings.openrouter_api_key,
        base_url: str = settings.openrouter_base_url,
        model: str = settings.openrouter_model,
        site_url: str = settings.openrouter_site_url,
        app_name: str = settings.openrouter_app_name,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.site_url = site_url
        self.app_name = app_name

    def ask(self, messages: list[Message], temperature: float = 0.7) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
        except httpx.RequestError as exc:
            raise OpenRouterError(f"OpenRouter network error: {exc}") from exc

        if response.status_code >= 400:
            raise OpenRouterError(
                f"OpenRouter returned {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise OpenRouterError("OpenRouter returned an unexpected response") from exc


def call_openrouter(messages: list[Message], temperature: float = 0.7) -> str:
    return OpenRouterClient().ask(messages, temperature=temperature)
