from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SITE_NAME: str = "imena-rs"
    DATABASE_URL: str = "sqlite:///./imena.db"

    class Config:
        env_file = ".env"


settings = Settings()
