from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Prospex"
    ENV: str = "development"
    SECRET_KEY: str = "change-me-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DATABASE_URL: str = "sqlite:///./leads.db"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = ""
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-5"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    HUNTER_API_KEY: str = ""
    CLEARBIT_API_KEY: str = ""
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://prospex-rho.vercel.app",
    ]
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"
    # If the configured database is unreachable, keep the API alive on a local
    # SQLite file instead of crash-looping. Set to false to fail fast instead.
    ALLOW_SQLITE_FALLBACK: bool = True
    SQLITE_FALLBACK_URL: str = "sqlite:///./leads_fallback.db"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()