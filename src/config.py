from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    SITE_NAME: str = "imena-rs"
    DATABASE_URL: str = "sqlite:///./imena.db"


settings = Settings()
