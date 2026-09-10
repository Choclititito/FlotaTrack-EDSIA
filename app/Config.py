from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la app, siempre por variables de entorno (nunca hardcodeada)."""

    database_url: str = "postgresql://fleettrack:fleettrack@localhost:5432/fleettrack"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
settings = Settings()
