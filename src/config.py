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

# A deployment platform's dashboard can define an env var with an empty
# value (present but blank), which pydantic-settings treats as "provided"
# rather than "unset" - it does NOT fall back to the field default the way
# a missing env var would. Since this site has no real use for either
# setting being blank, treat blank the same as unset.
if not settings.SITE_NAME:
    settings.SITE_NAME = "imenopis.rs"
if not settings.DATABASE_URL or "://" not in settings.DATABASE_URL:
    settings.DATABASE_URL = f"sqlite:///{BASE_DIR / 'imena.db'}"
