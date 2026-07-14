from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		case_sensitive=False,
		extra="ignore",
	)

	app_name: str = "File Mediation and Transformation Platform"
	app_version: str = "0.1.0"
	environment: str = "development"
	debug: bool = False

	api_v1_prefix: str = "/api/v1"

	cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
	cors_allow_credentials: bool = True
	cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
	cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])

	database_url: str

	secret_key: str
	algorithm: str = "HS256"
	access_token_expire_minutes: int = 60
	refresh_token_expire_days: int = 7

	log_level: str = "INFO"
	log_path: str = "logs/application.log"


@lru_cache
def get_settings() -> Settings:
	return Settings()