from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='agent-onsen')
    app_env: str = Field(default='dev')
    app_host: str = Field(default='0.0.0.0')
    app_port: int = Field(default=8000)

    database_url: str = Field(default='postgresql+psycopg://agent_onsen:agent_onsen@localhost:5432/agent_onsen')

    default_session_ttl_minutes: int = Field(default=60)
    api_key: str | None = Field(default=None)
    allowed_origins: str = Field(
        default='https://chat.openai.com,https://chatgpt.com,https://claude.ai'
    )

    default_locale: str = Field(default='en')

    @property
    def effective_database_url(self) -> str:
        url = self.database_url
        if url.startswith('postgresql://'):
            url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
        return url

    @property
    def allowed_origins_list(self) -> list[str]:
        values = [item.strip().rstrip('/') for item in self.allowed_origins.split(',') if item.strip()]
        for origin in ('http://localhost:8000', 'http://127.0.0.1:8000'):
            if origin not in values:
                values.append(origin)
        deduped: list[str] = []
        for item in values:
            if item not in deduped:
                deduped.append(item)
        return deduped


@lru_cache
def get_settings() -> Settings:
    return Settings()
