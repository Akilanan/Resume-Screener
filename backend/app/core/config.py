from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@postgres:5432/talentai"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ENCRYPTION_KEY: str = "your-fernet-key-base64-32-bytes=="
    REDIS_HOST: str = "redis"
    RABBITMQ_HOST: str = "rabbitmq"
    LLM_PROVIDER: str = "openai"  # "openai" | "gemini"
    LLM_API_KEY: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "noreply@talentai.com"

    class Config:
        env_file = ".env"


settings = Settings()
