from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    
    # Шлюз Polza.ai
    POLZA_API_KEY: str = ""
    POLZA_BASE_URL: str = "https://api.polza.ai/v1"
    AI_MODEL: str = "openai/gpt-4o-mini"

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Baserow
    BASEROW_URL: str = "https://crm.pisarev-n8n.ru"
    BASEROW_TOKEN: str = ""
    BASEROW_TABLE_ID: int = 278

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()