from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root, not the process cwd - a relative sqlite URL would otherwise
# resolve differently depending on where the process is launched from (e.g.
# a Vercel serverless function's cwd is not guaranteed to be the repo root).
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    SITE_NAME: str = "imenopis.rs"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'imena.db'}"


settings = Settings()
