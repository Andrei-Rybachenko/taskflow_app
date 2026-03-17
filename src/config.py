from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    SECRET: str

    @property
    def DB_URL(self):
        return (f"postgresql+asyncpg://{self.DB_USER}:"
                                        f"{self.DB_PASS}"
                                        f"@{self.DB_HOST}"
                                        f":{self.DB_PORT}"
                                        f"/{self.DB_NAME}")

    class Config:
        env_file = BASE_DIR / ".env"


settings = Settings()
