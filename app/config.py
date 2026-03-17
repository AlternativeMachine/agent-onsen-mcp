from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='agent-onsen')
    app_env: str = Field(default='dev')
    app_host: str = Field(default='0.0.0.0')
    app_port: int = Field(default=8000)
    mcp_host: str = Field(default='0.0.0.0')
    mcp_port: int = Field(default=8001)

    database_url: str = Field(default='postgresql+psycopg://agent_onsen:agent_onsen@localhost:5432/agent_onsen')
    public_base_url: str = Field(default='http://localhost:8000')
    mcp_public_url: str = Field(default='http://localhost:8001/mcp')

    default_session_ttl_minutes: int = Field(default=60)
    api_key: str | None = Field(default=None)
    allowed_origins: str = Field(
        default='http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001,https://chat.openai.com,https://chatgpt.com,https://claude.ai'
    )

    llm_backend: str = Field(default='none')
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default='gpt-5-mini')

    default_locale: str = Field(default='en')

    @property
    def allowed_origins_list(self) -> list[str]:
        values = [item.strip().rstrip('/') for item in self.allowed_origins.split(',') if item.strip()]
        deduped: list[str] = []
        for item in values:
            if item not in deduped:
                deduped.append(item)
        return deduped


@lru_cache
def get_settings() -> Settings:
    return Settings()
