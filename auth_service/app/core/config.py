from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Auth Service"
    env: str = "local"
    jwt_secret: str = "change-me-in-production"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60
    sqlite_path: str = "./auth.sqlite3"
    database_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def async_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.sqlite_path}"


settings = Settings()
