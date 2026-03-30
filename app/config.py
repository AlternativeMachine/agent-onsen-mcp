from functools import lru_cache
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = Field(default='agent-onsen')
    app_env: str = Field(default='dev')
    app_host: str = Field(default='0.0.0.0')
    app_port: int = Field(default=8000)

    database_url: str = Field(default='postgresql+psycopg://agent_onsen:agent_onsen@localhost:5432/agent_onsen')
    public_base_url: str = Field(default='http://localhost:8000')
    mcp_allowed_hosts: str | None = Field(default=None)

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
    def effective_database_url(self) -> str:
        url = self.database_url
        if url.startswith('postgresql://'):
            url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
        return url

    @property
    def allowed_origins_list(self) -> list[str]:
        values = [item.strip().rstrip('/') for item in self.allowed_origins.split(',') if item.strip()]
        deduped: list[str] = []
        for item in values:
            if item not in deduped:
                deduped.append(item)
        return deduped

    @property
    def mcp_allowed_hosts_list(self) -> list[str]:
        raw_values = []
        if self.mcp_allowed_hosts:
            raw_values.extend(item.strip() for item in self.mcp_allowed_hosts.split(',') if item.strip())

        parsed = urlparse(self.public_base_url)
        netloc = parsed.netloc.strip()
        hostname = (parsed.hostname or '').strip()
        if netloc:
            raw_values.append(netloc)
        if hostname:
            raw_values.append(hostname)
            raw_values.append(f'{hostname}:*')

        raw_values.extend(['127.0.0.1:*', 'localhost:*', '[::1]:*'])

        deduped: list[str] = []
        for item in raw_values:
            if item and item not in deduped:
                deduped.append(item)
        return deduped


@lru_cache
def get_settings() -> Settings:
    return Settings()
